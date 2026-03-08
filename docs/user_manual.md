# User Manual

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Face Swap Tab](#3-face-swap-tab)
4. [Face Restoration](#4-face-restoration)
5. [Denoiser](#5-denoiser)
6. [Face Expression Restorer](#6-face-expression-restorer)
7. [Face Pose / Expression Editor](#7-face-pose--expression-editor)
8. [Frame Enhancers](#8-frame-enhancers)
9. [Face Detection & Tracking](#9-face-detection--tracking)
10. [Job Manager](#10-job-manager)
11. [Presets](#11-presets)
12. [Video Timeline & Markers](#12-video-timeline--markers)
13. [Recording & Output](#13-recording--output)
14. [Settings](#14-settings)
15. [Model Optimiser](#15-model-optimiser)
16. [Tips & Best Practices](#16-tips--best-practices)
17. [Glossary](#17-glossary)

---

## 1. Introduction

VisoMaster Fusion is a desktop application for AI-powered face swapping, enhancement, and editing on images, videos, and live webcam feeds. It provides a full pipeline of tools — from face detection through swapping, masking, restoration, and expression editing — all controlled through a graphical interface built with PySide6.

The application supports multiple AI inference backends (CPU, CUDA, DirectML, TensorRT) and includes a batch job manager for processing multiple files unattended.

---

## 2. Getting Started

### 2.1 Launcher

When you first open VisoMaster Fusion, a launcher window appears. From here you can:

- Select your compute device (CPU, CUDA GPU, DirectML, or TensorRT)
- Update the application and download model files
- Configure initial settings before the main window opens

### 2.2 Main Window Layout

The main window is divided into several key areas:

- **Left panel** — source face input and face cards for assigning reference faces
- **Centre** — media preview with video playback controls and a timeline
- **Right panel** — tabbed settings panels (Face Swap, Face Editor, Denoiser, Settings)
- **Top toolbar** — file open/save, recording controls, and preset management

### 2.3 Supported Media Types

- **Images** — JPG, PNG, and other common still formats
- **Videos** — MP4 and most container formats supported by FFmpeg
- **Webcam / Live input** — real-time processing from a connected camera

### 2.4 Loading Media

Click the Open File button (or drag-and-drop) to load a target image or video. Source faces — the faces you want to paste in — are loaded separately via the face input panel on the left. Each source face becomes a face card that can be assigned to one or more detected faces in the target.

---

## 3. Face Swap Tab

The Face Swap tab contains the core swapping controls. Settings here apply per face card, so different people in the same clip can use entirely different configurations.

### 3.1 Swapper Model

Choose the AI model used to perform the face transfer. Each model has different characteristics:

| Model | Description |
|---|---|
| **Inswapper128** | The default model. Fast, versatile, and works well at multiple resolutions. Good starting point for most use cases. |
| **InStyleSwapper256 A / B / C** | Three style-aware variants operating at 256 px (optionally 512 px). Tend to preserve skin tone and style cues from the target. |
| **SimSwap512** | Operates natively at 512 px. Good identity preservation and fine detail. |
| **GhostFace v1 / v2 / v3** | A family of lightweight swappers. v2 and v3 generally outperform v1 in sharpness and identity fidelity. |
| **CSCS** | Combines two embeddings (appearance + identity) for stronger likeness. Best for challenging angles. |
| **DeepFaceLive (DFM)** | Uses custom pretrained DFM model files placed in the `onnxmodels/dfm_models` folder. Supports AMP Morph Factor and RCT colour transfer. |

### 3.2 Swapper Resolution

Available when using Inswapper128. Sets the internal resolution of the face crop during swapping (128, 256, 384, or 512 px). Higher values give more detail but are slower. Enable **Auto Resolution** to let the app pick based on the detected face size in the target frame.

### 3.3 Similarity Threshold

A filter (1–100) that controls how closely a detected face in the target must match your reference face card before the swap is applied. Higher values are stricter — only near-identical faces get swapped. Useful when multiple people share the screen and you only want to swap one of them.

### 3.4 Swap Strength & Likeness

| Feature | Description |
|---|---|
| **Strength** | Runs additional swap iterations on the result to deepen the effect. The Amount slider goes up to 500% (5× passes). 200% is a common sweet spot. |
| **Mode 2 (Anti-Drift)** | An advanced iteration mode using phase correlation and frequency separation. Reduces drift across many passes and better preserves skin texture. |
| **Face Likeness** | Directly adjusts how much the result resembles the source face versus the target. Negative values lean toward the target; values above 1.0 push harder toward the source. |
| **Face Keypoints Replacer** | Transfers the spatial landmark layout of the target face onto the source before swapping, helping the result fit the target's head pose and geometry. |
| **Pre-Swap Sharpness** | Sharpens the original face before it enters the swap model. Can improve edge detail but may interfere with Auto Face Restorer. |

### 3.5 Masks

Masks control which pixels from the swapped face are blended back into the original frame. Multiple mask types can be stacked.

#### 3.5.1 Border Mask

A rectangular mask with adjustable Top, Bottom, Left, Right, and Side edges. Anything outside the mask boundary fades back to the original image. Useful for hiding stray pixels at the hairline or chin. Includes a **Profile Auto-Fade** option that automatically fades the far edge of the face when the head is turned in profile view.

#### 3.5.2 Occluder Mask

Detects objects covering the face — a hand, glasses, a microphone — and cuts them out of the swap so they appear naturally in the final composite. An **Occluder Size** slider grows or shrinks the detected region. The **Inner Mouth Protection** toggle uses FaceParser to prevent the tongue or inner mouth from being accidentally erased when growing the mask.

#### 3.5.3 XSeg Mask

A second occlusion method using a dedicated XSeg segmentation model. Provides an independent mask channel that can be blended with the Occluder. Includes a separate **Mouth XSeg** option that applies XSeg specifically to the mouth region to fix artefacts on open mouths. An Inner Mouth Protection toggle is also available here.

#### 3.5.4 CLIP Text Mask

Uses the CLIP vision-language model to identify objects described in plain English (e.g. "glasses", "hat", "hand") and cuts them from the swap. Type one or more comma-separated terms into the text box and press Enter. Increase the strength slider to make the segmentation more aggressive.

#### 3.5.5 Mouth Fit & Align

Repositions and scales the original mouth region to fit cleanly inside the swapped face without distorting its shape. Can be used independently of FaceParser. Options include: using the original mouth as the reference, pasting the mouth mask after the restorers, applying Edge-Aware Unsharp Masking to sharpen teeth and lip edges, and a Mouth Zoom slider.

#### 3.5.6 FaceParser Mask (Lips)

Uses a semantic face parsing model to independently grow the upper lip, lower lip, and general mouth region in the swap mask, giving precise control over how much of the mouth area blends back into the original.

#### 3.5.7 Background Mask

When enabled, the unprocessed background from the original image shows through in the final composite rather than being replaced by the swapped result. Useful when you want the swap to affect only the face region.

---

## 4. Face Restoration

After swapping, one or two face restorer models can be applied to sharpen details and correct AI artefacts. Restorers operate on the aligned face crop and blend the result back.

### 4.1 Restorer Models

| Model | Description |
|---|---|
| **GFPGAN v1.4** | Fast and versatile all-round restorer. Good default choice. |
| **GFPGAN-1024** | Higher-resolution variant. More detail at the cost of speed. |
| **CodeFormer** | Quality-focused restorer with a Fidelity Weight slider (0–1). Lower fidelity = more creative but less faithful; higher = closer to the original. |
| **GPEN-256 / 512 / 1024 / 2048** | GPEN at different internal resolutions. Higher = more detail, slower. |
| **RestoreFormer++** | Attention-based restorer. Tends to produce very natural skin. |
| **VQFR-v2** | Vector-quantised restorer. Supports a Fidelity Weight similar to CodeFormer. |

### 4.2 Restorer Controls

| Control | Description |
|---|---|
| **Alignment** | How the restored face is positioned back into the frame: Original (exact alignment), Blend (smooth blend), or Reference (align to the reference face). |
| **Blend** | The mix ratio (0–100%) between the restored face and the raw swap output. 100% uses only the restorer result. |
| **Auto Restore** | Automatically adjusts the blend amount per frame based on a sharpness analysis. Useful when face size or motion varies across a video. |
| **Sharpness Mask** | Within Auto Restore, uses a per-pixel sharpness map to apply stronger blending only where the image is soft. |
| **Second Restorer** | A second, independent restorer pass with its own model and blend settings. Can be set to run at the end of the full pipeline — after the Face Editor — to recover sharpness lost by later processing steps. |

---

## 5. Denoiser

The Denoiser uses a UNet-based diffusion model to reduce noise and reconstruct fine texture on the aligned face. It can be applied at three points in the pipeline: before the restorers, after the first restorer, and after all restorers.

| Setting | Description |
|---|---|
| **Single Step mode** | Adds and then removes a controlled amount of noise in one pass. Fast and subtle. |
| **DDIM mode** | Full iterative diffusion over multiple steps. More detail, more processing time. Steps and CFG Scale are configurable. |
| **Single Step Timestep (t)** | Controls how much noise is injected and therefore removed. Lower values are more conservative. |
| **DDIM Steps** | Number of denoising iterations. More steps = more refined result. |
| **CFG Scale** | How strongly the denoiser follows the reference features. Higher values increase adherence to the source appearance. |
| **Latent Sharpening** | Applies sharpening directly inside the latent space before decoding. Recommended value: around 0.15. |
| **Exclusive Reference Path** | Forces the UNet to attend only to reference key/value features, maximising focus on the source face style. |
| **Base Seed** | Fixed random seed for reproducible noise patterns across all frames. |

---

## 6. Face Expression Restorer

The Face Expression Restorer transfers the expression, eye movement, and head pose from the original (driving) face onto the swapped face using the LivePortrait model pipeline. This corrects the "frozen" look that can occur after swapping.

### 6.1 Pipeline Position

Choose where in the processing chain the expression restorer runs — before or after the face restorers. Running it after can compensate for any stiffening introduced by restoration.

### 6.2 Core Controls

| Control | Description |
|---|---|
| **Neutral Factor** | The percentage of expression to restore. Because the swapped face already carries some expression from the swap model, this should generally be kept below 1.0. |
| **Expression Factor** | Controls the intensity of the expression transfer between the driving face and the swapped result. |
| **Animation Region** | Specifies which facial regions are involved in the restoration (eyes, lips, general features, etc.). |
| **Micro-Expression Boost** | Amplifies subtle movements that might otherwise be lost during the swap. Default is 1.0. |
| **Relative Position** | Makes the animation relative to the initial pose of the source image, which typically produces a more natural result. |

### 6.3 Per-Region Controls

Each region (Eyes, Brows, Lips, General Face Features) has independent toggles and factor sliders, plus these additional options:

| Control | Description |
|---|---|
| **Retargeting (Eyes / Lips)** | Adjusts the open/close ratio of eyes or lips to match the driving face more precisely. A Multiplier slider controls the intensity. |
| **Normalize (Eyes / Lips)** | Normalises the open/close ratio using a threshold so extreme values are clamped to a sensible range. A Max Open Ratio cap is also available for eyes. |
| **Include Nose / Jaw / Cheek / Contour / Head Top** | Adds the corresponding landmark group to the general expression region for finer control over which parts of the face move. |

### 6.4 Temporal Smoothing

The expression restorer includes internal smoothing (SmartSmoother and a One Euro Filter) to reduce per-frame jitter on ratios and keypoints, producing steadier animation across video playback.

---

## 7. Face Pose / Expression Editor

The Face Pose/Expression Editor lets you directly manipulate the swapped face's pose and expression using sliders, without needing a driving video. It uses the LivePortrait model pipeline under the hood.

### 7.1 Head Pose

| Control | Description |
|---|---|
| **Head Pitch** | Tilts the face up or down (nodding motion). |
| **Head Yaw** | Rotates the face left or right (turning motion). |
| **Head Roll** | Tilts the head sideways. |
| **X / Y / Z-Axis Movement** | Translates the face along the horizontal, vertical, or depth axis. |

### 7.2 Eye & Brow Controls

| Control | Description |
|---|---|
| **Eyes Open/Close Ratio** | Opens or closes the eyes on a continuous scale. |
| **Eye Wink** | Triggers a wink on one eye. |
| **EyeBrows Direction** | Raises or lowers the eyebrows. |
| **EyeGaze Horizontal / Vertical** | Redirects the gaze direction without moving the head. |

### 7.3 Mouth & Lip Controls

| Control | Description |
|---|---|
| **Lips Open/Close Ratio** | Opens or closes the mouth. |
| **Mouth Pouting** | Pushes the lips forward into a pout. |
| **Mouth Pursing** | Tightens and narrows the lips. |
| **Mouth Grin** | Widens the mouth into a grin. |
| **Mouth Smile** | Curves the corners of the mouth into a smile. |

### 7.4 Makeup

AI-powered makeup is applied using the FaceParser model to identify facial regions, then colour-blended on top of the image. Each area has independent Red/Green/Blue colour sliders and a Blend Amount (0 = original colour, 1 = full target colour).

| Area | Description |
|---|---|
| **Face Makeup** | Colours the skin on the face — cheeks, forehead, nose bridge — excluding hair, eyebrows, eyes, and lips. |
| **Hair Makeup** | Colours the hair region. |
| **EyeBrows Makeup** | Colours the eyebrows. |
| **Lips Makeup** | Colours the lips. |

---

## 8. Frame Enhancers

Frame Enhancers improve the quality of the entire output frame, not just the face region. They are applied as a post-processing step.

### 8.1 Upscaling Models

| Model | Description |
|---|---|
| **RealESRGAN x2 / x4 Plus** | AI super-resolution at 2× or 4× scale. Excellent general-purpose upscaler for photos and videos. |
| **BSRGan x2 / x4** | Blind super-resolution model. Good at recovering fine detail on compressed or blurry inputs. |
| **UltraSharp x4** | Optimised for sharpness and edge clarity at 4× scale. |
| **UltraMix x4** | A blended upscaler model balancing sharpness and naturalness. |
| **RealESR-General x4v3** | A general-purpose variant of RealESRGAN tuned for a wide range of degradation types. |

### 8.2 Colourisation Models

| Model | Description |
|---|---|
| **DeOldify Artistic** | Colourises black-and-white footage with a painterly, vibrant style. |
| **DeOldify Stable** | Colourises with a more conservative, consistent style suited to historical photos. |
| **DeOldify Video** | A temporal-aware variant of DeOldify optimised for video to reduce colour flickering. |
| **DDColor Artistic** | Modern deep-learning colouriser with rich, saturated colours. |
| **DDColor** | Standard DDColor model offering natural-looking colourisation. |

---

## 9. Face Detection & Tracking

### 9.1 Face Detector Models

The app uses ONNX-based detectors to locate faces in each frame before swapping. The active model is selected in the Settings tab. Supported models include RetinaFace and YOLOv8-based detectors at various resolutions.

| Setting | Description |
|---|---|
| **Detect Score** | Minimum confidence threshold for a detection to be accepted. Lower values catch more faces but may produce false positives. |
| **Max Faces to Detect** | Limits how many faces are processed per frame. Useful for performance when only one or two faces are relevant. |
| **Detection Interval** | Runs face detection only every N frames and reuses the result in between. Reduces CPU/GPU load on high-frame-rate video. |
| **Auto Rotation** | Rotates the input frame to the detected face's upright orientation before processing. |

### 9.2 ByteTrack Face Tracking

When enabled, ByteTrack assigns a consistent ID to each face across frames. This allows the app to apply the correct face card settings to the right person even when faces briefly leave frame or overlap.

| Setting | Description |
|---|---|
| **Track Threshold** | Minimum detection score for a new track to be initialised. |
| **Match Threshold** | How closely a detection must match an existing track to be linked to it. |
| **Track Buffer (Frames)** | How many frames a track is kept alive after the face disappears before it is discarded. |

---

## 10. Job Manager

The Job Manager allows you to queue multiple target files for batch processing, each with its own saved configuration. Jobs run sequentially in the background so you can queue a series of videos and let them run unattended.

| Feature | Description |
|---|---|
| **Add Job** | Adds the current target file and all current control settings as a new job entry. |
| **Save / Load Jobs** | Jobs are stored as JSON files in the `jobs/` folder and can be reloaded across sessions. |
| **Auto Swap** | When enabled, swapping begins automatically as soon as a target file is loaded. |
| **Keep Selected Input Faces** | Retains the loaded source face embeddings between jobs so you don't need to re-select them for each file. |
| **Swap Input Face Only Once** | Processes each source face's embedding only once per job rather than re-computing it for every frame. Speeds up processing on long videos. |

---

## 11. Presets

Presets save and restore all control panel settings as named JSON files stored in the `presets/` folder. They let you quickly switch between configurations — for example, a preset optimised for portrait photos versus one for action video.

- Save a preset by clicking the Save button and entering a name
- Apply a preset by double-clicking its name in the preset list
- The **Control Preset** toggle enables or disables automatically applying preset settings when a face card is selected
- Presets can be renamed or deleted via the right-click context menu

---

## 12. Video Timeline & Markers

The video timeline supports time-coded markers that let you apply different face card settings at different points in a video. Useful for scenes where the camera angle, lighting, or cast changes.

- Click **Add Marker** to insert a marker at the current playback position
- Each marker stores the currently active control settings
- **Previous / Next Marker** buttons jump between markers for quick navigation
- **Marker Save** commits the current settings to the selected marker
- **Track Markers on Video Seek** automatically moves to the nearest marker when you scrub the timeline

---

## 13. Recording & Output

### 13.1 Recording Controls

The recording toolbar contains Start, Stop, and Pause buttons for capturing the processed output. Output files are saved in the `outputs/` folder by default.

### 13.2 FFmpeg Output Options

| Option | Description |
|---|---|
| **Presets SDR / HDR** | FFmpeg encoding presets for standard- and high-dynamic-range output. Use the HDR preset only on HDR source material. |
| **Quality** | CRF-equivalent quality setting. Lower values produce larger, higher-quality files. |
| **Spatial AQ / Temporal AQ** | Adaptive quantisation options available with NVENC. Improve perceptual quality in flat areas and across time. |
| **Frame resize to 1920×1080** | Forces the output to 1080p resolution regardless of the source dimensions. |
| **Open Output Folder After Recording** | Automatically opens the output directory in your file explorer when recording stops. |

### 13.3 Playback Settings

| Setting | Description |
|---|---|
| **Playback FPS Override** | Sets a custom playback frame rate instead of reading it from the video file. |
| **Playback Buffering** | Enables frame buffering to smooth out playback on slower systems. |
| **Playback Loop** | Loops video playback continuously. |
| **Audio Playback Volume** | Controls the volume of audio during preview playback. |
| **Audio Start Delay** | Introduces a delay (in seconds) before audio begins, useful to compensate for sync issues. |

---

## 14. Settings

### 14.1 Performance

| Setting | Description |
|---|---|
| **Providers Priority** | The ordered list of inference backends. CUDA gives fast results on Nvidia GPUs. DirectML works on AMD and some integrated GPUs. CPU is the slowest but universally available. TensorRT unlocks the highest GPU throughput after a one-time engine build. |
| **Number of Threads** | Number of CPU threads used by the ONNX Runtime for CPU-mode inference. |
| **Resize Input Source** | Downscales the input resolution before processing to trade output quality for speed. |
| **Input Resolution Target** | The target resolution when Resize Input Source is enabled. |

### 14.2 Face Recognition

| Setting | Description |
|---|---|
| **Recognition Model** | The ArcFace-based embedding model used to generate face identity vectors for matching. Options include Inswapper128ArcFace, SimSwapArcFace, GhostArcFace, and CSCSArcFace. |
| **Swapping Similarity Type** | The alignment strategy used when computing face embeddings: Opal (standard), Pearl (offset alignment), or Optimal (full warp). Affects how closely the embedding captures the face geometry. |
| **Embedding Merge Method** | When multiple source images are provided for one face card, controls how their embeddings are combined. |

### 14.3 Appearance

The **Theme** selector lets you choose from a set of built-in UI colour schemes: Dark, Light, True Dark, Dracula, Gruvbox, Monokai, Nord, Solarized Dark, and Solarized Light. Themes are applied immediately without restarting.

### 14.4 VR / 360° Mode

When working with VR180 or equirectangular 360° video, enable **VR180 Mode**. The app will unproject perspective crops for each face, process them, and stitch them back into the equirectangular image. The **VR180 Eye Mode** setting controls whether processing targets the left eye, right eye, or both eyes of a side-by-side VR180 frame.

### 14.5 Advanced Embedding Editor

The Advanced Embedding Editor allows you to inspect and manually adjust the raw face identity vectors before they are used in swapping. This is an expert-level tool for cases where the automatic embedding produces an unsatisfactory likeness.

---

## 15. Model Optimiser

The Model Optimiser (`app/tools/optimize_models.py`) converts ONNX model files into TensorRT engine files for maximum inference speed on Nvidia GPUs. The conversion is performed once and the resulting engine files are cached. On the first use of a newly converted model, a short finalisation step runs and a progress dialog is displayed during this time.

> **Note:** TensorRT engines are hardware-specific. An engine built on one GPU will not work on a different GPU model and must be rebuilt.

---

## 16. Tips & Best Practices

- Start with the default **Inswapper128** model and **Auto Resolution** to verify your setup before trying higher-quality but slower options
- Enable **Face Restorer** (GFPGAN v1.4) as a first step — it corrects most visible artefacts with minimal configuration
- Use the **Similarity Threshold** to target a specific person in a crowd. Set it high (80+) if only one face should be swapped
- For video, enable **ByteTrack face tracking** so the app keeps the correct source assigned to the correct person across cuts and occlusions
- When using the **Face Expression Restorer**, keep the Neutral Factor below 1.0 — a value around 0.6–0.8 is usually sufficient
- If the swapped face looks blurry, try increasing Swapper Resolution or enabling Strength at 200%
- Save frequently used configurations as **Presets** so you can switch quickly between different target subjects or content types
- For batch processing, load all jobs into the **Job Manager** and let them run unattended
- For difficult multi-face scenes, process one face at a time — remove all other detected faces, record, then run the output back through for the next face

---

## 17. Glossary

| Term | Definition |
|---|---|
| **ArcFace** | A deep learning model that converts a face image into a compact numerical vector (embedding) representing its identity. |
| **ByteTrack** | A multi-object tracking algorithm that assigns consistent IDs to detected faces across video frames. |
| **DFM** | DeepFaceLive Model — a custom pretrained face swap model format originally from the DeepFaceLive project. |
| **Embedding** | A fixed-length numerical vector that encodes the identity of a face, used for matching and swapping. |
| **FaceParser** | A semantic segmentation model that labels every pixel of a face image into classes: skin, hair, lips, eyes, etc. |
| **ONNX** | An open model format used by VisoMaster Fusion to run AI models across different hardware backends. |
| **TensorRT** | Nvidia's inference optimisation library. Provides the fastest possible GPU performance after a one-time engine build. |
| **VR180** | A 180-degree equirectangular video format used in VR headsets. Two eye views are placed side by side. |
| **XSeg** | An occlusion segmentation model trained to identify foreground objects covering the face. |
| **CLIP** | OpenAI's vision-language model. Used here to segment objects described in plain text from the face region. |
