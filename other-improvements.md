# VisoMaster Fusion — Implementation Plan: Pipeline, VR180 & ByteTrack Improvements

**Document version:** 1.0
**Date:** 2026-03-05
**Scope:** Code-review findings from three independent analysis passes
**Status:** Pending implementation

---

## Table of Contents

1. [Review Scope](#1-review-scope)
2. [Summary by Area](#2-summary-by-area)
3. [Priority Matrix — Critical Fixes First](#3-priority-matrix--critical-fixes-first)
4. [Detailed Findings — 6.1: frame_worker.py Main Pipeline](#41-frameworkerpy--main-pipeline)
   - [Race Conditions](#race-conditions)
   - [Bugs](#bugs)
   - [Performance](#performance)
   - [Memory](#memory)
   - [Robustness](#robustness)
   - [Code Quality](#code-quality)
5. [Detailed Findings — 6.2: VR180 Processing](#42-vr180-processing)
6. [Detailed Findings — 6.3: ByteTrack Face Tracking](#43-bytetrack-face-tracking)
7. [Deferred / Architectural Items](#7-deferred--architectural-items)

---

## 1. Review Scope

Three areas of the codebase were reviewed:

| # | Area | Primary File(s) |
|---|------|-----------------|
| 1 | `frame_worker.py` main pipeline | `app/processors/frame_worker.py` |
| 2 | VR180 processing | `_process_frame_vr180`, `Equirec2Perspec_vr`, `PerspectiveConverter` |
| 3 | ByteTrack face tracking | ByteTracker integration in `frame_worker.py` / `run_detect` / `track_faces` |

---

## 2. Summary by Area

### 2.1 frame_worker.py — Main Pipeline (61 items)

| Category | HIGH | MED | LOW | Total |
|----------|------|-----|-----|-------|
| Race Condition (RACE) | 3 | 2 | 0 | **5** |
| Bug (BUG) | 5 | 5 | 4 | **14** |
| Performance (PERF) | 4 | 5 | 5 | **14** |
| Memory (MEM) | 0 | 2 | 1 | **3** |
| Robustness (ROBUST) | 4 | 4 | 4 | **12** |
| Code Quality (QUAL) | 0 | 3 | 10 | **13** |
| **Subtotal** | **16** | **21** | **24** | **61** |

### 2.2 VR180 Processing (16 items)

| Category | HIGH | MED | LOW | Total |
|----------|------|-----|-----|-------|
| Bug (BUG) | 2 | 5 | 1 | **8** |
| Performance (PERF) | 1 | 2 | 0 | **3** |
| Robustness (ROBUST) | 0 | 2 | 1 | **3** |
| Code Quality (QUAL) | 0 | 2 | 0 | **2** |
| **Subtotal** | **3** | **11** | **2** | **16** |

### 2.3 ByteTrack Face Tracking (14 items)

| Category | HIGH | MED | LOW | Total |
|----------|------|-----|-----|-------|
| Bug (BUG) | 3 | 2 | 0 | **5** |
| Race Condition (RACE) | 2 | 0 | 0 | **2** |
| Memory (MEM) | 0 | 1 | 0 | **1** |
| Performance (PERF) | 0 | 1 | 0 | **1** |
| Robustness (ROBUST) | 0 | 2 | 0 | **2** |
| Code Quality (QUAL) | 0 | 2 | 1 | **3** |
| **Subtotal** | **5** | **8** | **1** | **14** |

### Grand Total: **91 items** (24 HIGH, 40 MED, 27 LOW)

---

## 3. Priority Matrix — Critical Fixes First

Items that can crash the processing thread, corrupt output silently, or create data races that produce wrong results are listed here in recommended implementation order. Fix HIGH items before any MED or LOW work.

### Tier 1 — Must Fix (crash / data corruption / thread safety)

| ID | Area | Issue Summary |
|----|------|---------------|
| FW-RACE-01 | Pipeline | `target_faces` dict iterated from worker threads while UI mutates it |
| FW-RACE-02 | Pipeline | Qt UI widget state read from background worker threads |
| FW-RACE-03 | Pipeline | `last_detected_faces` / `last_processed_frame_number` written without lock |
| FW-BUG-01 | Pipeline | `kpss[i]` IndexError after tracker path — kpss / kpss_5 length mismatch |
| FW-BUG-03 | Pipeline | `input_face_affined` can be None, causing crash at first `.permute()` |
| FW-BUG-04 | Pipeline | Negative padding when image is smaller than 512px |
| FW-BUG-05 | Pipeline | DFM model receives wrong dtype/layout (CHW uint8 instead of HWC float32) |
| FW-ROBUST-02 | Pipeline | `tform.inverse` used without checking `tform.estimate()` return value |
| FW-ROBUST-03 | Pipeline | `calc_swapper_latent_*` None returns unguarded for 4 of 5 swapper models |
| FW-ROBUST-04 | Pipeline | `self.parameters[face_id]` KeyError if face added after snapshot |
| BT-01 | ByteTrack | Division by zero in `_calculate_iou` kills processing thread |
| BT-02 | ByteTrack | `det_scores` shape `(N,1)` causes broadcast errors in `_refine_landmarks` |
| BT-06 | ByteTrack | `self.tracker` accessed without lock from concurrent workers |
| BT-07 | ByteTrack | `self.frame_id += 1` without lock — Kalman filter state corruption |
| VR-01 | VR180 | 1-D bbox array for single detection crashes `calculate_theta_phi_from_bbox` |
| VR-02 | VR180 | Geometrically incorrect FOV near poles — faces at top/bottom grossly oversized |

### Tier 2 — High Value / Significant Correctness (MED severity)

| ID | Area | Issue Summary |
|----|------|---------------|
| FW-RACE-04 | Pipeline | `is_view_face_compare` / `is_view_face_mask` set from worker threads |
| FW-RACE-05 | Pipeline | `default_parameters.data` read without lock |
| FW-BUG-07 | Pipeline | `kps_all_on_crop` always None in VR mode — makeup editing silently disabled |
| FW-BUG-08 | Pipeline | Unreliable zero-face heuristic in SimSwap512 fallback |
| FW-BUG-09 | Pipeline | `_find_best_target_match` called 3x per face — can diverge if dict mutated |
| FW-BUG-10 | Pipeline | `ceil(StrengthAmountSlider/100)` produces discontinuous step function |
| FW-PERF-01 | Pipeline | O(F×T²) `_find_best_target_match` called 3x per face per frame |
| FW-PERF-04 | Pipeline | Three kernel tensors reallocated every call in `face_restorer_auto` |
| FW-ROBUST-05 | Pipeline | `local_control_state_from_feeder` not in `__init__` — AttributeError risk |
| FW-ROBUST-06 | Pipeline | `kps: np.ndarray | bool = False` bypasses the `.size == 0` guard |
| FW-ROBUST-07 | Pipeline | 1-D single-detection array iterates scalars in VR processing |
| BT-04 | ByteTrack | Coasted tracks silently dropped — occlusion-handling disabled |
| BT-05 | ByteTrack | `effective_score = 0.3` hardcoded, ignores user's `DetectorScoreSlider` |
| BT-08 | ByteTrack | `track_history` never pruned — memory leak in long sessions |
| VR-03 | VR180 | Asymmetric NMS distance threshold causes incorrect suppression |
| VR-04 | VR180 | `kps_all_on_crop` always None in VR (duplicate of FW-BUG-07) |
| VR-05 | VR180 | Frame re-uploaded to GPU even though tensor already on GPU |
| VR-14 | VR180 | Erosion kernel erodes small masks completely — crops silently discarded |
| VR-16 | VR180 | `padding_mode='border'` causes color artifact at longitude seam |

### Tier 3 — Refinements (LOW severity / code quality)

All FW-QUAL, FW-PERF LOW, FW-MEM LOW, VR-QUAL, VR-ROBUST LOW, BT-QUAL items.

---

## 4. Detailed Findings

### 4.1 frame_worker.py — Main Pipeline

---

#### Race Conditions

---

**ID:** FW-RACE-01
**Category:** Race Condition
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_find_best_target_match`, `_process_frame_standard`, `swap_core`

**Issue:**
`self.main_window.target_faces` is a plain `dict` that is iterated by pool worker threads. The Qt UI thread can add or remove face cards (mutating this dict) at any time. This can raise `RuntimeError: dictionary changed size during iteration` or, more subtly, produce wrong match results if a face is removed mid-iteration without raising.

**Fix:**
Snapshot `target_faces` at the start of `_process_frame_standard` under a lock:
```python
with self.lock:
    target_faces_snapshot = dict(self.main_window.target_faces)
```
Pass `target_faces_snapshot` through to all downstream callers (`_find_best_target_match`, `swap_core`) so no function iterates the live dict.

---

**ID:** FW-RACE-02
**Category:** Race Condition
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`, `_process_frame_standard`, `swap_core`

**Issue:**
`self.main_window.swapfacesButton.isChecked()` and `editFacesButton.isChecked()` are called from background worker threads. Qt documentation explicitly states that UI objects (including `QAbstractButton`) must only be accessed from the GUI thread. Calling them from worker threads is undefined behaviour and can cause crashes or incorrect values on certain platforms.

**Fix:**
Snapshot these booleans into `local_control_state_from_feeder` at feeder time (on the GUI thread) before the frame is queued:
```python
local_control_state_from_feeder['swap_enabled'] = self.main_window.swapfacesButton.isChecked()
local_control_state_from_feeder['edit_enabled'] = self.main_window.editFacesButton.isChecked()
```
Read from `local_control_state_from_feeder` in worker threads; never call `.isChecked()` on a background thread.

---

**ID:** FW-RACE-03
**Category:** Race Condition
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_standard`

**Issue:**
`self.last_detected_faces` and `self.last_processed_frame_number` are written from worker threads without any lock. Multiple concurrent single-frame workers share the same `FrameWorker` instance, so these attributes can be written simultaneously, producing torn reads and incorrect re-use of stale face data for live-preview.

**Fix:**
Use `self.lock` (declared in `__init__` at line 130 but never used) to guard these writes and their paired reads:
```python
with self.lock:
    self.last_detected_faces = detected
    self.last_processed_frame_number = frame_number
```

---

**ID:** FW-RACE-04
**Category:** Race Condition
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `process_and_emit_task`

**Issue:**
`self.is_view_face_compare` and `self.is_view_face_mask` are instance attributes set inside `process_and_emit_task`. Multiple concurrent single-frame worker threads share the same `FrameWorker` instance, so one thread's value can overwrite another's between assignment and use.

**Fix:**
Convert both to local variables within `process_and_emit_task`:
```python
is_view_face_compare = (control.get('ViewFaceCompareButton') == True)
is_view_face_mask = (control.get('ViewFaceMaskButton') == True)
```
Alternatively use `threading.local()` if the values are read in sub-functions.

---

**ID:** FW-RACE-05
**Category:** Race Condition
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_find_best_target_match`

**Issue:**
`self.main_window.default_parameters.data` is read without a lock while the UI thread can mutate it (e.g. a slider change). In single-frame preview mode this is the fallback parameter source, so a torn read can apply partially-updated parameters to a face.

**Fix:**
Use the same acquire-and-copy pattern as used elsewhere. Snapshot `default_parameters.data` to a local dict under `self.lock` before entering the worker function.

---

#### Bugs

---

**ID:** FW-BUG-01
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_standard`

**Issue:**
`kpss[i]` is indexed without a bounds check after the tracker code path. `kpss` and `kpss_5` can have different lengths (the tracker may return fewer tracked landmarks than detected bboxes), causing an `IndexError` at runtime.

**Fix:**
```python
kps_all_i = kpss[i] if kpss is not None and i < len(kpss) else None
```

---

**ID:** FW-BUG-02
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `get_swapped_and_prev_face`

**Issue:**
The DFM branch tensor layout contract (CHW vs HWC) is fragile and undocumented. If `dfm_model.convert()` returns a CHW tensor when HWC is expected, the `permute` at the line that converts the output corrupts spatial dimensions silently without any assertion or error — the result is a visually scrambled face with no warning.

**Fix:**
Document the contract explicitly with a comment and add an assertion after the DFM call:
```python
assert dfm_output.ndim == 3 and dfm_output.shape[2] == 3, \
    f"DFM model must return HWC RGB tensor, got shape {dfm_output.shape}"
```

---

**ID:** FW-BUG-03
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
When `calc_inswapper_latent` returns `None` (e.g. after the FW-ROBUST-03 fix is applied), `input_face_affined` becomes `None`. The next call to `get_swapped_and_prev_face` immediately crashes at the first `.permute()` call because it cannot operate on `None`.

**Fix:**
Add a None guard immediately after `get_affined_face_dim_and_swapping_latents`:
```python
if input_face_affined is None:
    swap = original_face_512
    # skip to mask section — nothing to swap
```

---

**ID:** FW-BUG-04
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
`v2.functional.pad(swap, (0, 0, img.shape[2]-512, img.shape[1]-512))` produces negative padding values when the source image is smaller than 512 pixels in either dimension. `torchvision` raises a `ValueError` for negative padding, crashing the frame.

**Fix:**
```python
pad_w = max(0, img.shape[2] - 512)
pad_h = max(0, img.shape[1] - 512)
swap = v2.functional.pad(swap, (0, 0, pad_w, pad_h))
```

---

**ID:** FW-BUG-05
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `get_swapped_and_prev_face`

**Issue:**
`dfm_model.convert(original_face_512)` receives a CHW uint8 tensor in the [0, 255] range, but DFM models universally expect an HWC float32 tensor in [0.0, 1.0]. No conversion is performed before the call, so the model processes garbage-scaled data, producing incorrect output.

**Fix:**
```python
dfm_input = original_face_512.permute(1, 2, 0).float() / 255.0
dfm_output = dfm_model.convert(dfm_input)
```

---

**ID:** FW-BUG-06
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_standard`

**Issue:**
An inline comment says "downscale" but the code block actually upscales small images. This causes developer confusion and incorrect reasoning about the code path when debugging resolution issues.

**Fix:**
Replace the comment with:
```python
# Upscale small frames so the shorter side is at least 512px before detection
```

---

**ID:** FW-BUG-07
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
`isinstance(kpss_crop, np.ndarray)` is always `False` because `kpss_crop` is a Python `list`, not an `ndarray`. This means `kps_all_on_crop` is always `None`, silently disabling dense-landmark makeup editing in VR mode without any error or warning.

**Fix:**
```python
if kpss_crop:
    kps_all_on_crop = kpss_crop[0]
else:
    kps_all_on_crop = None
```

---

**ID:** FW-BUG-08
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `get_swapped_and_prev_face` (SimSwap512 branch)

**Issue:**
`swapper_output.sum() < 1.0` is used as a failure heuristic to detect a zeroed-out swapper output, but a valid dark face can also produce a very small sum and incorrectly trigger the fallback, discarding a valid swap result.

**Fix:**
Use a more reliable near-zero check:
```python
if swapper_output.abs().max() < 1e-4:
    # treat as failed swap
```

---

**ID:** FW-BUG-09
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`, `_resolve_landmarks_to_draw`, `get_compare_faces_image`

**Issue:**
`_find_best_target_match` is called independently three times per face per frame — once in the swap loop, once in `_resolve_landmarks_to_draw`, and once in `get_compare_faces_image`. If `target_faces` is mutated between calls (see FW-RACE-01), the three calls can return different results for the same face, causing the overlay and compare modes to show a different target than was actually used for the swap.

**Fix:**
Store the matched target face in the `fface` dict during the swap loop:
```python
fface['matched_target'] = best_match
```
Reuse `fface['matched_target']` in `_resolve_landmarks_to_draw` and `get_compare_faces_image` instead of calling `_find_best_target_match` again.

---

**ID:** FW-BUG-10
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
`ceil(StrengthAmountSlider / 100.0)` produces a discontinuous step function. Moving the slider from 100 to 101 causes `ceil(1.00) == 1` to jump to `ceil(1.01) == 2`, doubling the number of iterations. Users experience an abrupt quality jump with no smooth intermediate values.

**Fix:**
```python
iterations = max(1, round(StrengthAmountSlider / 100.0))
```

---

**ID:** FW-BUG-11
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `get_swapped_and_prev_face` (GhostFace branch)

**Issue:**
The zero-output heuristic for GhostFace uses `swapper_output.sum()` but GhostFace outputs are in the `[-1, 1]` range, so positive and negative values cancel. A valid face output can sum to near zero and trigger the fallback incorrectly.

**Fix:**
```python
if swapper_output.abs().mean() < 0.01:
    # treat as failed swap
```

---

**ID:** FW-BUG-12
**Category:** Bug
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `get_border_mask`

**Issue:**
No validation is performed on the slider values passed to `get_border_mask`. Out-of-range values (e.g. `left > right` or `top > bottom` or values outside `[0, 128]`) produce geometrically invalid masks without any error.

**Fix:**
Add input validation at the start of the function:
```python
assert 0 <= left <= right <= 128, f"Border mask left/right out of range: {left}, {right}"
assert 0 <= top <= bottom <= 128, f"Border mask top/bottom out of range: {top}, {bottom}"
```

---

**ID:** FW-BUG-13
**Category:** Bug
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `apply_block_shift_gpu_jitter`

**Issue:**
`B = int(2**block_size)` is exponential. A slider value of `8` produces `256`-pixel blocks, `10` produces `1024`-pixel blocks. This is almost certainly not the intended behavior; block sizes grow far faster than the user expects.

**Fix:**
Either use the slider value directly as the block size in pixels:
```python
B = max(1, int(block_size))
```
Or rename the parameter to `block_size_exponent` throughout the UI and code to make the exponential behavior explicit.

---

**ID:** FW-BUG-14
**Category:** Bug
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
The local variable `swap2` is reused with different semantics in two separate blocks — once in the JPEG compression artifact simulation block and once in the BlockShift block. This makes the code confusing to read and creates a latent bug risk if the blocks are ever reordered.

**Fix:**
Use distinct names:
```python
swap_jpeg = ...      # in the JPEG compression block
swap_blockshift = ... # in the BlockShift block
```

---

#### Performance

---

**ID:** FW-PERF-01
**Category:** Performance
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_find_best_target_match`

**Issue:**
In `SwapOnlyBestMatch` mode, `_find_best_target_match` is O(F×T²) — it iterates all detected faces for each target face. Additionally it is called three times per detected face per frame (swap loop, landmark overlay, compare mode), multiplying the cost by 3.

**Fix:**
Cache the match result in the `fface` dict during the primary swap loop (see FW-BUG-09). The overlay and compare mode functions should read from `fface['matched_target']` instead of calling `_find_best_target_match` again.

---

**ID:** FW-PERF-02
**Category:** Performance
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_resolve_landmarks_to_draw`

**Issue:**
`_find_best_target_match` is called again for every detected face to determine which target face's landmarks to draw, even though the result was already computed during the swap loop.

**Fix:**
Resolved by FW-PERF-01 / FW-BUG-09: read `fface['matched_target']` that was stored during the swap loop.

---

**ID:** FW-PERF-03
**Category:** Performance
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `get_compare_faces_image`

**Issue:**
`get_compare_faces_image` calls `_find_best_target_match` a third time AND calls `enhance_core()` per face individually. For a 6-face scene with compare mode enabled, this means 18 total redundant match calls plus 6 separate enhancement passes per frame.

**Fix:**
Cache the match result (FW-BUG-09). Skip `enhance_core()` in compare mode — the compare image is a diagnostic view, not output, so enhancement is unnecessary and expensive.

---

**ID:** FW-PERF-04
**Category:** Performance
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `face_restorer_auto`, `sharpness_score`

**Issue:**
Three fixed-size kernel tensors (`lap_k`, `sobel_x`, `sobel_y`) are allocated as new `torch.tensor(...)` objects on every call. These functions are called up to 17 times per face per frame by the auto-restore search loop, creating up to 51 tensor allocations per face per frame.

**Fix:**
Promote the kernels to class-level constants or create them once in `__init__` as instance attributes:
```python
# In __init__:
self._lap_kernel = torch.tensor([[0,1,0],[1,-4,1],[0,1,0]], dtype=torch.float32, device=self.device)
self._sobel_x = torch.tensor([[-1,0,1],[-2,0,2],[-1,0,1]], dtype=torch.float32, device=self.device)
self._sobel_y = torch.tensor([[1,2,1],[0,0,0],[-1,-2,-1]], dtype=torch.float32, device=self.device)
```

---

**ID:** FW-PERF-05
**Category:** Performance
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `sharpness_map`

**Issue:**
`sharpness_map` independently allocates the same Laplacian and Sobel kernels as `sharpness_score` (FW-PERF-04), duplicating the allocation cost. Both functions run a separate convolution pass, but could share a single pass.

**Fix:**
Deduplicate kernel allocation by sharing the cached kernels from FW-PERF-04. Merge `sharpness_score` and `sharpness_map` to share a single `F.conv2d` pass, returning both the score and the map from one call.

---

**ID:** FW-PERF-06
**Category:** Performance
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `apply_gabor_filter_torch`

**Issue:**
`kernels.repeat_interleave(C, dim=0)` is called every invocation to expand the Gabor kernel bank to match the channel count `C` of the input. This large tensor operation is repeated even when `C` has not changed since the last call.

**Fix:**
Cache the expanded weight tensor keyed by `(*kernel_shape, C)`:
```python
cache_key = (*kernels.shape, C)
if cache_key not in self._gabor_kernels_cache:
    self._gabor_kernels_cache[cache_key] = kernels.repeat_interleave(C, dim=0)
expanded = self._gabor_kernels_cache[cache_key]
```

---

**ID:** FW-PERF-07
**Category:** Performance
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `process_frame`

**Issue:**
`set_scaling_transforms(control)` rebuilds 12 `torchvision` transform objects every frame, even when the interpolation-related control values have not changed since the last frame. Transform construction is not free — it involves object allocation and parameter validation.

**Fix:**
Add a dirty-flag: store the last-seen values of the relevant control keys and only call `set_scaling_transforms` when they change:
```python
if self._last_scaling_control != current_scaling_keys:
    set_scaling_transforms(control)
    self._last_scaling_control = current_scaling_keys
```

---

**ID:** FW-PERF-08
**Category:** Performance
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_standard`

**Issue:**
`v2.Resize(...)` objects are constructed inline every frame when a scale-up or scale-down operation is needed. Even at a fixed resolution, a new `Resize` object is created each frame.

**Fix:**
Cache the most recently constructed `Resize` by its `(h, w, antialias)` key:
```python
resize_key = (target_h, target_w, antialias)
if resize_key not in self._resize_cache:
    self._resize_cache[resize_key] = v2.Resize((target_h, target_w), antialias=antialias)
resizer = self._resize_cache[resize_key]
```

---

**ID:** FW-PERF-09
**Category:** Performance
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
`get_border_mask(parameters)` is called unconditionally on every face even when `BordermaskEnableToggle` is `False`. Mask generation involves tensor allocation and arithmetic on `[1,512,512]` tensors.

**Fix:**
```python
if parameters.get('BordermaskEnableToggle'):
    border_mask = get_border_mask(parameters)
else:
    border_mask = None
```
Guard all uses of `border_mask` with a None check.

---

**ID:** FW-PERF-10
**Category:** Performance
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `face_restorer_auto`

**Issue:**
The blur-search loop inside `face_restorer_auto` creates up to 10 `transforms.GaussianBlur(...)` objects inside the loop body per face per frame. `GaussianBlur` construction includes kernel precomputation.

**Fix:**
Precompute the list of `GaussianBlur` objects before the loop:
```python
blur_kernels = [transforms.GaussianBlur(k) for k in range(3, 23, 2)]
for blur in blur_kernels:
    ...
```

---

**ID:** FW-PERF-11
**Category:** Performance
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
Multiple `.clone()` calls on ~3 MB GPU tensors are performed as "before" snapshots, some of which are used only when a restoration or rollback path is actually taken. Every frame pays the clone cost regardless.

**Fix:**
Use lazy cloning — only clone when the downstream path is confirmed to be taken:
```python
if needs_restore:
    swap_before = swap.clone()
```

---

**ID:** FW-PERF-12
**Category:** Performance
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
`PerspectiveConverter` is instantiated even when no faces are detected in the VR crop. The constructor does non-trivial initialization work that is wasted when no processing occurs.

**Fix:**
```python
if not bboxes_crop:
    continue  # skip converter instantiation entirely
persp_converter = PerspectiveConverter(...)
```

---

**ID:** FW-PERF-13
**Category:** Performance
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `get_swapped_and_prev_face`

**Issue:**
`torch.cuda.synchronize()` is called before inference calls, not after. This forces the CPU to wait for all previously queued GPU work to complete before submitting the next kernel. Moving the sync before the call provides no benefit; it should follow the call if synchronization is needed for timing.

**Fix:**
Move `torch.cuda.synchronize()` to immediately after the inference call, or remove it entirely from the hot path (synchronization is implicit at tensor-to-CPU transfers).

---

**ID:** FW-PERF-14
**Category:** Performance
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `analyze_image`

**Issue:**
Heavy FFT and pooling operations run on every frame when `AnalyseImageEnableToggle` is `True`, even when `debug` is `False`. In that case the computed results are immediately discarded.

**Fix:**
```python
if debug and AnalyseImageEnableToggle:
    result = _run_image_analysis(img)
    debug_info['JS: '] = result
```

---

#### Memory

---

**ID:** FW-MEM-01
**Category:** Memory
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `get_gabor_kernels`

**Issue:**
`_gabor_kernels_cache` is an unbounded dict. Each unique slider position creates a new cache entry containing GPU tensors. Continuous slider dragging creates a monotonically growing GPU tensor cache that is never evicted.

**Fix:**
Use an `OrderedDict` with a maximum size:
```python
from collections import OrderedDict
MAX_GABOR_CACHE = 32

if len(self._gabor_kernels_cache) >= MAX_GABOR_CACHE:
    self._gabor_kernels_cache.popitem(last=False)  # evict oldest
```

---

**ID:** FW-MEM-02
**Category:** Memory
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
Processed VR crop tensors are accumulated in `processed_perspective_crops_details` until all stitching is complete. For frames with many detected faces across both eyes, this can hold several large GPU tensors simultaneously when it is safe to release each one immediately after its stitch is complete.

**Fix:**
```python
stitch_single_perspective(eye_side, crop_data, ...)
del processed_perspective_crops_details[eye_side]  # release immediately after stitch
```

---

**ID:** FW-MEM-03
**Category:** Memory
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
Eight `[1,512,512]` tensors (~8 MB total) are allocated per face per frame for mask and diff variables regardless of whether the corresponding features (border mask, diff, texture transfer, etc.) are enabled. For a 4-face scene at 30fps, this is 960 MB/s of unnecessary allocation/deallocation pressure.

**Fix:**
Initialize all mask and diff tensors lazily behind their respective feature toggles:
```python
border_mask = get_border_mask(params) if params.get('BordermaskEnableToggle') else None
diff_mask = compute_diff(swap, orig) if params.get('DiffEnableToggle') else None
```

---

#### Robustness

---

**ID:** FW-ROBUST-01
**Category:** Robustness
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_standard`

**Issue:**
Duplicate of FW-BUG-01. `kpss[i]` is accessed without a bounds check after the tracker path, where `kpss` and `kpss_5` can have different lengths.

**Fix:**
See FW-BUG-01.

---

**ID:** FW-ROBUST-02
**Category:** Robustness
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
`tform.inverse` is used to compute the inverse affine transform without checking whether `tform.estimate()` returned `True`. When keypoints are degenerate (collinear, identical, or near-identical), `estimate()` can fail and return `False` while silently leaving `tform` as an identity matrix. This places the swapped face at the top-left corner of the frame without any error.

**Fix:**
```python
success = tform.estimate(src_pts, dst_pts)
if not success:
    logger.warning("Affine estimation failed for face %s — skipping swap", face_id)
    continue
```

---

**ID:** FW-ROBUST-03
**Category:** Robustness
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `get_affined_face_dim_and_swapping_latents`

**Issue:**
`calc_swapper_latent_*` functions for InStyleSwapper, SimSwap512, GhostFace, and CSCS can all return `None` on failure, but no `None` guard exists for these four models. Only Inswapper128 has a None guard, leaving the other four models able to propagate `None` silently into `swap_core` and crash at the first tensor operation.

**Fix:**
Apply a uniform None guard for all models:
```python
latent = calc_swapper_latent_for_model(face, model)
if latent is None:
    logger.warning("calc_swapper_latent returned None for model %s", model_name)
    return None, None
```

---

**ID:** FW-ROBUST-04
**Category:** Robustness
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_standard`

**Issue:**
`self.parameters[target_face.face_id]` raises a `KeyError` if a face card was added to `target_faces` after the snapshot was taken but before `self.parameters` was populated for that face ID. This can happen during live processing when the user adds a new face mid-stream.

**Fix:**
```python
params = self.parameters.get(face_id, self.main_window.default_parameters.data)
```

---

**ID:** FW-ROBUST-05
**Category:** Robustness
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `process_and_emit_task`

**Issue:**
`self.local_control_state_from_feeder` is not initialized in `__init__`. If `process_and_emit_task` is ever called before `run()` completes its setup (e.g. during a rapid start/stop cycle), the attribute access raises `AttributeError`.

**Fix:**
Add to `__init__`:
```python
self.local_control_state_from_feeder = {}
```

---

**ID:** FW-ROBUST-06
**Category:** Robustness
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
The `kps` parameter is typed as `np.ndarray | bool = False`. The guard `kps.size == 0` correctly handles the empty-array case, but `bool.size` is `1` (Python's `bool` inherits `__sizeof__` from `int`), so a `False` value passes the `.size == 0` guard and reaches code that expects an ndarray.

**Fix:**
Change the default and type annotation to use `None`:
```python
def swap_core(self, ..., kps: np.ndarray | None = None, ...):
    if kps is None or kps.size == 0:
        ...
```

---

**ID:** FW-ROBUST-07
**Category:** Robustness
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
When only a single face is detected in the equirectangular detection pass, the detector may return `bboxes_eq_np` with shape `(5,)` instead of `(1, 5)`. The `bboxes_eq_np.ndim == 2` check passes as `False`, but the single-detection case is never handled, so it is silently skipped.

**Fix:**
```python
if bboxes_eq_np.ndim == 1 and bboxes_eq_np.shape[0] in (4, 5):
    bboxes_eq_np = bboxes_eq_np.reshape(1, -1)
```

---

**ID:** FW-ROBUST-08
**Category:** Robustness
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
Duplicate of FW-BUG-04. Negative padding when image is smaller than 512.

**Fix:**
See FW-BUG-04.

---

**ID:** FW-ROBUST-09
**Category:** Robustness
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `sharpness_map`

**Issue:**
The `alpha_map_blur` kernel size derived from the slider is used directly in `GaussianBlur`. If the slider produces an even value, `GaussianBlur` raises a `ValueError` (kernel size must be odd), but the code silently falls back to 0 instead of the next valid odd number.

**Fix:**
```python
if alpha_map_blur % 2 == 0:
    alpha_map_blur += 1
alpha_map_blur = max(3, alpha_map_blur)
```

---

**ID:** FW-ROBUST-10
**Category:** Robustness
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
`best_target_button_vr.calculate_assigned_input_embedding()` is called from within the worker thread. This method writes to shared attributes on the face button object without any lock, which can corrupt the embedding data if another thread (or the UI) also calls it concurrently.

**Fix:**
Either call this method only from the UI thread (dispatching via `QMetaObject.invokeMethod`) or add a per-face-button lock around the call and within the method.

---

**ID:** FW-ROBUST-11
**Category:** Robustness
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `get_face_similarity_tform`

**Issue:**
The return value of `tform.estimate()` is discarded silently. If estimation fails (degenerate input), the resulting `tform` is an identity matrix, and the subsequent `tform.inverse` silently returns an identity, placing landmarks at wrong positions without any diagnostic.

**Fix:**
```python
if not tform.estimate(src_pts, dst_pts):
    raise ValueError(f"Similarity transform estimation failed for face {face_id}")
```

---

**ID:** FW-ROBUST-12
**Category:** Robustness
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_standard`

**Issue:**
In `SwapOnlyBestMatch` inner loop, `target_faces.items()` is iterated live (not from the snapshot taken at the top of the function). If the UI adds or removes a face card during this inner loop, a `RuntimeError: dictionary changed size during iteration` is raised.

**Fix:**
Use the snapshotted copy (from FW-RACE-01 fix) consistently in all inner loops.

---

#### Code Quality

---

**ID:** FW-QUAL-01
**Category:** Code Quality
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
A Restoration-2 block of approximately 60 lines is duplicated verbatim in two separate positions within `swap_core` ("before-end" position and "end" position). This creates a maintenance burden: any bug fix or improvement to the restoration logic must be applied twice.

**Fix:**
Extract a helper function:
```python
def _apply_restorer_with_auto(self, swap, original, restored, params, slot_id):
    ...
```
Call it from both positions with the appropriate arguments.

---

**ID:** FW-QUAL-02
**Category:** Code Quality
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
`debug_info["Restore2"]` is set in both of the duplicated Restoration-2 blocks. The second assignment silently overwrites the first, meaning only the last-applied restorer's debug info is visible in the debug overlay.

**Fix:**
Resolved by FW-QUAL-01. With a shared helper, the key should be parameterized: `debug_info[f"Restore2_{position}"]`.

---

**ID:** FW-QUAL-03
**Category:** Code Quality
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
A large dead-code block at lines 2794–2804 is wrapped in triple-quoted strings (`"""..."""`) used as multi-line comments. These are evaluated at runtime as discarded string literals, incurring a minor parsing cost and making the code appear to have complex string logic that it does not.

**Fix:**
Convert to `#`-prefixed comment lines, or remove the block entirely if it is no longer needed.

---

**ID:** FW-QUAL-04
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
`restore_mask` is initialized early in the function but is immediately and unconditionally overwritten at lines 2492, 2603, and 3027. The early initialization has no effect and adds confusion about where the actual value originates.

**Fix:**
Remove the early initialization and let `restore_mask` be assigned at first use.

---

**ID:** FW-QUAL-05
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `__init__`

**Issue:**
`self.lock = threading.Lock()` is declared in `__init__` but never used anywhere in the class. It exists as dead code.

**Fix:**
Wire it up to guard the writes identified in FW-RACE-03 (and FW-RACE-01 snapshot), or remove it if a different locking strategy is used.

---

**ID:** FW-QUAL-06
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `get_swapped_and_prev_face`

**Issue:**
`for k in range(itex):` uses the loop variable `k` but never references it inside the loop body. This is a convention violation (unused loop variables should be named `_`).

**Fix:**
```python
for _ in range(itex):
    ...
```

---

**ID:** FW-QUAL-07
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
`debug_info["JS: "] = image_analyse_swap` stores a dict as a debug value. The debug overlay prints it as `repr(dict)`, producing an unreadable one-liner in the overlay text.

**Fix:**
Flatten the inner dict keys into `debug_info` individually:
```python
for k, v in image_analyse_swap.items():
    debug_info[f"JS:{k}"] = v
```

---

**ID:** FW-QUAL-08
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `get_swapped_and_prev_face`

**Issue:**
When all tiling passes fail and the output tensor remains all-zeros, a silent black face is returned with no warning. Downstream, the face blends in seamlessly as a pure black square with no indication that anything went wrong.

**Fix:**
```python
if output.abs().max() < 1.0:
    logger.warning("[WARN] All tiles failed for face %s — output is all-zero", face_id)
```

---

**ID:** FW-QUAL-09
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `get_affined_face_dim_and_swapping_latents`

**Issue:**
`apply_likeness_with_norm_preservation` is defined as an inner function inside `get_affined_face_dim_and_swapping_latents`, meaning a new function object is created on every call to the outer function.

**Fix:**
Promote to a `@staticmethod` on the class, or to a module-level helper function.

---

**ID:** FW-QUAL-10
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `get_face_similarity_tform`, `get_swapped_and_prev_face`

**Issue:**
GhostFace version comparisons are expressed as chained `!=`/`==` string comparisons spread across multiple locations: `model_name != 'GhostFace-v1' and model_name != 'GhostFace-v2'`, etc. Adding a new GhostFace version requires finding and updating every occurrence.

**Fix:**
Define a module-level constant:
```python
GHOSTFACE_MODELS = frozenset({'GhostFace-v1', 'GhostFace-v2', 'GhostFace-v3'})
```
Use `model_name in GHOSTFACE_MODELS` / `model_name not in GHOSTFACE_MODELS` throughout.

---

**ID:** FW-QUAL-11
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_standard`

**Issue:**
Variables `img_x` and `img_y` are used for image width and height respectively. In the context of a CHW (channels-first) PyTorch tensor, `x` and `y` are ambiguous and counterintuitive dimension labels.

**Fix:**
Rename throughout the function:
```python
img_w = img.shape[2]   # was img_x
img_h = img.shape[1]   # was img_y
```

---

**ID:** FW-QUAL-12
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `swap_core`

**Issue:**
Auto-color transfer and `EndingColorTransfer` operate on different mask states — one runs before `FaceParser` is applied and one after. The inconsistency is not documented and makes it difficult to reason about which color transfer applies to which mask state.

**Fix:**
Add an explicit comment block explaining why each color transfer operates at its respective pipeline position, and document whether the pre-parser or post-parser mask is intentional for each case.

---

**ID:** FW-QUAL-13
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `_apply_denoiser_pass`

**Issue:**
Denoiser pass names are constructed by string concatenation with a `pass_suffix` argument, creating an undocumented convention that is fragile — any caller that passes an unexpected suffix string silently creates a new unrecognized pass type.

**Fix:**
Define an `Enum` for pass types:
```python
from enum import Enum

class DenoiserPass(Enum):
    PRE_SWAP = "pre_swap"
    POST_SWAP = "post_swap"
    POST_RESTORE = "post_restore"
```
Use `DenoiserPass` values as the argument type.

---

### 4.2 VR180 Processing

---

**ID:** VR-01
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
When only one face is detected in the equirectangular image, some detectors return `bboxes_eq_np` with shape `(4,)` or `(5,)` instead of `(1, 4)` or `(1, 5)`. The loop `for bbox_eq_single in bboxes_eq_np` then iterates over individual scalar values instead of bbox rows. This causes `calculate_theta_phi_from_bbox` to receive a scalar instead of a 4-element array, crashing the VR pipeline.

**Fix:**
After the array is obtained, normalize its shape:
```python
if bboxes_eq_np.ndim == 1 and bboxes_eq_np.shape[0] in (4, 5):
    bboxes_eq_np = bboxes_eq_np.reshape(1, -1)
if bboxes_eq_np.shape[0] == 0:
    return original_equirect_tensor_for_vr  # no faces detected
```

---

**ID:** VR-02
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
The field-of-view for perspective crops is derived from equirectangular pixel extents using a linear mapping. This is geometrically incorrect because equirectangular projections are not linear — pixels near the poles represent a much narrower actual angular span than pixels at the equator. The error factor is `1/cos(latitude)`, meaning a face near the top or bottom of a VR frame gets a crop that is up to several times too large.

**Fix:**
Compute the face center latitude (phi) from the bbox center coordinates, then divide the angular width by `cos(phi)`:
```python
phi_radians = math.radians(phi_center_deg)
corrected_angular_width = angular_width_deg / max(0.1, math.cos(phi_radians))
fov_deg = min(corrected_angular_width * VR_FOV_SCALE_FACTOR, 120.0)
```

---

**ID:** VR-03
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
The custom NMS implementation uses the width of the suppressor box as the sole distance threshold when deciding whether to suppress a candidate detection. This is asymmetric — a small face can fail to suppress a large face near it, while a large face always suppresses smaller nearby faces regardless of overlap.

**Fix:**
Replace with IoU-based NMS using a threshold of 0.5, which is symmetric and scale-invariant:
```python
keep = torchvision.ops.nms(boxes_tensor, scores_tensor, iou_threshold=0.5)
```
If IoU NMS is unavailable, use `max(widths[idx1], widths[j]) * 0.5` as a symmetric distance threshold.

---

**ID:** VR-04
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
Duplicate of FW-BUG-07. `isinstance(kpss_crop, np.ndarray)` is always `False` because `kpss_crop` is a Python list, silently disabling dense-landmark makeup editing in VR mode.

**Fix:**
See FW-BUG-07.

---

**ID:** VR-05
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
`EquirectangularConverter` and `PerspectiveConverter` both receive `img_numpy_rgb_uint8` (a CPU NumPy array) which triggers a CPU-to-GPU transfer of the full frame. However `original_equirect_tensor_for_vr` is already a GPU tensor. The CPU array is only kept for this purpose.

**Fix:**
Modify both converter constructors to accept a GPU tensor directly:
```python
equirect_converter = EquirectangularConverter(original_equirect_tensor_for_vr)
```
This eliminates a full-frame PCIe round-trip on every VR processing call.

---

**ID:** VR-06
**Category:** Bug (corrected classification: Performance)
**Severity:** MED
**File:** `app/processors/frame_worker.py` / `Equirec2Perspec_vr`
**Function:** `GetPerspective`

**Issue:**
`_persp_cache` is an instance variable on `EquirectangularConverter`. Since `EquirectangularConverter` is reconstructed fresh every frame, the cache is destroyed at the end of each frame and provides zero cross-frame benefit. The cache math is correct (the grid is view-direction independent and reusable), but it is thrown away before it can be reused.

**Fix:**
See VR-10 (promote cache to class-level or module-level dict).

---

**ID:** VR-07
**Category:** Bug
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
Stitching crop results are stored in a dict keyed by `f"{eye_side}_{theta}_{phi}"`. Two faces at very similar angular positions can produce identical float-formatted theta/phi strings and collide, silently discarding one face's processed crop.

**Fix:**
Replace the dict with a list of tuples:
```python
perspective_crops = []  # list of (eye_side, theta, phi, crop_data) tuples
```

---

**ID:** VR-08
**Category:** Performance
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
Both `EquirectangularConverter` and `PerspectiveConverter` are reconstructed fresh on every frame. Constructor initialization includes non-trivial setup and (via VR-05) a full PCIe transfer of the 4K equirectangular frame. At 30fps with a 4K frame, this wastes approximately 50 MB/s of PCIe bandwidth on redundant re-uploads.

**Fix:**
Cache both converters at the `FrameWorker` level and invalidate only when the input resolution changes:
```python
if self._vr_converter is None or self._vr_frame_size != current_frame_size:
    self._vr_converter = EquirectangularConverter(...)
    self._vr_frame_size = current_frame_size
```

---

**ID:** VR-09
**Category:** Performance
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
The initial equirectangular face detection uses `input_size=(512, 512)`. VR180/VR360 source images have a 2:1 aspect ratio. A square input crops or letterboxes half the vertical content, reducing detection coverage of the frame significantly.

**Fix:**
Use an aspect-ratio-aware input size:
```python
# For 2:1 equirectangular content:
input_size = (1024, 512)
```
Verify the detector supports non-square input; if not, tile the equirectangular horizontally.

---

**ID:** VR-10
**Category:** Performance
**Severity:** MED
**File:** `Equirec2Perspec_vr`
**Function:** `GetPerspective`

**Issue:**
`_persp_cache` is an instance variable and is destroyed when the `EquirectangularConverter` instance is destroyed at end of frame (see VR-06). The cached sampling grids (which are view-direction-independent and expensive to compute) are never reused across frames.

**Fix:**
Promote the cache to a module-level or class-level dict:
```python
_PERSP_GRID_CACHE: dict = {}  # module level

cache_key = (str(device), FOV, height, width, THETA, PHI)
if cache_key not in _PERSP_GRID_CACHE:
    _PERSP_GRID_CACHE[cache_key] = _compute_sampling_grid(...)
grid = _PERSP_GRID_CACHE[cache_key]
```
Consider bounding the cache size with an `OrderedDict` (max 256 entries) to prevent unbounded growth (see also FW-MEM-01).

---

**ID:** VR-11
**Category:** Code Quality
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
`rotation_angles=[0, 90, 180, 270]` is passed to the equirectangular detector when `AutoRotationToggle` is enabled. Rotating an equirectangular image at 90° or 270° produces geometrically invalid bboxes because the spherical coordinate mapping is not rotation-symmetric in pixel space.

**Fix:**
Force `rotation_angles=[0]` in VR mode regardless of `AutoRotationToggle`:
```python
vr_rotation_angles = [0]  # non-zero angles produce invalid spherical coords
```
Add a comment explaining why rotation is disabled in VR mode.

---

**ID:** VR-12
**Category:** Code Quality
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `_process_single_vr_perspective_crop_multi`

**Issue:**
`swap_core` is called with a 512×512 perspective crop as both the processing target and the coordinate frame. When `frame == template size == 512`, the affine transform calibration may produce an off-centre result. This constraint is undocumented and untested.

**Fix:**
Add an assertion at the entry of the function:
```python
assert crop_tensor.shape[-2:] == (512, 512), \
    f"VR perspective crop must be 512x512, got {crop_tensor.shape}"
```
Document why 512×512 is required and verify the transform math produces centred results at this exact size.

---

**ID:** VR-13
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
`VR_DYNAMIC_FOV_PADDING_FACTOR = 1.0` means no padding is applied to the crop FOV. The constant name says "padding" but the effective behaviour is no padding, causing faces to be tightly clipped at the edges of perspective crops. The default value and name are both misleading.

**Fix:**
Rename to `VR_FOV_SCALE_FACTOR` and set the default to `1.5` to provide comfortable padding around detected faces:
```python
VR_FOV_SCALE_FACTOR = 1.5  # scale factor applied to detected face angular extent
```
Expose as a UI parameter in the VR settings section.

---

**ID:** VR-14
**Category:** Robustness
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `stitch_single_perspective`, `_apply_feathering`

**Issue:**
A 25×25 erosion kernel is applied unconditionally to the reprojected face mask before feathering. For small faces (e.g. distant or low-resolution detections), the erosion completely removes the mask content, causing the crop to be silently discarded from stitching with no warning.

**Fix:**
Clamp the erosion kernel size to a fraction of the mask's spatial extent:
```python
max_erosion = min(mask_h, mask_w) // 8
erosion_k = min(25, max_erosion)
erosion_k = max(3, erosion_k | 1)  # ensure odd and at least 3
```
After erosion, check that the mask is non-empty before blending:
```python
if feathered_mask.max() < 1e-4:
    logger.debug("VR stitch: feathered mask is empty after erosion — skipping crop")
    return equirect_tensor  # unchanged
```

---

**ID:** VR-15
**Category:** Robustness
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `_process_frame_vr180`

**Issue:**
The VR stitching loop does not check `stop_event` during iteration. If the user cancels processing, partial stitching continues for all remaining crops before the cancellation is honoured, wasting GPU time.

**Fix:**
```python
for crop_key, crop_data in processed_perspective_crops_details.items():
    if stop_event is not None and stop_event.is_set():
        break
    stitch_single_perspective(...)
```

---

**ID:** VR-16
**Category:** Bug
**Severity:** MED
**File:** `Equirec2Perspec_vr`
**Function:** `GetPerspective`

**Issue:**
`grid_sample` is called with `padding_mode='border'` on the equirectangular image sampling grid. At the 0°/360° longitude seam (`THETA ≈ ±180°`), `padding_mode='border'` replaces out-of-bounds sample coordinates with the colour of the border pixel instead of wrapping around. This produces a visible monochrome vertical band artifact for any face near the left or right edge of the equirectangular frame.

**Fix:**
Wrap the out-of-bounds `grid_x` values before sampling:
```python
# Wrap grid_x from [-1,1] to handle the 0/360 seam
grid_x = grid_x % 2.0 - 1.0  # maps out-of-range values to their wrapped equivalents
```
Or tile the equirectangular image horizontally by one frame width on each side before sampling, then use `padding_mode='zeros'`.

---

### 4.3 ByteTrack Face Tracking

---

**ID:** BT-01
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py` (ByteTracker integration)
**Function:** `_calculate_iou`

**Issue:**
When a Kalman filter prediction produces a degenerate bounding box (zero width or zero height), the union area `boxAArea + boxBArea - interArea` becomes zero or negative, causing a division-by-zero exception. This exception propagates uncaught and kills the processing thread.

**Fix:**
```python
def _calculate_iou(boxA, boxB):
    ...
    denominator = boxAArea + boxBArea - interArea
    if denominator <= 0:
        return 0.0
    return interArea / denominator
```

---

**ID:** BT-02
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect`

**Issue:**
`det_scores` from YOLO and YuNet detectors may be returned with shape `(N, 1)` instead of `(N,)`. When this shape is used in NumPy operations inside `_refine_landmarks` (e.g. boolean indexing, comparison operators), subtle broadcast errors occur that produce incorrect or empty landmark sets without raising an exception.

**Fix:**
Ensure a flat score array at the point of return from `_filter_detections_gpu`:
```python
det_scores = det_scores.flatten()  # guarantee shape (N,)
```

---

**ID:** BT-03
**Category:** Bug
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect`

**Issue:**
`img_info` and `img_size` are both set to `img_hw` (the same tuple). The intent is `img_info = original_input_size` and `img_size = model_input_size`. When they are equal, `scale = 1.0` coincidentally produces correct results. If the model input size ever differs from the frame size, the in-place `bboxes /= scale` operation in ByteTracker will mutate the tracker input array incorrectly.

**Fix:**
Document the intentional same-size usage with a comment. Use non-in-place division to avoid the in-place mutation risk:
```python
bboxes = bboxes / scale  # non-in-place: safe even when used after ByteTracker
```

---

**ID:** BT-04
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect`

**Issue:**
Coasted tracks (Kalman-predicted positions with no matching raw detection in the current frame) are identified by `match_idx == -1` but this path does nothing — coasted tracks are silently dropped from the output. ByteTrack's core value for handling brief occlusions is completely negated.

**Fix:**
For coasted tracks, output the Kalman-predicted bbox with the most recent available landmarks:
```python
if match_idx == -1:
    # Use Kalman-predicted position with last known landmarks
    predicted_bbox = strack.tlbr  # Kalman prediction
    last_kps = track_history.get(strack.track_id, {}).get('kps', None)
    if last_kps is not None:
        output_tracks.append((predicted_bbox, last_kps, strack.score))
```

---

**ID:** BT-05
**Category:** Bug
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect`

**Issue:**
When ByteTrack is enabled, `effective_score` is hardcoded to `0.3` for all detections, ignoring the user's `DetectorScoreSlider` setting. This value is also below ByteTracker's own `track_thresh=0.4`, causing low-confidence detections to be classified as "low confidence new tracks" and increasing false-positive track creation.

**Fix:**
```python
user_score = control.get('DetectorScoreSlider', 0.5)
effective_score = min(user_score, 0.5)  # respect user intent, cap at 0.5 for ByteTrack
```

---

**ID:** BT-06
**Category:** Race Condition
**Severity:** HIGH
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect`

**Issue:**
`self.tracker` (the `BYTETracker` instance) is read and re-created (`self.tracker = BYTETracker(...)`) from worker threads without any lock. Concurrent workers from the thread pool can corrupt the tracker instance mid-update, producing garbage Kalman state and incorrect track associations.

**Fix:**
Add a dedicated tracker lock:
```python
# In __init__:
self._tracker_lock = threading.Lock()

# In run_detect:
with self._tracker_lock:
    online_targets = self.tracker.update(detections, img_info, img_size)
```
Also guard the re-initialization of `self.tracker` under this lock.

---

**ID:** BT-07
**Category:** Race Condition
**Severity:** HIGH
**File:** ByteTracker implementation
**Function:** `BYTETracker.update`

**Issue:**
`self.frame_id += 1` inside `BYTETracker.update` is not thread-safe. If two frames are processed concurrently (which the pool worker design allows), both threads can read the same `frame_id`, increment it independently, and write back, causing the frame counter to advance by 1 instead of 2. This corrupts the Kalman filter state for all subsequent frames.

**Fix:**
Serializing all calls to `self.tracker.update()` via `self._tracker_lock` (from BT-06) is sufficient, as this eliminates concurrent access to `BYTETracker.update` entirely.

---

**ID:** BT-08
**Category:** Memory
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect`, `__init__`

**Issue:**
`track_history` is a dict keyed by `track_id`. Track IDs are monotonically increasing integers. In a long session or a webcam stream, the dict accumulates thousands of entries for tracks that have long since disappeared. The comment mentions a `'last_seen'` field, but it is never actually written, so the GC condition can never fire.

**Fix:**
Write `last_seen` on every frame a track appears:
```python
track_history[tid]['last_seen'] = current_frame_number
```
Evict stale entries periodically:
```python
stale_ids = [tid for tid, data in track_history.items()
             if current_frame_number - data.get('last_seen', 0) > track_buffer]
for tid in stale_ids:
    del track_history[tid]
```

---

**ID:** BT-09
**Category:** Performance
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect`

**Issue:**
The IoU re-association loop between unmatched tracks and unmatched detections is implemented as pure Python nested loops over `_calculate_iou`. For 20 tracks and 20 detections this means 400 Python function calls per frame at 30fps (12,000 IoU calculations per second in Python).

**Fix:**
Vectorize the IoU computation using NumPy broadcasting:
```python
# Compute full T×D IoU matrix in one vectorized call
iou_matrix = compute_iou_matrix_vectorized(track_boxes, det_boxes)  # shape (T, D)
best_det_idx = np.argmax(iou_matrix, axis=1)  # shape (T,)
best_det_score = iou_matrix[np.arange(len(tracks)), best_det_idx]
matched = best_det_idx[best_det_score > iou_threshold]
```

---

**ID:** BT-10
**Category:** Code Quality
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `track_faces`

**Issue:**
If any single face fails landmark detection during tracking, the entire `track_faces` call aborts and triggers a full re-detect for all faces. Valid tracked faces are abandoned and have to re-acquire track IDs on the next frame, causing flickering face assignments.

**Fix:**
Track failures per face:
```python
failed_faces = []
successful_faces = []
for face in tracked_faces:
    try:
        result = refine_landmarks(face)
        successful_faces.append(result)
    except Exception:
        failed_faces.append(face)

# Only trigger full re-detect if failure rate exceeds threshold
if len(failed_faces) / max(len(tracked_faces), 1) > 0.5:
    return full_redetect()
return successful_faces  # continue with valid faces
```

---

**ID:** BT-11
**Category:** Code Quality
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect`

**Issue:**
`TrackerArgs` is defined inline with hardcoded values: `track_thresh=0.4`, `track_buffer=30` (assumes 30fps without reading actual video FPS), `match_thresh=0.8`, and `frame_rate=30`. None of these values are connected to the UI or to the actual video frame rate. For 60fps or 24fps content, `track_buffer=30` frames is either too short (60fps: 0.5 seconds) or too long (24fps: 1.25 seconds) for the intended behavior.

**Fix:**
Pass the actual video FPS to `BYTETracker`:
```python
video_fps = control.get('VideoFPS', 30)
tracker_args = TrackerArgs(
    track_thresh=control.get('ByteTrackThreshold', 0.4),
    track_buffer=int(video_fps * control.get('ByteTrackBufferSeconds', 1.0)),
    match_thresh=control.get('ByteTrackMatchThreshold', 0.8),
    frame_rate=video_fps
)
```
Expose `ByteTrackThreshold`, `ByteTrackBufferSeconds`, and `ByteTrackMatchThreshold` as UI controls in the tracker settings section.

---

**ID:** BT-12
**Category:** Code Quality
**Severity:** LOW
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect`

**Issue:**
When ByteTrack returns zero active tracks, `kpss` is returned as an empty Python `list` (`[]`). In all other code paths, `kpss` is a NumPy array. This inconsistency in return types makes calling code fragile — any code that calls `np.array(kpss)` or `kpss.shape` on the zero-track result will behave differently.

**Fix:**
Return a consistently-typed empty array:
```python
return (
    np.empty((0, 4), dtype=np.float32),    # bboxes
    np.empty((0,), dtype=np.float32),       # scores
    np.empty((0,), dtype=object)            # kpss
)
```

---

**ID:** BT-13
**Category:** Robustness
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `run_detect` (webcam path)

**Issue:**
When used with a webcam, there is no scene-cut or frame-discontinuity detection. If the user briefly covers the camera, moves it to a completely different scene, or the video source resets, the Kalman filters accumulate stale state indefinitely. On the next real detection, tracks associate with wrong faces because the predicted positions are far from the actual face positions.

**Fix:**
Implement a simple scene-cut detector: if the fraction of successfully matched tracks drops below a threshold (e.g. fewer than 30% of existing tracks matched), treat it as a scene cut and reset the tracker:
```python
if active_tracks > 0 and matched_count / active_tracks < 0.3:
    logger.info("ByteTrack: scene cut detected — resetting tracker")
    self.tracker = BYTETracker(tracker_args, frame_rate=video_fps)
    track_history.clear()
```

---

**ID:** BT-14
**Category:** Robustness
**Severity:** MED
**File:** `app/processors/frame_worker.py`
**Function:** `track_faces`

**Issue:**
When landmark refinement fails for a tracked face, a fallback confidence score of `0.99` is assigned. This is unrealistically high and prevents any secondary landmark model from ever being selected to improve the result, because the primary model's confidence always dominates.

**Fix:**
Use a conservative fallback score that reflects uncertainty:
```python
fallback_score = 0.5  # conservative fallback — secondary model can improve this
```

---

## 7. Deferred / Architectural Items

The following improvements require broader architectural changes or UI design work that goes beyond a localized code fix. They are documented here for future planning rather than immediate implementation.

---

### ARCH-01 — Full Thread-Safety Overhaul for `target_faces`

**Affected IDs:** FW-RACE-01, FW-RACE-02, FW-RACE-05, FW-ROBUST-12

**Description:**
The root cause of multiple race conditions is that `self.main_window.target_faces`, `self.main_window.default_parameters.data`, and several Qt widget states are accessed directly from background worker threads. The correct architectural fix is to snapshot all required UI state into an immutable data structure at the moment a frame is queued by the feeder, and pass that snapshot through the entire processing pipeline.

**Proposed approach:**
1. Define a `FrameControlSnapshot` dataclass that captures all required UI state at queue time:
   - `target_faces: dict` (shallow copy under lock)
   - `default_parameters: dict` (deep copy under lock)
   - `swap_enabled: bool`
   - `edit_enabled: bool`
   - `view_mode: str`
2. The feeder thread populates `FrameControlSnapshot` under `self.lock` before queuing each frame.
3. All worker functions receive `FrameControlSnapshot` as a parameter; no function accesses `self.main_window` directly from a worker thread.
4. Remove `self.lock` workarounds scattered through the code once the snapshot pattern is uniformly adopted.

**Estimated scope:** Medium — affects feeder, `_process_frame_standard`, `_process_frame_vr180`, `swap_core`, `_find_best_target_match`, `process_and_emit_task`.

---

### ARCH-02 — Full VR Converter Caching System

**Affected IDs:** VR-06, VR-08, VR-10

**Description:**
The VR pipeline currently reconstructs `EquirectangularConverter` and `PerspectiveConverter` from scratch every frame, discarding cached sampling grids. A proper caching system would:
1. Make `EquirectangularConverter` a long-lived object held at `FrameWorker` level, invalidated only on resolution change.
2. Promote the `_persp_cache` sampling grid cache in `Equirec2Perspec_vr` from an instance variable to a bounded class-level `OrderedDict` keyed by `(device, FOV, height, width, THETA, PHI)`.
3. Accept an already-GPU tensor as input to eliminate redundant PCIe transfers (VR-05).

**Estimated scope:** Medium — requires changes to `EquirectangularConverter`, `PerspectiveConverter`, `Equirec2Perspec_vr`, and `_process_frame_vr180`.

---

### ARCH-03 — ByteTrack UI Parameter Exposure

**Affected IDs:** BT-05, BT-11

**Description:**
ByteTrack has several critical parameters that are currently hardcoded: detection score threshold, track buffer duration, match threshold, and frame rate. These significantly affect tracking quality and have no default values appropriate for all use cases. Exposing them in the UI would allow users to tune tracking for their specific content (film grain, fast motion, occlusion frequency, etc.).

**Proposed UI additions (in tracker/detection settings panel):**
- `ByteTrack Score Threshold` slider (range 0.1–0.9, default 0.4)
- `ByteTrack Buffer (seconds)` slider (range 0.1–3.0, default 1.0) — auto-converts to frames using detected video FPS
- `ByteTrack Match Threshold` slider (range 0.5–1.0, default 0.8)

**Implementation notes:**
- Video FPS must be determined at session start and passed to `BYTETracker` at initialization.
- `TrackerArgs` should be rebuilt when any of these parameters change, not just at startup.
- The tracker instance must be re-created (not just reconfigured) when `track_buffer` changes, as it is used to initialize the Kalman filter's covariance parameters.

**Estimated scope:** Medium — requires UI widget additions, parameter wiring through `control` dict, and `BYTETracker` lifecycle management changes.

---

*End of document*
