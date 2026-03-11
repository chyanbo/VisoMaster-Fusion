# Auto-Mouth Expression Restorer — Implementation Plan

## Problem

When a target face (the person in the video) opens their mouth wide — eating, yawning,
laughing — the swapped face may not open its mouth correspondingly, causing an unnatural
"closed/half-open" mouth artifact on the swapped result.
Goal: **detect wide-open mouth automatically** and activate the expression restorer's
lip-transfer (+ Face Parser lower lip: 1) for exactly those frames, without requiring manual markers.

---

## Core Logic

Three rules, in priority order:

1. **Detection succeeds AND ratio ≥ threshold** → **activate**
2. **Detection fails or landmarks invalid** → **stay in current state** (object covering mouth — can't confirm closed, keep effect running)
3. **Detection succeeds AND ratio < threshold** → **deactivate** (mouth confirmed normal/closed)

EMA provides the only smoothing: a single low-ratio frame won't immediately deactivate
because recent high-ratio frames keep the smoothed value above threshold.

### Graceful failure guarantee

`apply_face_expression_restorer` returns the `target` tensor **unchanged** whenever its
own internal landmark detection fails (empty list) — confirmed at `frame_edits.py:116-119`
and `162-165`.  LivePortrait models are lazy-loaded on first use.  So calling the restorer
with auto-synthesized params is always safe: worst case it is a no-op.

---

## Eating Scenario Coverage

| Scene | Detection result | Ratio | State machine outcome |
|---|---|---|---|
| Anticipation (mouth barely open) | Succeeds | Low | Inactive — correct |
| **Mouth wide open** to receive food | Succeeds | High | **Activates ✓** |
| Object tip entering mouth (inner landmarks distorted) | Succeeds but ratio unreliable | Low or mid | EMA inertia keeps smoothed value above threshold for brief dips |
| **Object fully in mouth** (spoon, banana, lollipop) | **Fails → 5-pt fallback kps** | `len < 203` → None | **Rule 2 — stays active ✓** |
| **Hand / fingers over mouth** | **Fails → 5-pt fallback kps** | `len < 203` → None | **Rule 2 — stays active ✓** |
| Chewing (cyclic open/close) | Alternates valid/invalid | Oscillates | EMA keeps smoothed value high; invalid frames apply rule 2 |
| Mouth confirmed closed after eating | Succeeds | Low (< threshold) | **Deactivates ✓** |
| Straw in mouth (lips sealed, correct low ratio) | Succeeds | Low | Correctly stays inactive |
| Normal speech | Succeeds | Variable but low | Correctly stays inactive unless wide open |

**Note on `kps` when `LandmarkDetectToggle=False`:** The pipeline always populates `kps_all` —
when landmark detection is disabled it falls back to the 5-point keypoints (shape `(5, 2)`).
`compute_lip_open_ratio_203` and `compute_lip_open_ratio_68` catch this via `len(kps) < 203`
/ `< 68` and return `None`, correctly applying rule 2.

**VR180 mode:** In VR180, landmarks are detected on the per-eye perspective crop
(512×512), not the full equirectangular image. `kps_all_on_crop_param` is therefore in
crop coordinates.  The ratio formula is scale-invariant, so the computation is identical.
If landmark detection fails for one eye and the VR mirror fallback also fails,
`kps_all_on_crop_param` will be `None` → `len` check → `None` → rule 2 (stay active).

---

## Detection Method

### No extra inference — reuse already-computed landmarks

The call sites in `_process_frame_standard` already have `kps_all` for each face (as
`best_fface["kps_all"]` or `fface["kps_all"]`) before `swap_core` is called.  The ratio
computation happens **at the call site**, keyed to the `TargetFaceCardButton` object (which
is also present at both call sites as `target_face` / `best_target`).

The ratio formula is **scale- and translation-invariant** (ratio of two distances), so
full-image coordinates work identically to crop-space coordinates.

### 203-pt Lip Open Ratio (primary)

```
lip_open_ratio = ‖kps[90] − kps[102]‖   (inner upper↔lower lip vertical gap)
                 ─────────────────────────
                 ‖kps[48] − kps[66]‖     (mouth width, corner to corner)
```

Uses `faceutil.calc_lip_close_ratio`.  Closed ≈ 0.03–0.08.  Normal speech ≈ 0.10–0.18.
Wide eating/yawning ≥ 0.25.

### 68-pt Lip Open Ratio (if user has "68" selected)

```
lip_open_ratio_68 = ‖kps[62] − kps[66]‖   (inner lip vertical)
                    ───────────────────────
                    ‖kps[48] − kps[54]‖    (mouth corners)
```

### Unsupported models → ratio = None → rule 2

Models "5", "3d68", "98", "106", "478" produce `len(kps) < 203` or wrong index layouts.
`ratio = None` → rule 2 (stay in current state).  This is a safe no-op: if state starts
`active=False` and never activates, the feature simply does nothing until the user corrects
the model selection.  The UI toggle handler (Step 4) prevents this in the normal path.

### Validity check (catches collapsed detections)

```python
span = ‖kps[48] − kps[66]‖  (203-pt)   or   ‖kps[48] − kps[54]‖  (68-pt)
valid = span ≥ MIN_MOUTH_SPAN_PX   # 8 px — collapse guard only
```

If span < minimum → `None` → rule 2.

### EMA cold-start note

On first activation (state fresh, `ema=0.0`), with default α=0.40 and threshold=0.20, a
ratio of 0.30 needs ~3 frames to push EMA above threshold (frame 1: 0.12, frame 2: 0.19,
frame 3: 0.24).  This ~0.1 s delay is acceptable.  Users needing faster response can
raise α toward 1.0.

---

## Landmark model selection — interaction with auto-mouth

`control["LandmarkDetectModelSelection"]` options: `["5", "68", "3d68", "98", "106", "203", "478"]`

| Selected model | Auto-mouth behaviour |
|---|---|
| `"203"` | Use 203-pt indices on `kps_all` — full support |
| `"68"` | Use 68-pt indices on `kps_all` — full support |
| Any other | `ratio = None` → rule 2; UI toggle handler forces switch to "203" |

`LandmarkDetectToggle=False` → `kps_all` contains 5-pt fallback → `len < 203` → `None` →
rule 2.  UI toggle handler also enables `LandmarkDetectToggle`.

---

## New UI Settings

Add a collapsible **"Auto Mouth Expression"** sub-section inside the **"Expression Restorer"**
group in `app/ui/widgets/swapper_layout_data.py`.  All keys in `parameters` (per-face,
stored on `TargetFaceCardButton`).

| Widget key | Type | Default | Range | Description |
|---|---|---|---|---|
| `AutoMouthExpressionEnableToggle` | Toggle | False | — | Master enable; triggers landmark model check on change |
| `AutoMouthOpenThresholdDecimalSlider` | Decimal slider | 0.20 | 0.05–0.60 | Lip-open ratio that triggers activation. Has **"Set from frame"** action button (see Step 4a) |
| `AutoMouthEMAAlphaDecimalSlider` | Decimal slider | 0.40 | 0.05–1.00 | EMA smoothing (lower = smoother/slower; raise for faster response) |
| `AutoMouthExpressionStrengthDecimalSlider` | Decimal slider | 0.80 | 0.10–1.50 | `FriendlyFactor` for lips when auto-activated |
| `AutoMouthNormalizeLipsToggle` | Toggle | True | — | Enable lip-ratio normalisation when auto-activated |

`AutoMouthExpressionEnableToggle` is independent of `FaceExpressionEnableBothToggle`
(no `parentToggle`).

---

## Implementation Steps

### Step 1 — Mouth Openness Helper (`app/processors/mouth_openness.py`)

New file (~65 lines):

```python
"""Auto-mouth: detect mouth openness from pipeline landmarks; maintain on/stay/off state."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from app.processors.utils import faceutil

MIN_MOUTH_SPAN_PX = 8.0  # collapse guard (full-image coords)


def compute_lip_open_ratio_203(kps: np.ndarray) -> float | None:
    """Return lip-open ratio from pipeline 203-pt kps (full-image coords), or None."""
    if kps is None or len(kps) < 203:
        return None
    span = float(np.linalg.norm(kps[48] - kps[66]))
    if span < MIN_MOUTH_SPAN_PX:
        return None
    ratio = faceutil.calc_lip_close_ratio(kps[None])   # shape (1, 1)
    return float(ratio[0, 0])


def compute_lip_open_ratio_68(kps: np.ndarray) -> float | None:
    """Return lip-open ratio from pipeline 68-pt kps (full-image coords), or None."""
    if kps is None or len(kps) < 68:
        return None
    span = float(np.linalg.norm(kps[48] - kps[54]))
    if span < MIN_MOUTH_SPAN_PX:
        return None
    vert = float(np.linalg.norm(kps[62] - kps[66]))
    return vert / (span + 1e-6)


@dataclass
class MouthOpennessState:
    active: bool = False
    ema: float = 0.0

    def update(self, ratio: float | None, alpha: float, threshold: float) -> bool:
        """
        ratio=None  → detection failed / unsupported model; stay in current state (rule 2).
        ratio≥threshold → activate (rule 1).
        ratio<threshold → deactivate (rule 3).
        """
        if ratio is None:
            return self.active          # rule 2 — stay

        self.ema = alpha * ratio + (1.0 - alpha) * self.ema

        self.active = self.ema >= threshold
        return self.active

    def reset(self) -> None:
        self.active = False
        self.ema = 0.0
```

### Step 2 — State attribute on `TargetFaceCardButton`

In `app/ui/widgets/widget_components.py`, add to `TargetFaceCardButton.__init__`:

```python
from app.processors.mouth_openness import MouthOpennessState

# Auto-mouth: per-face temporal mouth-openness tracking
self.mouth_openness_state: MouthOpennessState = MouthOpennessState()
```

This is consistent with the existing pattern of per-face state (`aged_input_embedding`,
`aged_kv_map`) already stored on `TargetFaceCardButton`.

State automatically resets whenever a new target face button is created (video change,
face re-assignment) because a new `TargetFaceCardButton` instance is constructed with a
fresh `MouthOpennessState`.

**No changes to `swap_core`'s parameter list are needed.**

### Step 3 — Detection at all three `swap_core` call sites

There are **three** places in the codebase where `swap_core` is called:

| # | Line | Function | Mode | Key variables |
|---|---|---|---|---|
| A | ~1645 | `_process_frame_standard` | Standard — best-match branch | `target_face`, `best_fface["kps_all"]`, `params`, `control` |
| B | ~1742 | `_process_frame_standard` | Standard — swap-all-matches branch | `best_target`, `fface["kps_all"]`, `params`, `control` |
| C | ~612 | `_process_single_vr_perspective_crop_multi` | **VR180** | `target_face_button`, `kps_all_on_crop_param`, `parameters_for_face`, `control_global` |

All three sites have the `TargetFaceCardButton` (with `mouth_openness_state`) and the
already-computed landmark array available.  The same detection logic is inserted at each.

**VR180 coordinate note**: in site C, `kps_all_on_crop_param` contains landmarks in the
*perspective-crop coordinate system* (detected on the 512×512 crop, not the full equirect
image).  The lip-open ratio is a ratio of distances and is therefore scale-invariant — the
computation is identical to sites A and B.

**VR180 stereo note**: VR180 processes left and right eye crops separately, both using the
same `target_face_button`.  Since `mouth_openness_state` lives on that shared button, both
eye crops share one EMA state.  This is correct — the face has one mouth, and whichever eye
sees it first for a given frame updates the state; the second eye's crop (same frame) then
reads the already-updated state.

#### Reusable helper (extract to avoid duplication)

Because the same block is needed at all three sites, extract it as a private helper on
`FrameWorker`.

```python
def _apply_auto_mouth(
    self,
    params: dict,          # plain dict or ParametersDict — both supported
    kps_all: np.ndarray | None,
    target_fb: "widget_components.TargetFaceCardButton",
    control: dict,
) -> dict:
    """
    Compute auto-mouth lip-open ratio from already-detected pipeline landmarks.
    Returns params unchanged (same object, zero allocation) when inactive.
    Returns a new plain dict copy with synthesized expression keys when active.
    """
    if not params.get("AutoMouthExpressionEnableToggle", False):
        return params

    from app.processors.mouth_openness import (
        compute_lip_open_ratio_203,
        compute_lip_open_ratio_68,
    )
    _alpha     = params.get("AutoMouthEMAAlphaDecimalSlider", 0.40)
    _threshold = params.get("AutoMouthOpenThresholdDecimalSlider", 0.20)
    _lmk_model = control.get("LandmarkDetectModelSelection", "203")

    _ratio = None
    if _lmk_model == "203":
        _ratio = compute_lip_open_ratio_203(kps_all)
    elif _lmk_model == "68":
        _ratio = compute_lip_open_ratio_68(kps_all)
    else:
        # Unsupported model — warn once per session, then fall through to rule 2
        if not getattr(self, "_auto_mouth_warned", False):
            print(
                f"[WARN] Auto-mouth requires landmark model '203' or '68'. "
                f"Current model is '{_lmk_model}'. Feature disabled until model is changed."
            )
            self._auto_mouth_warned = True

    # Defensive access: mouth_openness_state might be absent on older button objects
    _state = getattr(target_fb, "mouth_openness_state", None)
    if _state is None:
        from app.processors.mouth_openness import MouthOpennessState
        target_fb.mouth_openness_state = MouthOpennessState()
        _state = target_fb.mouth_openness_state

    _auto_active = _state.update(_ratio, _alpha, _threshold)

    if _auto_active and not params.get("FaceExpressionEnableBothToggle", False):
        _strength  = params.get("AutoMouthExpressionStrengthDecimalSlider", 0.80)
        _normalize = params.get("AutoMouthNormalizeLipsToggle", True)
        _p = dict(params)                                        # shallow copy — safe (see note)
        _p["FaceExpressionEnableBothToggle"]                     = True
        _p["FaceExpressionModeSelection"]                        = "Advanced"
        _p["FaceExpressionBeforeTypeSelection"]                  = "Beginning"
        # Lips: the primary target
        _p["FaceExpressionLipsToggle"]                           = True
        _p["FaceExpressionFriendlyFactorLipsDecimalSlider"]      = _strength
        _p["FaceExpressionRelativeLipsToggle"]                   = True
        _p["FaceExpressionNormalizeLipsEnableToggle"]            = _normalize
        # Jaw: must move coherently with lips to avoid warp-field discontinuities
        # at the lip-cheek boundary (LivePortrait warp-decode expects coherent keypoints)
        _p["FaceExpressionGeneralToggle"]                        = True
        _p["FaceExpressionGeneralJawToggle"]                     = True
        _p["FaceExpressionFriendlyFactorGeneralDecimalSlider"]   = _strength * 0.5
        # All other regions: off
        _p["FaceExpressionEyesToggle"]                           = False
        _p["FaceExpressionBrowsToggle"]                          = False
        _p["FaceExpressionGeneralNoseToggle"]                    = False
        _p["FaceExpressionGeneralCheekToggle"]                   = False
        _p["FaceExpressionGeneralContourToggle"]                 = False
        _p["FaceExpressionGeneralHeadToggle"]                    = False
        return _p

    return params
```

**Why jaw must move with lips**: LivePortrait's warp-decode model was trained to expect
all 21 keypoints to move coherently.  Providing only lip-keypoint deltas while leaving jaw
keypoints stationary creates an unnatural keypoint geometry, producing subtle "pulling" or
"smearing" artifacts at the lip-cheek boundary.  Enabling `FaceExpressionGeneralJawToggle`
at half strength (`_strength * 0.5`) moves the jaw coherently with the lips, eliminating
this discontinuity without visibly affecting other face regions.

**No double-run risk**: The three `apply_face_expression_restorer` call-sites inside
`swap_core` are gated by mutually exclusive values of `FaceExpressionBeforeTypeSelection`
(`"Beginning"` / `"After First Restorer"` / `"After Second Restorer"`).  Auto-mouth always
sets it to `"Beginning"`.  Even if the user had a different stage configured, the manual
restorer is fully disabled (`FaceExpressionEnableBothToggle=False`) whenever auto-mouth
synthesizes its own params, so each stage fires at most once.

**Shallow copy safety**: `apply_face_expression_restorer` uses `.get(key, default)` for
all parameter accesses.  A plain `dict` copy is safe — no bare `[]` access on potentially
missing keys within the restorer.  The copy does NOT need to be a `ParametersDict`.

#### Site A — standard best-match branch (~line 1645)

`params` at this site is a `ParametersDict`.  `_apply_auto_mouth` returns it unchanged
(same object) when auto-mouth is inactive, or a new plain dict when active.  Either is
safe for `swap_core` — `cast(dict, ...)` in the original code was only a type annotation,
not an actual conversion; `ParametersDict` already supports all dict operations.

```python
_params_for_swap = self._apply_auto_mouth(
    params, best_fface["kps_all"], target_face, control
)
img, best_fface["original_face"], best_fface["swap_mask"] = self.swap_core(
    img,
    best_fface["kps_5"],
    best_fface["kps_all"],
    s_e=s_e,
    t_e=target_face.get_embedding(arcface_model),
    parameters=cast(dict, _params_for_swap),
    control=control,
    dfm_model_name=params["DFMModelSelection"],
    kv_map=_reaging_kv,
)
```

#### Site B — standard swap-all-matches branch (~line 1742)

```python
_params_for_swap = self._apply_auto_mouth(
    params, fface["kps_all"], best_target, control
)
img, fface["original_face"], fface["swap_mask"] = self.swap_core(
    img,
    fface["kps_5"],
    fface["kps_all"],
    s_e=s_e,
    t_e=best_target.get_embedding(arcface_model),
    parameters=cast(dict, _params_for_swap),
    control=control,
    dfm_model_name=params["DFMModelSelection"],
    kv_map=_reaging_kv,
)
```

When auto-mouth is inactive, `_apply_auto_mouth` returns `params` unchanged — zero extra
allocation.  When active, it returns a plain dict copy with the synthesized keys.  The
existing `cast(dict, ...)` wrapper remains and is harmless in both cases.

#### Site C — VR180 (~line 607, inside `_process_single_vr_perspective_crop_multi`)

Insert immediately before the `try:` block that wraps the `swap_core` call.

**Critical**: the existing VR code passes `parameters_for_face.data` (the underlying plain
dict of the `ParametersDict`) to `swap_core`.  `swap_core` has 80+ bare `parameters["key"]`
accesses — passing a `ParametersDict` object instead would trigger its lazy-set side-effect
on every missing-key access, causing unexpected mutations.  Therefore `_apply_auto_mouth`
must always receive and return a **plain dict** at this site too.

```python
# Always resolve to a plain dict before passing to _apply_auto_mouth
_params_for_swap_vr = self._apply_auto_mouth(
    parameters_for_face.data,          # plain dict — consistent with existing VR convention
    kps_all_on_crop_param,
    target_face_button,
    control_global
)
try:
    (
        swapped_face_512_torch_rgb_uint8,
        comprehensive_mask_1x512x512_from_swap_core,
        _,
    ) = self.swap_core(
        perspective_crop_torch_rgb_uint8,
        kps_5_on_crop_param,
        kps=kps_all_on_crop_param,
        s_e=s_e_for_swap_core,
        t_e=t_e_for_swap_np,
        parameters=_params_for_swap_vr,        # ← changed from parameters_for_face.data
        control=control_global,
        ...
    )
```

When auto-mouth is inactive, `_apply_auto_mouth` returns `parameters_for_face.data`
unchanged — identical to the original code path.

### Step 4 — UI toggle handler: auto-switch landmark model

**`exec_function` signature clarification**: for per-face parameter widgets the framework
calls `exec_function(main_window, new_value, *exec_function_args)` where `new_value` is
the new widget value.

In `app/ui/widgets/swapper_layout_data.py`:

```python
"AutoMouthExpressionEnableToggle": {
    "label": "Enable Auto Mouth Expression",
    "default": False,
    "exec_function": control_actions.handle_auto_mouth_toggle,
    "exec_function_args": [],          # no extra args — new_value is passed automatically
    ...
},
```

In `app/ui/widgets/actions/control_actions.py`:

```python
def handle_auto_mouth_toggle(main_window: "MainWindow", new_value: bool) -> None:
    """When auto-mouth is enabled, ensure a compatible landmark model is active."""
    if not new_value:
        return  # toggling off — leave landmark settings as-is

    # 1. Ensure landmark detection is turned on
    if not main_window.control.get("LandmarkDetectToggle", False):
        main_window.control["LandmarkDetectToggle"] = True
        handle_landmark_state_change(main_window, "LandmarkDetectToggle")
        # Also update the checkbox widget to reflect the change visually.
        # Use the same pattern as other control actions that update widgets:
        lmk_toggle_widget = main_window.control_widgets.get("LandmarkDetectToggle")
        if lmk_toggle_widget is not None:
            lmk_toggle_widget.setChecked(True)

    # 2. If the current model is not "203" or "68", force it to "203"
    current_model = main_window.control.get("LandmarkDetectModelSelection", "203")
    if current_model not in ("203", "68"):
        main_window.control["LandmarkDetectModelSelection"] = "203"
        handle_landmark_model_selection_change(main_window, "203", "LandmarkDetectModelSelection")
        # Update the combo-box widget to reflect the forced change.
        model_widget = main_window.control_widgets.get("LandmarkDetectModelSelection")
        if model_widget is not None:
            model_widget.setCurrentText("203")
```

Note: `main_window.control_widgets` is illustrative — use whatever dict/lookup the
codebase uses for control widgets (the same pattern used in other `control_actions.py`
functions that programmatically update a control widget value).

### Step 4a — "Set from frame" action button on the threshold slider

#### Widget definition in `swapper_layout_data.py`

Add an `action_button` to `AutoMouthOpenThresholdDecimalSlider`.  This follows the
identical pattern used by `FaceReagingTargetAgeSlider`:

```python
"AutoMouthOpenThresholdDecimalSlider": {
    "level": 2,
    "label": "Open Threshold",
    "min_value": "0.05",
    "max_value": "0.60",
    "default": "0.20",
    "step_decimal": 2,
    "parentToggle": "AutoMouthExpressionEnableToggle",
    "requiredToggleValue": True,
    "enable_refresh_frame": False,
    "help": "Lip-open ratio that triggers auto-mouth activation. "
            "Click 'Set from frame' to measure from the current video frame.",
    "action_button": {
        "label": "Set from frame",
        "help": "Seek to a frame where the mouth is open at the desired trigger level, "
                "then click this button. The measured lip-open ratio is set as the threshold.",
        "exec_function": control_actions.set_auto_mouth_threshold_from_frame,
    },
},
```

The `action_button` is rendered as a small QPushButton alongside the slider (same as the
re-aging Apply button, max width 55 px).  Its `exec_function` receives only `main_window`
as argument (framework always calls `partial(exec_function, main_window)` with no extras).

#### Action function in `app/ui/widgets/actions/control_actions.py`

```python
def set_auto_mouth_threshold_from_frame(main_window: "MainWindow") -> None:
    """
    Measure the lip-open ratio of the largest detected face in the current video frame
    and write the result to the AutoMouthOpenThresholdDecimalSlider.

    Workflow:
      1. Guard: frame and selected target face must exist.
      2. Detect faces in the current frame.
      3. If multiple faces detected, pick the one whose 5-pt keypoints are closest
         to the selected target face button's stored kps_5 (from its assigned input face);
         fall back to the largest face by bbox area if no match is available.
      4. Run landmark detection (203-pt if selected/available, else 68-pt).
      5. Compute lip-open ratio via compute_lip_open_ratio_203 / _68.
      6. Clamp to slider range [0.05, 0.60] and write to the threshold slider widget.
    """
    import torch
    import numpy as np
    from app.processors.mouth_openness import (
        compute_lip_open_ratio_203,
        compute_lip_open_ratio_68,
    )

    # ── 1. Guards ──────────────────────────────────────────────────────────────
    target_fb = main_window.cur_selected_target_face_button
    if target_fb is None:
        print("[Auto-mouth] No target face selected.")
        return

    raw_frame = main_window.video_processor.current_frame   # RGB uint8 ndarray or None
    if raw_frame is None:
        print("[Auto-mouth] No frame available (no video loaded?).")
        return

    models_processor = main_window.models_processor

    # ── 2. Convert frame to CHW tensor for detection ───────────────────────────
    frame_chw = torch.from_numpy(raw_frame).permute(2, 0, 1).contiguous()

    # ── 3. Detect faces ────────────────────────────────────────────────────────
    detector_model = main_window.control.get("DetectorModelSelection", "SCRFD")
    bboxes, kpss_5, _ = models_processor.run_detect(
        frame_chw,
        detector_model,
        max_num=10,
        score=0.30,                 # permissive threshold
        input_size=(512, 512),
        use_landmark_detection=False,
        rotation_angles=[0],
    )

    if bboxes is None or (hasattr(bboxes, '__len__') and len(bboxes) == 0):
        print("[Auto-mouth] No face detected in the current frame.")
        return

    # ── 4. Pick best face ──────────────────────────────────────────────────────
    # Prefer the face closest to the target button's known source-face centre.
    # Fall back to largest face by bbox area when no source kps are stored.
    best_idx = 0
    ref_kps = None
    if target_fb.assigned_input_faces:
        first_id = next(iter(target_fb.assigned_input_faces))
        ref_kps = target_fb.assigned_input_faces[first_id].get("kps_5")

    if ref_kps is not None and len(kpss_5) > 1:
        # Closest face by mean distance of 5-pt keypoints to source face kps
        ref_centre = np.mean(ref_kps, axis=0)
        dists = [np.linalg.norm(np.mean(k, axis=0) - ref_centre) for k in kpss_5]
        best_idx = int(np.argmin(dists))
    else:
        # Largest face by bounding box area
        areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in bboxes]
        best_idx = int(np.argmax(areas))

    best_bbox  = bboxes[best_idx]
    best_kps_5 = kpss_5[best_idx]

    # ── 5. Landmark detection (203-pt preferred; 68-pt fallback) ──────────────
    lmk_model = main_window.control.get("LandmarkDetectModelSelection", "203")
    if lmk_model not in ("203", "68"):
        lmk_model = "203"               # force a usable model for this one-shot call

    _, kps_all, _ = models_processor.landmark_detectors.run_detect_landmark(
        img=frame_chw,
        bbox=best_bbox,
        det_kpss=best_kps_5,
        detect_mode=lmk_model,
    )

    if not (hasattr(kps_all, '__len__') and len(kps_all) > 0):
        print("[Auto-mouth] Landmark detection failed for the selected face.")
        return

    # ── 6. Compute lip-open ratio ──────────────────────────────────────────────
    ratio = (
        compute_lip_open_ratio_203(kps_all)
        if lmk_model == "203"
        else compute_lip_open_ratio_68(kps_all)
    )

    if ratio is None:
        print("[Auto-mouth] Lip-open ratio could not be computed (landmarks invalid?).")
        return

    # ── 7. Clamp and write to slider ───────────────────────────────────────────
    clamped = round(max(0.05, min(0.60, ratio)), 2)
    main_window.parameter_widgets["AutoMouthOpenThresholdDecimalSlider"].set_value(clamped)
    print(f"[Auto-mouth] Threshold set to {clamped:.2f}  (raw ratio: {ratio:.3f})")
```

#### Design notes

**Face selection heuristic**: the function first tries to match the detected face to the
target face button's assigned source face (by comparing 5-pt keypoint centres in image
space).  This is a lightweight proxy for "which detected face belongs to this target slot"
without needing a full arcface similarity comparison.  If no source face is assigned, it
falls back to the largest detected face — the most common case where the target person
dominates the frame.

**Model loading**: `run_detect_landmark` lazy-loads the 203-pt model if not yet loaded,
using the same path as the processing pipeline.  This may cause a one-time delay of ~1–2 s
on first click; subsequent clicks are instant.

**No refresh**: `enable_refresh_frame: False` is set on the slider so that changing its
value via `set_value()` does NOT trigger a frame reprocess.  The threshold is just stored;
it takes effect at the next processed frame automatically.

**Image input format**: `main_window.video_processor.current_frame` is an RGB uint8
`numpy.ndarray` (HWC).  Converting to CHW torch tensor matches what `run_detect` and
`run_detect_landmark` expect.

**Guard for images vs videos**: `current_frame` is `None` when no media is loaded.  The
function returns early with a log message in that case.  For still images the same path
works — the current frame is the image itself.

### Step 5 — Patch the three restorer call-sites inside `swap_core`

`swap_core` now receives `_params_for_swap` (already synthesized) as `parameters`.
The three existing `apply_face_expression_restorer` call-sites at lines ~3265, ~3619,
~3690 require **no changes** — they already use whatever `parameters` was passed in.

This is the cleanest approach: `swap_core` stays unmodified; all the auto-mouth logic
lives at the call sites where `target_face` (the TargetFaceCardButton with state) is
naturally available.

---

## Workspace Loading — Limitation and Mitigation

**Fact**: `load_saved_workspace` restores per-face `parameters` values directly without
calling per-face `exec_functions`.  Control-level settings (`control` dict) do have their
`exec_functions` called via `set_control_widgets_values`.

**Consequence**: If a saved workspace has `AutoMouthExpressionEnableToggle=True` and
`LandmarkDetectModelSelection` is some incompatible model (e.g. "98"), loading that
workspace will NOT auto-switch to "203".

**Runtime behaviour**: `compute_lip_open_ratio_203/68` will return `None` (unsupported
model) → rule 2 → state stays `active=False` forever.  The feature silently does nothing.
**No crash, no incorrect output** — just the feature being effectively disabled.

**Mitigation**: Add a one-time runtime log/warning inside the auto-mouth detection block:

```python
if params.get("AutoMouthExpressionEnableToggle", False):
    _lmk_model = control.get("LandmarkDetectModelSelection", "203")
    if _lmk_model not in ("203", "68"):
        # Log once per session (use a flag on self to avoid log spam)
        if not getattr(self, "_auto_mouth_warned", False):
            print("[WARN] Auto-mouth requires landmark model '203' or '68'. "
                  "Current model is '{}'. Feature disabled.".format(_lmk_model))
            self._auto_mouth_warned = True
```

A follow-up improvement could be to also call `handle_auto_mouth_toggle` for each
`TargetFaceCardButton` during workspace load.

---

## Data Flow

```
Per-frame (both standard AND VR180 paths):

  _process_frame_standard            _process_single_vr_perspective_crop_multi
  ┌──────────────────────┐           ┌────────────────────────────────────────┐
  │ target_face          │           │ target_face_button                     │
  │ kps_all (full-img)   │           │ kps_all_on_crop_param (crop-coords)    │
  │ params               │           │ parameters_for_face                    │
  │ control              │           │ control_global                         │
  └──────────┬───────────┘           └──────────────────┬─────────────────────┘
             │                                          │
             └──────────── self._apply_auto_mouth() ◄───┘
                               │
                     AutoMouthExpressionEnableToggle?
                               │ True
                               ▼
                     control["LandmarkDetectModelSelection"]
                       "203" → compute_lip_open_ratio_203(kps_all)
                       "68"  → compute_lip_open_ratio_68(kps_all)
                       other → None  (one-time warning)
                               │
                     target_fb.mouth_openness_state.update(ratio, α, threshold)
                       ratio ≥ threshold → active = True   (rule 1)
                       ratio = None      → active unchanged (rule 2)
                       ratio < threshold → active = False  (rule 3)
                               │
                     active AND FaceExpressionEnableBothToggle == False?
                       Yes → return modified _params_for_swap (lips only, Advanced)
                       No  → return original params unchanged
                               │
                               ▼
              swap_core(..., parameters=_params_for_swap, ...)
                               │
                   apply_face_expression_restorer uses _params_for_swap
                   (swap_core itself has no changes)
```

**UI toggle time** (separate from per-frame path):
```
User enables AutoMouthExpressionEnableToggle
      │
      ├─ LandmarkDetectToggle == False?  → enable it + update widget
      │
      └─ LandmarkDetectModelSelection not in {"203","68"}?  → force to "203"
               loads 203 model, unloads previous model, updates combo-box widget
```

---

## File Change Summary

| File | Change |
|---|---|
| `app/processors/mouth_openness.py` | **New** — `compute_lip_open_ratio_203`, `compute_lip_open_ratio_68`, `MouthOpennessState` |
| `app/ui/widgets/widget_components.py` | Add `mouth_openness_state: MouthOpennessState = MouthOpennessState()` to `TargetFaceCardButton.__init__` |
| `app/processors/workers/frame_worker.py` | `_apply_auto_mouth()` helper method; call it at all **three** `swap_core` sites: standard best-match (~1645), standard all-matches (~1742), VR180 `_process_single_vr_perspective_crop_multi` (~607) |
| `app/ui/widgets/swapper_layout_data.py` | 5 new widgets in "Auto Mouth Expression" sub-section; `exec_function` on toggle |
| `app/ui/widgets/actions/control_actions.py` | `handle_auto_mouth_toggle(main_window, new_value)` + `set_auto_mouth_threshold_from_frame(main_window)` |
| `tests/unit/processors/test_mouth_openness.py` | **New** — unit tests |

**`swap_core` itself requires no changes.**

---

## Testing Plan

1. **`compute_lip_open_ratio_203`**: synthetic `(203, 2)` array with known distances →
   assert expected ratio.  `kps=None` → `None`.  `len(kps) < 203` (e.g. 5-pt fallback) → `None`.
   Collapsed span → `None`.

2. **`compute_lip_open_ratio_68`**: same for 68-pt indices.

3. **`MouthOpennessState` — rule 1**: feed ratio above threshold → `active=True`.

4. **`MouthOpennessState` — rule 2**: `active=True` → `update(None, …)` → remains `True`.
   Also `active=False` → `update(None, …)` → remains `False`.

5. **`MouthOpennessState` — rule 3**: warm to `active=True`; feed ratio below threshold
   enough EMA steps → `active=False`.

6. **EMA cold-start**: with α=0.40, threshold=0.20, ratio=0.30 — verify takes ~3 frames
   to activate (expected EMA values: 0.12, 0.19, 0.23).

7. **5-pt fallback `kps`**: pass `kps` with `len=5` to `compute_lip_open_ratio_203` →
   returns `None` (not crash, not wrong ratio).

8. **Integration — 203 model**: `control["LandmarkDetectModelSelection"]="203"`, high-ratio
   `kps_all`; assert `_params_for_swap` has `FaceExpressionLipsToggle=True` and
   `FaceExpressionEnableBothToggle=True`.  Verify `params` (original) is unchanged.

9. **Integration — 68 model**: same with "68" and correct 68-pt geometry.

10. **Integration — unsupported model (e.g. "98")**: state `active=True`; assert stays
    `active=True` (rule 2, not erroneously deactivated).

11. **Integration — stays active through occlusion**: warm to `active=True`; pass 5-pt
    `kps_all` (landmark detection off simulation) for multiple calls; assert
    `_params_for_swap` continues to have lips enabled.

12. **Integration — deactivates**: warm to `active=True`; feed valid low-ratio `kps_all`
    for enough frames; assert `_params_for_swap` eventually equals `params` (no override).

13. **No interference when user manually enables restorer**: set
    `FaceExpressionEnableBothToggle=True` in params; trigger auto-mouth active; assert
    `_params_for_swap is params` (shallow copy NOT made).

14. **Regression**: `AutoMouthExpressionEnableToggle=False` → no ratio computation, no
    copy, `_params_for_swap is params`.

15. **`handle_auto_mouth_toggle` — incompatible model**: mock `control["LandmarkDetect
    ModelSelection"]="98"`, call with `new_value=True`; assert model changed to "203".

16. **`handle_auto_mouth_toggle` — compatible model**: "68" selected, `new_value=True`;
    assert model NOT changed.

17. **`handle_auto_mouth_toggle` — toggle off**: `new_value=False`; assert no changes to
    control settings regardless of current model.

18. **VR180 — `_apply_auto_mouth` called with crop-coordinate `kps_all`**: synthesise a
    `(203, 2)` landmark array in crop-coordinate space (values in range 0–512); assert
    ratio is computed correctly (same formula as full-image coords — scale-invariant).

19. **VR180 — stereo eye sharing**: simulate two consecutive `_apply_auto_mouth` calls on
    the same `TargetFaceCardButton.mouth_openness_state` (left eye then right eye, same
    frame); verify the second call returns the already-updated `active` from the first
    (EMA updated once by left eye; right eye reads stable state).

20. **VR180 — `parameters_for_face.data` passthrough**: when auto-mouth is inactive,
    `_apply_auto_mouth` returns `parameters_for_face.data` unchanged (same object); assert
    `_params_for_swap_vr is parameters_for_face.data` (no copy made).

21. **Jaw coherence — synthesized params include jaw**: when auto-mouth synthesizes params,
    assert `FaceExpressionGeneralToggle=True`, `FaceExpressionGeneralJawToggle=True`,
    `FaceExpressionFriendlyFactorGeneralDecimalSlider == strength * 0.5`,
    and `FaceExpressionGeneralNoseToggle=False` (jaw only, not other general regions).

22. **No double-run**: synthesized params set `FaceExpressionBeforeTypeSelection="Beginning"`.
    Confirm that with `FaceExpressionEnableBothToggle=False` in original params, the restorer
    fires exactly once in `swap_core` (at "Beginning" stage only).

23. **Graceful missing `mouth_openness_state`**: construct a mock `TargetFaceCardButton`
    without the attribute; call `_apply_auto_mouth`; assert no `AttributeError` and that
    `mouth_openness_state` is created and attached to the button.

24. **Zero allocation when inactive**: call `_apply_auto_mouth` with
    `AutoMouthExpressionEnableToggle=False`; assert the returned object `is params`
    (identical object reference — no copy).

25. **`set_auto_mouth_threshold_from_frame` — no frame**: `current_frame=None`; assert
    early return (no exception, no slider write).

26. **`set_auto_mouth_threshold_from_frame` — no face selected**: `cur_selected_target_face_button=None`;
    assert early return.

27. **`set_auto_mouth_threshold_from_frame` — no face detected**: mock `run_detect`
    returning empty arrays; assert early return with log message, slider not written.

28. **`set_auto_mouth_threshold_from_frame` — landmark detection fails**: mock
    `run_detect_landmark` returning `([], [], [])`; assert early return, slider not written.

29. **`set_auto_mouth_threshold_from_frame` — ratio above max**: mock landmarks that give
    ratio 0.80; assert slider receives clamped value 0.60, not 0.80.

30. **`set_auto_mouth_threshold_from_frame` — ratio below min**: mock landmarks giving
    ratio 0.02; assert slider receives 0.05.

31. **`set_auto_mouth_threshold_from_frame` — face selection heuristic**: mock two detected
    faces; target button has stored source kps closer to face 1; assert best_idx = 0 (face 1
    chosen, not the larger face 2).

32. **`set_auto_mouth_threshold_from_frame` — unsupported model forced to 203**: set
    `LandmarkDetectModelSelection="98"`; assert `run_detect_landmark` is called with
    `detect_mode="203"` (not "98").

---

## Calibration Notes

- **Threshold 0.20**: calibrate by printing `ratio` and `active` to stdout on eating
  footage before finalising the default.

- **EMA alpha 0.40**: lower (0.20–0.30) for noisier footage or faster eating; higher
  (0.60–0.80) for snappier single-frame response.

- **Follow-up enhancement**: when auto-mouth is active, also increment `MouthParserSlider`
  by a small offset to widen the face-parser mask, ensuring the corrected mouth shape is
  not clipped.
