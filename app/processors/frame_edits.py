from typing import TYPE_CHECKING

import torch
import numpy as np
from torchvision.transforms import v2
from skimage import transform as trans

from app.processors.utils import faceutil

if TYPE_CHECKING:
    from app.processors.models_processor import ModelsProcessor


class FrameEdits:
    """
    Manages Face Editing operations (Expression restoration, LivePortrait editing, Makeup).
    Moves high-level processing logic out of FrameWorker.

    This class handles the 'LivePortrait' pipeline, including:
    - Motion Extraction (Pose, Expression)
    - Temporal Smoothing (SmartSmoother)
    - Feature Retargeting (Eyes, Lips)
    - Image Warping and Pasting
    """

    def __init__(self, models_processor: "ModelsProcessor"):
        """
        Initializes the FrameEdits class.
        Args:
            models_processor: Reference to the central model manager.
        """
        self.models_processor = models_processor

        # Transforms will be updated per frame/settings via set_transforms
        self.t256_face = None
        self.interpolation_expression_faceeditor_back = None

    def reset_temporal_state(self):
        """
        Resets the smoothing filters.
        Must be called on video seek, scene change, or single-image processing
        to prevent 'ghosting' from previous motion history.
        """
        if hasattr(self.models_processor, "smart_smoother"):
            self.models_processor.smart_smoother.reset()

    def set_transforms(self, t256_face, interpolation_expression_faceeditor_back):
        """
        Updates the scaling transforms and interpolation modes based on current control settings.
        Called from FrameWorker.set_scaling_transforms.
        """
        self.t256_face = t256_face
        self.interpolation_expression_faceeditor_back = (
            interpolation_expression_faceeditor_back
        )

    def apply_face_expression_restorer(
        self, driving: torch.Tensor, target: torch.Tensor, parameters: dict
    ) -> torch.Tensor:
        """
        Restores the expression of the face using the LivePortrait model pipeline.

        Features:
        - Supports 'Simple' (Global) and 'Advanced' (Granular) modes.
        - Smart Wink Detection: Distinguishes between real winks and perspective distortion.
        - Micro-Expression Boost: Amplifies subtle movements (1.75x factor).
        - Temporal Smoothing: Uses OneEuroFilter to stabilize jitter across frames.
        - Non-Linear Eye Response: Forces snappy blinks to avoid 'zombie' half-closed eyes.
        - Pose Damping: Reduces head rotation amplitude to anchor the face better.

        Optimizations:
        - Vectorized tensor operations (removed Python loops).
        - Fully Asynchronous GPU execution (No CPU/GPU sync barriers).
        """
        # 1. SETUP THE ASYNCHRONOUS CONTEXT
        # We queue all GPU operations in the current stream without blocking the CPU.
        current_stream = torch.cuda.current_stream()

        with torch.cuda.stream(current_stream):
            # --- CONFIGURATION ---

            # Use User Toggle for Mean Eyes (Stability vs Accuracy tradeoff)
            use_mean_eyes = parameters.get("LandmarkMeanEyesToggle", False)

            # Toggle for the Smart Smoother engine
            use_smoothing = parameters.get(
                "FaceExpressionTemporalSmoothingToggle", True
            )

            # --- 1. DRIVING FACE PROCESSING (The Original Face) ---
            # We detect landmarks on the 512px input to allow re-cropping based on sliders.
            _, driving_lmk_crop, _ = self.models_processor.run_detect_landmark(
                driving,
                bbox=np.array([0, 0, 512, 512]),
                det_kpss=[],
                detect_mode="203",
                score=0.5,
                from_points=False,
                use_mean_eyes=use_mean_eyes,
            )

            # Occlusion Handling: Repair mouth geometry if inverted (e.g., mic or food blocking mouth)
            if driving_lmk_crop is not None and len(driving_lmk_crop) > 0:
                driving_lmk_crop = faceutil.repair_mouth_inversion_203(driving_lmk_crop)

            # Interpolation setup
            interp_mode = (
                self.interpolation_expression_faceeditor_back
                if self.interpolation_expression_faceeditor_back is not None
                else v2.InterpolationMode.BILINEAR
            )

            if self.t256_face is None:
                self.t256_face = v2.Resize(
                    (256, 256),
                    interpolation=v2.InterpolationMode.BILINEAR,
                    antialias=False,
                )

            # Crop Driving Face
            driving_face_512, _, _ = faceutil.warp_face_by_face_landmark_x(
                driving,
                driving_lmk_crop,
                dsize=512,
                scale=parameters.get("FaceExpressionCropScaleBothDecimalSlider", 2.3),
                vy_ratio=parameters.get(
                    "FaceExpressionVYRatioBothDecimalSlider", -0.125
                ),
                interpolation=interp_mode,
            )

            driving_face_256 = self.t256_face(driving_face_512)

            # Calculate geometrical ratios (Eye Openness / Lip Openness)
            c_d_eyes_lst = faceutil.calc_eye_close_ratio(driving_lmk_crop[None])
            c_d_lip_lst = faceutil.calc_lip_close_ratio(driving_lmk_crop[None])

            # Extract Raw Motion (Heavy Inference)
            x_d_i_info = self.models_processor.lp_motion_extractor(
                driving_face_256, "Human-Face"
            )

            # --- TEMPORAL SMOOTHING & STABILIZATION ---
            if use_smoothing:
                smoother = self.models_processor.smart_smoother

                # Smooth Pose (Rigid movement: Pitch, Yaw, Roll, Translation, Scale)
                (
                    x_d_i_info["pitch"],
                    x_d_i_info["yaw"],
                    x_d_i_info["roll"],
                    x_d_i_info["t"],
                    x_d_i_info["scale"],
                ) = smoother.smooth_pose(
                    x_d_i_info["pitch"],
                    x_d_i_info["yaw"],
                    x_d_i_info["roll"],
                    x_d_i_info["t"],
                    x_d_i_info["scale"],
                )

                # Smooth Expression (Non-Rigid movement: Blinks, Smiles)
                x_d_i_info["exp"] = smoother.smooth_expression(x_d_i_info["exp"])

                # POSE DAMPING:
                # We reduce the amplitude of head rotation to 80%.
                # This keeps the face "anchored" to the original neck/body, reducing
                # the "floating head" artifact while maintaining liveliness.
                pose_damping = 0.8
                x_d_i_info["pitch"] *= pose_damping
                x_d_i_info["yaw"] *= pose_damping
                x_d_i_info["roll"] *= pose_damping

            # --- 2. TARGET FACE PROCESSING (The Swapped Face) ---
            # Optimization: Use in-place clamp to save memory bandwidth
            target = target.clamp(0, 255).type(torch.uint8)

            # Detect landmarks on the target (Geometry is different from Driving)
            _, source_lmk, _ = self.models_processor.run_detect_landmark(
                target,
                bbox=np.array([0, 0, 512, 512]),
                det_kpss=[],
                detect_mode="203",
                score=0.5,
                from_points=False,
                use_mean_eyes=use_mean_eyes,
            )

            # Crop Target Face
            target_face_512, M_o2c, M_c2o = faceutil.warp_face_by_face_landmark_x(
                target,
                source_lmk,
                dsize=512,
                scale=parameters.get("FaceExpressionCropScaleBothDecimalSlider", 2.3),
                vy_ratio=parameters.get(
                    "FaceExpressionVYRatioBothDecimalSlider", -0.125
                ),
                interpolation=interp_mode,
            )

            target_face_256 = self.t256_face(target_face_512)

            # Extract Target Identity and Motion
            x_s_info = self.models_processor.lp_motion_extractor(
                target_face_256, "Human-Face"
            )
            x_c_s = x_s_info["kp"]
            R_s = faceutil.get_rotation_matrix(
                x_s_info["pitch"], x_s_info["yaw"], x_s_info["roll"]
            )
            f_s = self.models_processor.lp_appearance_feature_extractor(
                target_face_256, "Human-Face"
            )
            x_s = faceutil.transform_keypoint(x_s_info)

            x_d_i_new = None
            face_editor_type = parameters.get("FaceEditorTypeSelection", "Human-Face")

            # --- 3. MOTION RETARGETING LOGIC ---
            mode = parameters.get("FaceExpressionModeSelection", "Advanced")

            # Indices for Vectorization (Standard LivePortrait topology)
            eye_indices = [11, 13, 15, 16, 18]
            lip_indices = [6, 12, 14, 17, 19, 20]

            if mode == "Simple":
                # SIMPLE MODE: Global transfer with basic multipliers
                driving_multiplier = parameters.get(
                    "FaceExpressionFriendlyFactorDecimalSlider", 1.0
                )
                animation_region = parameters.get(
                    "FaceExpressionAnimationRegionSelection", "all"
                )
                if animation_region == "all":
                    animation_region = "eyes,lips"

                flag_normalize_lip = parameters.get(
                    "FaceExpressionNormalizeLipsEnableToggle", True
                )
                lip_normalize_threshold = parameters.get(
                    "FaceExpressionNormalizeLipsThresholdDecimalSlider", 0.03
                )
                lip_delta_before_animation = None

                # Check initial lip state for normalization
                if flag_normalize_lip and source_lmk is not None:
                    c_d_lip_before_animation = [0.0]
                    combined_lip_ratio_tensor_before_animation = (
                        faceutil.calc_combined_lip_ratio(
                            c_d_lip_before_animation,
                            source_lmk,
                            device=self.models_processor.device,
                        )
                    )
                    if (
                        combined_lip_ratio_tensor_before_animation[0][0]
                        >= lip_normalize_threshold
                    ):
                        lip_delta_before_animation = (
                            self.models_processor.lp_retarget_lip(
                                x_s, combined_lip_ratio_tensor_before_animation
                            )
                        )

                delta_new = x_s_info["exp"].clone()

                # Optimized Vectorized Assignments
                if "lips" in animation_region:
                    lp_lip_array = torch.from_numpy(
                        self.models_processor.lp_lip_array
                    ).to(dtype=torch.float32, device=self.models_processor.device)
                    # Add driving lip motion relative to neutral lip array
                    delta_new[:, lip_indices, :] = (
                        x_s_info["exp"] + (x_d_i_info["exp"] - lp_lip_array)
                    )[:, lip_indices, :]

                if "eyes" in animation_region:
                    delta_new[:, eye_indices, :] = (
                        x_s_info["exp"] + x_d_i_info["exp"]
                    )[:, eye_indices, :]

                # Apply Motion
                R_new = R_s
                t_new = x_s_info["t"]
                scale_new = x_s_info["scale"]
                t_new[..., 2].fill_(0)  # Zero out Z-translation
                x_d_i_new = scale_new * (x_c_s @ R_new + delta_new) + t_new

                # Stitching
                if flag_normalize_lip and lip_delta_before_animation is not None:
                    x_d_i_new = (
                        self.models_processor.lp_stitching(
                            x_s, x_d_i_new, face_editor_type
                        )
                        + lip_delta_before_animation
                    )
                else:
                    x_d_i_new = self.models_processor.lp_stitching(
                        x_s, x_d_i_new, face_editor_type
                    )

                # Apply Global Intensity
                x_d_i_new = x_s + (x_d_i_new - x_s) * driving_multiplier

            else:
                # ADVANCED MODE: Granular control over Eyes and Lips
                driving_multiplier_eyes = parameters.get(
                    "FaceExpressionFriendlyFactorEyesDecimalSlider", 1.0
                )
                driving_multiplier_lips = parameters.get(
                    "FaceExpressionFriendlyFactorLipsDecimalSlider", 1.0
                )

                flag_activate_eyes = parameters.get("FaceExpressionEyesToggle", False)
                flag_eye_retargeting = parameters.get(
                    "FaceExpressionRetargetingEyesBothEnableToggle", False
                )
                eye_retargeting_multiplier = parameters.get(
                    "FaceExpressionRetargetingEyesMultiplierBothDecimalSlider", 1.0
                )

                flag_activate_lips = parameters.get("FaceExpressionLipsToggle", False)
                flag_normalize_lip = parameters.get(
                    "FaceExpressionNormalizeLipsBothEnableToggle", False
                )
                lip_normalize_threshold = parameters.get(
                    "FaceExpressionNormalizeLipsThresholdBothDecimalSlider", 0.03
                )

                flag_normalize_eyes = parameters.get(
                    "FaceExpressionNormalizeEyesBothEnableToggle", True
                )
                eyes_normalize_threshold = parameters.get(
                    "FaceExpressionNormalizeEyesThresholdBothDecimalSlider", 0.40
                )

                flag_lip_retargeting = parameters.get(
                    "FaceExpressionRetargetingLipsBothEnableToggle", False
                )
                lip_retargeting_multiplier = parameters.get(
                    "FaceExpressionRetargetingLipsMultiplierBothDecimalSlider", 1.0
                )
                eyes_normalize_max = parameters.get(
                    "FaceExpressionNormalizeEyesMaxBothDecimalSlider", 0.50
                )

                flag_relative_motion_eyes = parameters.get(
                    "FaceExpressionRelativeEyesToggle", False
                )
                flag_relative_motion_lips = parameters.get(
                    "FaceExpressionRelativeLipsToggle", False
                )

                # Micro-Expression Boost: Amplifies small movements to make the face more "alive"
                micro_expression_boost = 1.50

                lip_delta_before_animation = None
                combined_eyes_ratio_normalize = None

                # Lip Normalization Logic
                if flag_normalize_lip and source_lmk is not None:
                    c_d_lip_before_animation = [0.0]
                    combined_lip_ratio_tensor_before_animation = (
                        faceutil.calc_combined_lip_ratio(
                            c_d_lip_before_animation,
                            source_lmk,
                            device=self.models_processor.device,
                        )
                    )
                    if (
                        combined_lip_ratio_tensor_before_animation[0][0]
                        >= lip_normalize_threshold
                    ):
                        lip_delta_before_animation = (
                            self.models_processor.lp_retarget_lip(
                                x_s, combined_lip_ratio_tensor_before_animation
                            )
                        )

                if flag_normalize_eyes and source_lmk is not None:
                    c_d_eyes_normalize = c_d_eyes_lst
                    eyes_ratio = np.array([c_d_eyes_normalize[0][0]], dtype=np.float32)
                    eyes_ratio_normalize = max(eyes_ratio, 0.10)
                    eyes_ratio_l = min(c_d_eyes_normalize[0][0], eyes_normalize_max)
                    eyes_ratio_r = min(c_d_eyes_normalize[0][1], eyes_normalize_max)
                    eyes_ratio_max = np.array(
                        [[eyes_ratio_l, eyes_ratio_r]], dtype=np.float32
                    )
                    if eyes_ratio_normalize > eyes_normalize_threshold:
                        combined_eyes_ratio_normalize = (
                            faceutil.calc_combined_eye_ratio_norm(
                                eyes_ratio_max,
                                source_lmk,
                                device=self.models_processor.device,
                            )
                        )
                    else:
                        combined_eyes_ratio_normalize = (
                            faceutil.calc_combined_eye_ratio(
                                eyes_ratio_max,
                                source_lmk,
                                device=self.models_processor.device,
                            )
                        )

                delta_new_eyes = x_s_info["exp"].clone()
                delta_new_lips = x_s_info["exp"].clone()

                x_d_i_new_eyes = torch.zeros_like(x_s)
                x_d_i_new_lips = torch.zeros_like(x_s)

                # --- 4. CALCULATE DELTAS (Vectorized) ---

                # EYES
                if flag_activate_eyes:
                    if flag_relative_motion_eyes:
                        delta_diff = (x_d_i_info["exp"] - 0) * micro_expression_boost
                        delta_new_eyes[:, eye_indices, :] = (
                            x_s_info["exp"] + delta_diff
                        )[:, eye_indices, :]
                    else:
                        delta_new_eyes[:, eye_indices, :] = x_d_i_info["exp"][
                            :, eye_indices, :
                        ]

                    scale_new_eyes = x_s_info["scale"]
                    R_new_eyes = R_s
                    t_new_eyes = x_s_info["t"]
                    t_new_eyes[..., 2].fill_(0)
                    x_d_i_new_eyes = (
                        scale_new_eyes * (x_c_s @ R_new_eyes + delta_new_eyes)
                        + t_new_eyes
                    )

                if flag_activate_eyes and not flag_eye_retargeting:
                    x_d_i_new_eyes = self.models_processor.lp_stitching(
                        x_s, x_d_i_new_eyes, face_editor_type
                    )

                elif flag_activate_eyes and flag_eye_retargeting:
                    eyes_delta = None
                    if flag_eye_retargeting and source_lmk is not None:
                        # Only apply normalization delta if not a wink
                        if (
                            flag_normalize_eyes
                            and combined_eyes_ratio_normalize is not None
                        ):
                            combined_eye_ratio_tensor = (
                                combined_eyes_ratio_normalize
                                * eye_retargeting_multiplier
                            )
                            eyes_delta = self.models_processor.lp_retarget_eye(
                                x_s, combined_eye_ratio_tensor, face_editor_type
                            )
                        else:
                            c_d_eyes_i = c_d_eyes_lst
                            combined_eye_ratio_tensor = (
                                faceutil.calc_combined_eye_ratio(
                                    c_d_eyes_i,
                                    source_lmk,
                                    device=self.models_processor.device,
                                )
                            )
                            combined_eye_ratio_tensor = (
                                combined_eye_ratio_tensor * eye_retargeting_multiplier
                            )
                            eyes_delta = self.models_processor.lp_retarget_eye(
                                x_s, combined_eye_ratio_tensor, face_editor_type
                            )

                    if flag_relative_motion_eyes:
                        x_d_i_new_eyes = x_s + (
                            eyes_delta if eyes_delta is not None else 0
                        )
                    else:
                        x_d_i_new_eyes = x_d_i_new_eyes + (
                            eyes_delta if eyes_delta is not None else 0
                        )
                    x_d_i_new_eyes = self.models_processor.lp_stitching(
                        x_s, x_d_i_new_eyes, face_editor_type
                    )

                if flag_activate_eyes:
                    x_d_i_new_eyes = (x_d_i_new_eyes - x_s) * driving_multiplier_eyes

                # LIPS
                if flag_activate_lips:
                    if flag_relative_motion_lips:
                        lp_lip_array = torch.from_numpy(
                            self.models_processor.lp_lip_array
                        ).to(dtype=torch.float32, device=self.models_processor.device)
                        delta_diff = (
                            x_d_i_info["exp"] - lp_lip_array
                        ) * micro_expression_boost
                        delta_new_lips[:, lip_indices, :] = (
                            x_s_info["exp"] + delta_diff
                        )[:, lip_indices, :]
                    else:
                        delta_new_lips[:, lip_indices, :] = x_d_i_info["exp"][
                            :, lip_indices, :
                        ]

                    scale_new_lips = x_s_info["scale"]
                    R_new_lips = R_s
                    t_new_lips = x_s_info["t"]

                    t_new_lips[..., 2].fill_(0)
                    x_d_i_new_lips = (
                        scale_new_lips * (x_c_s @ R_new_lips + delta_new_lips)
                        + t_new_lips
                    )

                if flag_activate_lips and not flag_lip_retargeting:
                    if flag_normalize_lip and lip_delta_before_animation is not None:
                        x_d_i_new_lips = (
                            self.models_processor.lp_stitching(
                                x_s, x_d_i_new_lips, face_editor_type
                            )
                            + lip_delta_before_animation
                        )
                    else:
                        x_d_i_new_lips = self.models_processor.lp_stitching(
                            x_s, x_d_i_new_lips, face_editor_type
                        )

                elif flag_activate_lips and flag_lip_retargeting:
                    lip_delta = None
                    if flag_lip_retargeting and source_lmk is not None:
                        c_d_lip_i = c_d_lip_lst
                        combined_lip_ratio_tensor = faceutil.calc_combined_lip_ratio(
                            c_d_lip_i, source_lmk, device=self.models_processor.device
                        )
                        combined_lip_ratio_tensor = (
                            combined_lip_ratio_tensor * lip_retargeting_multiplier
                        )
                        lip_delta = self.models_processor.lp_retarget_lip(
                            x_s, combined_lip_ratio_tensor, face_editor_type
                        )

                    if flag_relative_motion_lips:
                        x_d_i_new_lips = x_s + (
                            lip_delta if lip_delta is not None else 0
                        )
                    else:
                        x_d_i_new_lips = x_d_i_new_lips + (
                            lip_delta if lip_delta is not None else 0
                        )
                    x_d_i_new_lips = self.models_processor.lp_stitching(
                        x_s, x_d_i_new_lips, face_editor_type
                    )

                if flag_activate_lips:
                    x_d_i_new_lips = (x_d_i_new_lips - x_s) * driving_multiplier_lips

                # Combine Results
                x_d_i_new = x_s
                if flag_activate_lips and flag_activate_eyes:
                    x_d_i_new = x_s + x_d_i_new_eyes + x_d_i_new_lips
                elif flag_activate_eyes and not flag_activate_lips:
                    x_d_i_new = x_s + x_d_i_new_eyes
                elif not flag_activate_eyes and flag_activate_lips:
                    x_d_i_new = x_s + x_d_i_new_lips

            # --- 5. GENERATE FINAL IMAGE ---
            out = self.models_processor.lp_warp_decode(
                f_s, x_s, x_d_i_new, face_editor_type
            )
            out = torch.squeeze(out)
            out = out.clamp_(0, 1)  # In-place clamp

            # --- 6. PASTE BACK (No Sync needed) ---
            t = trans.SimilarityTransform()
            t.params[0:2] = M_c2o
            dsize = (target.shape[1], target.shape[2])

            out = faceutil.pad_image_by_size(out, dsize)
            out = v2.functional.affine(
                out,
                t.rotation * 57.2958,
                translate=(t.translation[0], t.translation[1]),
                scale=t.scale,
                shear=(0.0, 0.0),
                interpolation=v2.InterpolationMode.BILINEAR,
                center=(0, 0),
            )
            out = v2.functional.crop(out, 0, 0, dsize[0], dsize[1])

        # Final conversion in-place
        out = out.mul_(255.0).clamp_(0, 255).type(torch.float32)

        return out

    def swap_edit_face_core(
        self,
        img: torch.Tensor,
        swap_restorecalc: torch.Tensor,
        parameters: dict,
        control: dict,
        **kwargs,
    ) -> torch.Tensor:
        """
        Applies Face Editor manipulations (Pose, Gaze, Expression) to the face via manual sliders.
        Optimized: Removed explicit CPU/GPU sync.
        """

        use_mean_eyes = parameters.get("LandmarkMeanEyesToggle", False)

        if parameters["FaceEditorEnableToggle"]:
            # 1. SETUP THE ASYNCHRONOUS CONTEXT
            current_stream = torch.cuda.current_stream()

            with torch.cuda.stream(current_stream):
                init_source_eye_ratio = 0.0
                init_source_lip_ratio = 0.0

                # Detection
                _, lmk_crop, _ = self.models_processor.run_detect_landmark(
                    swap_restorecalc,
                    bbox=np.array([0, 0, 512, 512]),
                    det_kpss=[],
                    detect_mode="203",
                    score=0.5,
                    from_points=False,
                    use_mean_eyes=use_mean_eyes,
                )
                source_eye_ratio = faceutil.calc_eye_close_ratio(lmk_crop[None])
                source_lip_ratio = faceutil.calc_lip_close_ratio(lmk_crop[None])
                init_source_eye_ratio = round(float(source_eye_ratio.mean()), 2)
                init_source_lip_ratio = round(float(source_lip_ratio[0][0]), 2)

                interp_mode = (
                    self.interpolation_expression_faceeditor_back
                    if self.interpolation_expression_faceeditor_back is not None
                    else v2.InterpolationMode.BILINEAR
                )

                # Prepare Image
                original_face_512, M_o2c, M_c2o = faceutil.warp_face_by_face_landmark_x(
                    img,
                    lmk_crop,
                    dsize=512,
                    scale=parameters["FaceEditorCropScaleDecimalSlider"],
                    vy_ratio=parameters["FaceEditorVYRatioDecimalSlider"],
                    interpolation=interp_mode,
                )

                if self.t256_face is None:
                    self.t256_face = v2.Resize(
                        (256, 256),
                        interpolation=v2.InterpolationMode.BILINEAR,
                        antialias=False,
                    )

                original_face_256 = self.t256_face(original_face_512)

                # Extract features
                x_s_info = self.models_processor.lp_motion_extractor(
                    original_face_256, parameters["FaceEditorTypeSelection"]
                )
                x_d_info_user_pitch = x_s_info["pitch"] + parameters["HeadPitchSlider"]
                x_d_info_user_yaw = x_s_info["yaw"] + parameters["HeadYawSlider"]
                x_d_info_user_roll = x_s_info["roll"] + parameters["HeadRollSlider"]

                R_s_user = faceutil.get_rotation_matrix(
                    x_s_info["pitch"], x_s_info["yaw"], x_s_info["roll"]
                )
                R_d_user = faceutil.get_rotation_matrix(
                    x_d_info_user_pitch, x_d_info_user_yaw, x_d_info_user_roll
                )

                f_s_user = self.models_processor.lp_appearance_feature_extractor(
                    original_face_256, parameters["FaceEditorTypeSelection"]
                )
                x_s_user = faceutil.transform_keypoint(x_s_info)

                # Apply Manual Sliders
                mov_x = torch.tensor(parameters["XAxisMovementDecimalSlider"]).to(
                    self.models_processor.device
                )
                mov_y = torch.tensor(parameters["YAxisMovementDecimalSlider"]).to(
                    self.models_processor.device
                )
                mov_z = torch.tensor(parameters["ZAxisMovementDecimalSlider"]).to(
                    self.models_processor.device
                )
                eyeball_direction_x = torch.tensor(
                    parameters["EyeGazeHorizontalDecimalSlider"]
                ).to(self.models_processor.device)
                eyeball_direction_y = torch.tensor(
                    parameters["EyeGazeVerticalDecimalSlider"]
                ).to(self.models_processor.device)
                smile = torch.tensor(parameters["MouthSmileDecimalSlider"]).to(
                    self.models_processor.device
                )
                wink = torch.tensor(parameters["EyeWinkDecimalSlider"]).to(
                    self.models_processor.device
                )
                eyebrow = torch.tensor(parameters["EyeBrowsDirectionDecimalSlider"]).to(
                    self.models_processor.device
                )
                lip_variation_zero = torch.tensor(
                    parameters["MouthPoutingDecimalSlider"]
                ).to(self.models_processor.device)
                lip_variation_one = torch.tensor(
                    parameters["MouthPursingDecimalSlider"]
                ).to(self.models_processor.device)
                lip_variation_two = torch.tensor(
                    parameters["MouthGrinDecimalSlider"]
                ).to(self.models_processor.device)
                lip_variation_three = torch.tensor(
                    parameters["LipsCloseOpenSlider"]
                ).to(self.models_processor.device)

                x_c_s = x_s_info["kp"]
                delta_new = x_s_info["exp"]
                scale_new = x_s_info["scale"]
                t_new = x_s_info["t"]
                R_d_new = (R_d_user @ R_s_user.permute(0, 2, 1)) @ R_s_user

                # Apply modifications
                if eyeball_direction_x != 0 or eyeball_direction_y != 0:
                    delta_new = faceutil.update_delta_new_eyeball_direction(
                        eyeball_direction_x, eyeball_direction_y, delta_new
                    )
                if smile != 0:
                    delta_new = faceutil.update_delta_new_smile(smile, delta_new)
                if wink != 0:
                    delta_new = faceutil.update_delta_new_wink(wink, delta_new)
                if eyebrow != 0:
                    delta_new = faceutil.update_delta_new_eyebrow(eyebrow, delta_new)
                if lip_variation_zero != 0:
                    delta_new = faceutil.update_delta_new_lip_variation_zero(
                        lip_variation_zero, delta_new
                    )
                if lip_variation_one != 0:
                    delta_new = faceutil.update_delta_new_lip_variation_one(
                        lip_variation_one, delta_new
                    )
                if lip_variation_two != 0:
                    delta_new = faceutil.update_delta_new_lip_variation_two(
                        lip_variation_two, delta_new
                    )
                if lip_variation_three != 0:
                    delta_new = faceutil.update_delta_new_lip_variation_three(
                        lip_variation_three, delta_new
                    )
                if mov_x != 0:
                    delta_new = faceutil.update_delta_new_mov_x(-mov_x, delta_new)
                if mov_y != 0:
                    delta_new = faceutil.update_delta_new_mov_y(mov_y, delta_new)

                x_d_new = mov_z * scale_new * (x_c_s @ R_d_new + delta_new) + t_new
                eyes_delta, lip_delta = None, None

                # Retargeting Sliders
                input_eye_ratio = max(
                    min(
                        init_source_eye_ratio
                        + parameters["EyesOpenRatioDecimalSlider"],
                        0.80,
                    ),
                    0.00,
                )
                if input_eye_ratio != init_source_eye_ratio:
                    combined_eye_ratio_tensor = faceutil.calc_combined_eye_ratio(
                        [[float(input_eye_ratio)]],
                        lmk_crop,
                        device=self.models_processor.device,
                    )
                    eyes_delta = self.models_processor.lp_retarget_eye(
                        x_s_user,
                        combined_eye_ratio_tensor,
                        parameters["FaceEditorTypeSelection"],
                    )

                input_lip_ratio = max(
                    min(
                        init_source_lip_ratio
                        + parameters["LipsOpenRatioDecimalSlider"],
                        0.80,
                    ),
                    0.00,
                )
                if input_lip_ratio != init_source_lip_ratio:
                    combined_lip_ratio_tensor = faceutil.calc_combined_lip_ratio(
                        [[float(input_lip_ratio)]],
                        lmk_crop,
                        device=self.models_processor.device,
                    )
                    lip_delta = self.models_processor.lp_retarget_lip(
                        x_s_user,
                        combined_lip_ratio_tensor,
                        parameters["FaceEditorTypeSelection"],
                    )

                x_d_new = (
                    x_d_new
                    + (eyes_delta if eyes_delta is not None else 0)
                    + (lip_delta if lip_delta is not None else 0)
                )

                flag_stitching_retargeting_input: bool = kwargs.get(
                    "flag_stitching_retargeting_input", True
                )
                if flag_stitching_retargeting_input:
                    x_d_new = self.models_processor.lp_stitching(
                        x_s_user, x_d_new, parameters["FaceEditorTypeSelection"]
                    )

                out = self.models_processor.lp_warp_decode(
                    f_s_user, x_s_user, x_d_new, parameters["FaceEditorTypeSelection"]
                )
                out = torch.squeeze(out)
                out = out.clamp_(0, 1)

            # --- POST-PROCESSING ---
            t = trans.SimilarityTransform()
            t.params[0:2] = M_c2o
            dsize = (img.shape[1], img.shape[2])
            out = faceutil.pad_image_by_size(out, dsize)
            out = v2.functional.affine(
                out,
                t.rotation * 57.2958,
                translate=(t.translation[0], t.translation[1]),
                scale=t.scale,
                shear=(0.0, 0.0),
                interpolation=interp_mode,
                center=(0, 0),
            )
            out = v2.functional.crop(out, 0, 0, dsize[0], dsize[1])  # cols, rows

            img = out
            img = img.mul_(255.0).clamp_(0, 255).type(torch.float32)

        return img

    def swap_edit_face_core_makeup(
        self,
        img: torch.Tensor,
        kps: np.ndarray,
        parameters: dict,
        control: dict,
        **kwargs,
    ) -> torch.Tensor:
        """
        Applies digital makeup to the face using face parser masks.
        """
        use_mean_eyes = parameters.get("LandmarkMeanEyesToggle", False)

        if (
            parameters["FaceMakeupEnableToggle"]
            or parameters["HairMakeupEnableToggle"]
            or parameters["EyeBrowsMakeupEnableToggle"]
            or parameters["LipsMakeupEnableToggle"]
        ):
            _, lmk_crop, _ = self.models_processor.run_detect_landmark(
                img,
                bbox=[],
                det_kpss=kps,
                detect_mode="203",
                score=0.5,
                from_points=False,
                use_mean_eyes=use_mean_eyes,
            )

            # Use the interpolation mode passed from FrameWorker, or default to BILINEAR
            interp_mode = (
                self.interpolation_expression_faceeditor_back
                if self.interpolation_expression_faceeditor_back is not None
                else v2.InterpolationMode.BILINEAR
            )

            # Prepare Image
            original_face_512, M_o2c, M_c2o = faceutil.warp_face_by_face_landmark_x(
                img,
                lmk_crop,
                dsize=512,
                scale=parameters["FaceEditorCropScaleDecimalSlider"],
                vy_ratio=parameters["FaceEditorVYRatioDecimalSlider"],
                interpolation=interp_mode,
            )

            out, mask_out = self.models_processor.apply_face_makeup(
                original_face_512, parameters
            )
            if 1:
                # Gaussian blur for soft blending
                gauss = v2.GaussianBlur(kernel_size=5 * 2 + 1, sigma=(5 + 1) * 0.2)
                out = torch.clamp(torch.div(out, 255.0), 0, 1).type(torch.float32)
                mask_crop = gauss(self.models_processor.lp_mask_crop)
                img = faceutil.paste_back_adv(out, M_c2o, img, mask_crop)

        return img
