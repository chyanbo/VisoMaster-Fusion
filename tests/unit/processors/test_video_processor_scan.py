from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from app.processors.video_processor import VideoProcessor


class _DummyCapture:
    def isOpened(self):
        return True

    def set(self, *_args, **_kwargs):
        return True


def test_scan_issue_frames_restores_dense_smoothing_state():
    processor = VideoProcessor.__new__(VideoProcessor)
    processor.media_path = "dummy.mp4"
    processor.media_rotation = 0
    processor.fps = 30.0
    processor.current_frame_number = 0
    processor.last_detected_faces = [{"id": 1}]
    processor._smoothed_kps = {1: np.array([[1.0, 2.0]], dtype=np.float32)}
    processor._smoothed_dense_kps = {1: np.array([[3.0, 4.0]], dtype=np.float32)}
    processor.last_detected_faces = [{"id": 1}]
    processor.main_window = SimpleNamespace(
        control={},
        parameters={},
        target_faces={},
        dropped_frames=set(),
        videoSeekSlider=SimpleNamespace(value=lambda: 7),
    )
    processor._get_target_input_height = lambda: 256

    with (
        patch(
            "app.processors.video_processor.cv2.VideoCapture",
            return_value=_DummyCapture(),
        ),
        patch("app.processors.video_processor.misc_helpers.release_capture"),
    ):
        result = processor.scan_issue_frames(
            scan_ranges=[(1, 0)],
            base_control={},
            base_params={},
            target_faces_snapshot={},
            reset_frame_number=3,
        )

    assert result == {
        "issue_frames_by_face": {},
        "frames_scanned": 0,
        "faces_with_issues": 0,
    }
    np.testing.assert_array_equal(
        processor._smoothed_dense_kps[1], np.array([[3.0, 4.0]], dtype=np.float32)
    )
    np.testing.assert_array_equal(
        processor._smoothed_kps[1], np.array([[1.0, 2.0]], dtype=np.float32)
    )
    assert processor.last_detected_faces == [{"id": 1}]
    assert processor.current_frame_number == 3


def test_describe_issue_scan_scope_uses_normalized_effective_ranges():
    processor = VideoProcessor.__new__(VideoProcessor)
    processor.max_frame_number = 100
    processor.main_window = SimpleNamespace(
        job_marker_pairs=[(20, 30), (10, 25), (40, None)]
    )

    scope_text = processor.describe_issue_scan_scope([(10, 30), (40, 100)])

    assert scope_text == "Scanning 1 marked range and record start frame 40 to end"


def test_describe_issue_scan_scope_uses_raw_open_start_when_ranges_merge():
    processor = VideoProcessor.__new__(VideoProcessor)
    processor.max_frame_number = 100
    processor.main_window = SimpleNamespace(job_marker_pairs=[(10, 30), (20, None)])

    scope_text = processor.describe_issue_scan_scope([(10, 100)])

    assert scope_text == "Scanning 1 marked range and record start frame 20 to end"
