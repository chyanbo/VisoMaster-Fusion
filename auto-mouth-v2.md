# Auto-Mouth Expression V2 — Implementation Plan

## Analysis of Current Implementation

### Bugs found

#### Bug 1 — Wrong normalize toggle key (no normalization in practice)
`_apply_auto_mouth` sets:
```python
_p["FaceExpressionNormalizeLipsEnableToggle"] = _normalize
```
But `FaceExpressionNormalizeLipsEnableToggle` is the **Simple-mode** normalize toggle (see
`frame_edits.py:325`, only read inside `if mode == "Simple"`). Auto-mouth always sets
`FaceExpressionModeSelection = "Advanced"`, so this value is **never read** by the restorer.

The correct Advanced-mode normalize toggle is `FaceExpressionNormalizeLipsBothEnableToggle`.
Result: normalisation has been silently inactive since shipping.

#### Bug 2 — Lip retargeting not enabled (root cause of quality gap)
The "restore lips" feature works well because Simple mode's normalization path (line 332-340
in `frame_edits.py`) calls `lp_retarget_lip(x_s, calc_combined_lip_ratio(...))`. This
directly shapes the lips of the swapped face to match the measured ratio of the driving face.

Auto-mouth skips this entirely. In Advanced mode the retargeting toggle is
`FaceExpressionRetargetingLipsBothEnableToggle`, which is `False` by default and auto-mouth
never sets it. The restorer therefore only transfers raw expression deltas without any
explicit lip-shape correction.

#### Bug 3 — FaceParser interaction is unsafe
`_apply_auto_mouth` unconditionally forces:
```python
_p["FaceParserEnableToggle"] = True
_p["LowerLipParserSlider"] = 1
```
If the user has `FaceParserEnableToggle=False` or has custom FaceParser values, these are
overwritten silently in the synthesized copy. More critically, if `FaceParserEnableToggle`
was already `True` with non-1 lower-lip values, those user values are also stomped.

---

### Triggering issues

#### Issue 1 — Default threshold 0.20 misses moderate-open mouths
Measured lip-open ratio ranges:
- Closed / relaxed: 0.01–0.06
- Light speech: 0.07–0.12
- Normal "open mouth" (moderate eating, laughing): 0.12–0.20
- Wide open (yawn, big laugh): 0.25+

A threshold of 0.20 only catches genuinely wide-open mouths, missing the moderate range.
A default of **0.12** would cover normal eating/conversation scenarios while still filtering
resting/closed faces.

#### Issue 2 — EMA cold-start delay (~0.1 s latency)
With α=0.40 and threshold=0.20 (or even new 0.12), when a 0.30 ratio first appears:
- Frame 1: ema = 0.12  → still inactive
- Frame 2: ema = 0.19  → still inactive (just under threshold)
- Frame 3: ema = 0.24  → activates

Three frames ≈ 100 ms at 30 fps. Visible as a delayed "pop-on" effect.

Fix: if the raw ratio exceeds the threshold, activate **immediately** (skip EMA on first
trigger). EMA then smooths the strength after activation.

#### Issue 3 — No hysteresis → oscillation at boundary
When ratio hovers near the threshold (e.g., 0.18–0.22), EMA crosses the threshold
repeatedly each frame causing the restorer to switch on/off/on/off visibly.

Fix: add a separate deactivation threshold = activation threshold × 0.75. Once active,
deactivation only occurs when EMA falls below this lower value.

#### Issue 4 — Occlusion "stuck active" risk
Rule 2 (stay active when ratio=None) is correct in principle but has no upper bound. If a
face is occluded or lost after activation, auto-mouth will remain active indefinitely with
no mechanism to recover.

Fix: add an occlusion-frame counter (`none_streak`). After N consecutive None-ratio frames
while active, the EMA slowly decays and eventually falls below the deactivate threshold.

#### Issue 5 — Binary on/off produces abrupt transitions
The feature pops from 0 to full strength when the EMA crosses the threshold. A proportional
approach (scale strength with how far above threshold the EMA is) produces smoother results.

---

### Quality issues

#### Issue 6 — Advanced mode without retargeting is inferior to Simple mode
The "restore lips" path that users report as "much better" corresponds to Simple mode with
`FaceExpressionNormalizeLipsEnableToggle=True`. This calls:
1. `calc_combined_lip_ratio(c_d_lip_lst, source_lmk)` — combines driving ratio with
   the swapped face's own lip geometry.
2. `lp_retarget_lip(x_s, combined_lip_ratio)` — generates a delta that drives the swapped
   face's lip keypoints to precisely match the measured ratio.

This retargeting is model-aware and geometry-correct, producing far better shapes than the
raw expression-delta transfer used by Advanced mode without retargeting.

**Recommended fix**: switch auto-mouth to **Simple mode** with
`FaceExpressionAnimationRegionSelection="lips"` and `FaceExpressionNormalizeLipsEnableToggle=True`.
This makes auto-mouth use exactly the same high-quality path as the manual "restore lips" toggle,
with the normalization/retargeting built in.

The jaw coherence (currently added via `FaceExpressionGeneralJawToggle`) can be retained by
changing `FaceExpressionAnimationRegionSelection` to `"all"` instead of just `"lips"`, since
Simple mode handles eyes+lips together at the same strength. Alternatively, if jaw-only
without eyes is needed, keep Advanced mode but fix both bugs above and add retargeting.

**Recommended approach: Simple mode**
- Cleaner, fewer synthesized keys
- `lp_retarget_lip` is used automatically
- Normalization works correctly
- Proven to match user's "restore lips" quality expectation

**Alternative: Fixed Advanced mode** (if per-component control is important)
- Fix Bug 1: change `FaceExpressionNormalizeLipsEnableToggle` → `FaceExpressionNormalizeLipsBothEnableToggle`
- Fix Bug 2: add `FaceExpressionRetargetingLipsBothEnableToggle=True`
- Add `FaceExpressionRetargetingLipsMultiplierBothDecimalSlider=1.0`

---

## Implementation Plan

### Change 1 — `MouthOpennessState` improvements (`app/processors/mouth_openness.py`)

Replace `MouthOpennessState` with an expanded version supporting hysteresis, occlusion
timeout, proportional strength and immediate activation:

```python
@dataclass
class MouthOpennessState:
    active: bool = False
    ema: float = 0.0
    none_streak: int = 0        # consecutive frames with ratio=None while active

    # Configurable occlusion timeout (frames). At 30 fps, 45 ≈ 1.5 s.
    OCCLUSION_TIMEOUT: int = 45

    def update(
        self,
        ratio: float | None,
        alpha: float,
        threshold: float,
    ) -> tuple[bool, float]:
        """
        Returns (active, effective_ratio) where effective_ratio is the smoothed
        EMA value for proportional strength calculation.

        Rules:
          1. ratio is None → rule 2 (stay); increment none_streak; decay EMA slowly
             after OCCLUSION_TIMEOUT frames to prevent stuck-active
          2. ratio >= threshold AND not yet active → activate immediately (no cold-start)
          3. ratio available → update EMA; apply hysteresis thresholds
        """
        deactivate_threshold = threshold * 0.75  # hysteresis band

        if ratio is None:
            # Rule 2: stay in current state
            if self.active:
                self.none_streak += 1
                if self.none_streak > self.OCCLUSION_TIMEOUT:
                    # Slow decay to eventually fall below deactivate threshold
                    self.ema *= 0.92
                    if self.ema < deactivate_threshold:
                        self.active = False
                        self.none_streak = 0
            return self.active, self.ema

        # Ratio is valid — reset occlusion counter
        self.none_streak = 0

        # Immediate first-frame activation (skip cold-start delay)
        if not self.active and ratio >= threshold:
            self.ema = ratio  # skip ramp-up
            self.active = True
            return True, self.ema

        # Normal EMA update
        self.ema = alpha * ratio + (1.0 - alpha) * self.ema

        # Hysteresis: activate at threshold, deactivate at threshold * 0.75
        if not self.active and self.ema >= threshold:
            self.active = True
        elif self.active and self.ema < deactivate_threshold:
            self.active = False

        return self.active, self.ema

    def reset(self) -> None:
        self.active = False
        self.ema = 0.0
        self.none_streak = 0
```

The `update` method now returns `(active, ema)` instead of just `active`.

---

### Change 2 — `_apply_auto_mouth` rewrite (`app/processors/workers/frame_worker.py`)

Replace the synthesized-params block entirely. Switch to Simple mode to get `lp_retarget_lip`
quality, fix normalize toggle, fix FaceParser interaction, add proportional strength.

```python
def _apply_auto_mouth(
    self,
    params: dict,
    kps_all: "np.ndarray | None",
    target_fb: Any,
    control: dict,
) -> dict:
    """
    Compute auto-mouth lip-open ratio and, when active, return a modified params
    dict using Simple mode lip-transfer (same quality path as 'restore lips').

    Returns *params* unchanged (same object, zero allocation) when inactive.
    """
    if not params.get("AutoMouthExpressionEnableToggle", False):
        return params

    from app.processors.mouth_openness import (
        MouthOpennessState,
        compute_lip_open_ratio_203,
        compute_lip_open_ratio_68,
    )

    _alpha     = params.get("AutoMouthEMAAlphaDecimalSlider", 0.65)
    _threshold = params.get("AutoMouthOpenThresholdDecimalSlider", 0.12)
    _lmk_model = control.get("LandmarkDetectModelSelection", "203")

    _ratio: "float | None" = None
    if _lmk_model == "203":
        _ratio = compute_lip_open_ratio_203(kps_all)
    elif _lmk_model == "68":
        _ratio = compute_lip_open_ratio_68(kps_all)
    else:
        if not getattr(self, "_auto_mouth_warned", False):
            print(
                f"[WARN] Auto-mouth requires landmark model '203' or '68'. "
                f"Current model is '{_lmk_model}'. Feature disabled until changed."
            )
            self._auto_mouth_warned = True

    _state: "MouthOpennessState | None" = getattr(target_fb, "mouth_openness_state", None)
    if _state is None:
        target_fb.mouth_openness_state = MouthOpennessState()
        _state = target_fb.mouth_openness_state

    _auto_active, _ema_value = _state.update(_ratio, _alpha, _threshold)

    if _auto_active and not params.get("FaceExpressionEnableBothToggle", False):
        _base_strength = params.get("AutoMouthExpressionStrengthDecimalSlider", 0.80)

        # Proportional scaling: ramp from threshold up to threshold*2 → 0.0 to 1.0
        _ramp_range = max(_threshold * 0.5, 0.04)
        _proportion = min(1.0, max(0.0, (_ema_value - _threshold) / _ramp_range))
        _strength = _base_strength * _proportion

        _normalize = params.get("AutoMouthNormalizeLipsToggle", True)
        _region    = params.get("AutoMouthAnimationRegionSelection", "lips")

        _p = dict(params)
        _p["FaceExpressionEnableBothToggle"]         = True
        _p["FaceExpressionModeSelection"]            = "Simple"  # uses lp_retarget_lip
        _p["FaceExpressionBeforeTypeSelection"]      = "Beginning"
        _p["FaceExpressionAnimationRegionSelection"] = _region
        _p["FaceExpressionFriendlyFactorDecimalSlider"] = _strength
        # Simple-mode normalize toggle (correct key for Simple mode)
        _p["FaceExpressionNormalizeLipsEnableToggle"] = _normalize
        # Do NOT forcibly set FaceParserEnableToggle — respect user's settings
        return _p

    return params
```

**Key differences from current implementation:**
1. Uses **Simple mode** instead of Advanced → activates the `lp_retarget_lip` path.
2. `FaceExpressionNormalizeLipsEnableToggle` is now **correct** for Simple mode.
3. **No forced FaceParser override** — the user's existing FaceParser settings are preserved.
4. `_state.update` now returns `(active, ema)` — proportional strength used.
5. Default `_alpha=0.65` (was 0.40), `_threshold=0.12` (was 0.20).
6. New `_region` param allows user to control whether jaw/eyes move with lips.

---

### Change 3 — New `AutoMouthAnimationRegionSelection` widget

Add a selection widget under the auto-mouth section in `common_layout_data.py`:

```python
"AutoMouthAnimationRegionSelection": {
    "level": 2,
    "label": "Animation Region",
    "options": ["lips", "all"],
    "default": "lips",
    "parentToggle": "AutoMouthExpressionEnableToggle",
    "requiredToggleValue": True,
    "help": (
        "'lips' transfers only mouth/jaw motion (recommended). "
        "'all' also includes eyes, matching full expression restorer behaviour."
    ),
},
```

This replaces the explicit jaw-coherence block from v1 (which used Advanced mode sub-toggles)
with a clean Simple mode equivalent. `"lips"` → Simple mode animation_region="lips".
`"all"` → Simple mode animation_region="all" (eyes + lips).

---

### Change 4 — Update `MouthOpennessState` call sites in `_apply_auto_mouth`

The `update()` signature changes from returning `bool` to returning `tuple[bool, float]`.
All three call sites for `_apply_auto_mouth` (VR and standard) go through the same method,
so only the method itself needs updating (already done in Change 2 above).

The test file `tests/unit/processors/test_mouth_openness.py` must be updated to:
- Call `state.update(ratio, alpha, threshold)` and unpack `(active, ema)`.
- Add tests for hysteresis (activates at threshold, deactivates at threshold*0.75).
- Add tests for occlusion timeout (none_streak > OCCLUSION_TIMEOUT → EMA decays).
- Add tests for immediate first-frame activation (first valid ratio ≥ threshold → ema=ratio, immediate activation).
- Add tests for proportional strength calculation in `_apply_auto_mouth`.

---

### Change 5 — Update default slider values in `common_layout_data.py`

```python
"AutoMouthOpenThresholdDecimalSlider": {
    ...
    "default": "0.12",   # was "0.20"
    ...
},
"AutoMouthEMAAlphaDecimalSlider": {
    ...
    "default": "0.65",   # was "0.40"
    ...
},
"AutoMouthExpressionStrengthDecimalSlider": {
    ...
    "default": "1.00",   # was "0.80"; increase because proportional ramp now scales it down
    ...
},
```

Note: the "Set from frame" calibration button on `AutoMouthOpenThresholdDecimalSlider` is
already implemented and still works correctly with the new lower default.

---

### Change 6 — `compute_lip_open_ratio_203`: scale MIN_MOUTH_SPAN_PX with face size

Currently `MIN_MOUTH_SPAN_PX = 8.0` is absolute. For a face that is only 30–40 px wide in
the frame, the mouth corners may be < 8 px apart even when visible, causing the ratio to
return `None` and applying rule 2 prematurely.

Option A (simpler): lower `MIN_MOUTH_SPAN_PX` to **4.0**. This only serves as a
divide-by-zero guard, so a lower threshold is safe.

Option B: accept an optional `face_bbox_width: float | None` parameter and use
`min_span = face_bbox_width * 0.03` when provided, falling back to absolute 4.0. The call
site in `_apply_auto_mouth` would need to pass the face bounding-box width from `fface["bbox"]`.

Recommendation: start with Option A (change constant to 4.0), add Option B later if small-face
detection is still unreliable.

---

### Change 7 — Interaction when user has expression restorer enabled

Current gate:
```python
if _auto_active and not params.get("FaceExpressionEnableBothToggle", False):
```
This completely disables auto-mouth if the user has manually enabled the expression restorer.
Result: auto-mouth never fires for users who have expression restorer on.

Better behaviour: if user already has `FaceExpressionEnableBothToggle=True` AND
`FaceExpressionModeSelection="Simple"` AND `FaceExpressionAnimationRegionSelection` doesn't
include lips, then we CAN add lips. But merging is complex and risky.

**Recommended fix**: remove the gate entirely and always synthesize when active:
- If user has their own expression restorer enabled AND auto-mouth fires, the synthesized
  params override the user's per-face settings for that one call. Since auto-mouth always
  sets `FaceExpressionBeforeTypeSelection="Beginning"`, and only fires the one restorer call
  at Beginning stage, there is no double-run risk.
- The user can disable auto-mouth for faces where they have a manual restorer configured.

If complete override is undesirable, a softer rule: gate only on `FaceExpressionModeSelection`
not matching `"Simple"`, so auto-mouth still runs when user is in Advanced mode.

---

### Change 8 — `set_auto_mouth_threshold_from_frame` clamp range update

Update the clamp to reflect the new slider range minimum/default:
```python
clamped = round(max(0.05, min(0.60, ratio)), 2)
```
No change needed — 0.05 minimum is still appropriate. But add a log note if ratio is below
0.05 (face may be resting/closed when button was pressed):
```python
if ratio < 0.05:
    print("[Auto-mouth] Warning: measured ratio is very low (face may not be open). "
          "Seek to a more open-mouth frame and try again.")
```

---

## File Change Summary

| File | Change |
|---|---|
| `app/processors/mouth_openness.py` | Expand `MouthOpennessState`: add `none_streak`, hysteresis, occlusion timeout, immediate activation; change `update()` to return `(bool, float)` |
| `app/processors/workers/frame_worker.py` | Rewrite `_apply_auto_mouth`: switch to Simple mode, fix normalize key, remove FaceParser override, proportional strength, update `update()` unpack |
| `app/ui/widgets/common_layout_data.py` | Add `AutoMouthAnimationRegionSelection` widget; update slider defaults (threshold→0.12, alpha→0.65, strength→1.00) |
| `app/ui/widgets/actions/control_actions.py` | Minor: add low-ratio warning in `set_auto_mouth_threshold_from_frame` |
| `tests/unit/processors/test_mouth_openness.py` | Update unpack `(active, ema) = state.update(...)`; add hysteresis/timeout/proportional tests |

**`swap_core`, `frame_edits.py`, and `widget_components.py` require no changes.**

---

## Root Cause Summary

| Problem | Root Cause | Fix |
|---|---|---|
| No normalization in practice | Wrong toggle key (`NormalizeLipsEnableToggle` is Simple-mode only, auto-mouth was using Advanced mode) | Switch to Simple mode → correct toggle automatically |
| Quality worse than "restore lips" | No `lp_retarget_lip` call; raw delta transfer only | Simple mode uses retargeting automatically via normalize path |
| Doesn't trigger on moderate openings | Threshold 0.20 too high | Lower to 0.12 |
| Cold-start delay (~3 frames) | EMA ramps from 0 | Immediate activation on first valid ratio ≥ threshold |
| Oscillation near threshold | Single threshold for activate/deactivate | Hysteresis: deactivate at threshold×0.75 |
| Stuck active during tracking loss | No occlusion timeout | `none_streak` counter + EMA decay after 45 frames |
| Abrupt pop-on | Binary on/off | Proportional strength: ramp from threshold to threshold×2 |
| FaceParser conflict | Unconditionally overrides user's FaceParser settings | Remove forced FaceParser override |
| Misses small faces | MIN_MOUTH_SPAN_PX=8.0 too large for small/distant faces | Lower to 4.0 |
