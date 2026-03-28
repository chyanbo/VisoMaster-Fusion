from types import SimpleNamespace

from app.ui.widgets.ui_workers import IssueScanWorker
from app.ui.widgets.actions.video_control_actions import _handle_issue_scan_progress


def test_issue_scan_worker_progress_emits_live_fps(monkeypatch):
    main_window = SimpleNamespace(
        control={},
        parameters={},
        target_faces={},
        parameter_widgets={},
        videoSeekSlider=SimpleNamespace(value=lambda: 0),
        video_processor=SimpleNamespace(
            _get_issue_scan_ranges=lambda: [(0, 2)],
            describe_issue_scan_scope=lambda _ranges: "Scanning 1 marked range",
            _get_target_input_height=lambda: 256,
            prepare_issue_scan_target_faces_snapshot=lambda *_args, **_kwargs: {},
            scan_issue_frames=None,
        ),
    )

    def fake_scan_issue_frames(**kwargs):
        progress_callback = kwargs["progress_callback"]
        progress_callback(1, 3, 10)
        progress_callback(2, 3, 11)
        progress_callback(3, 3, 12)
        return {
            "issue_frames_by_face": {},
            "frames_scanned": 3,
            "faces_with_issues": 0,
        }

    main_window.video_processor.scan_issue_frames = fake_scan_issue_frames
    worker = IssueScanWorker(main_window)
    emitted = []
    completed = []
    monotonic_values = iter([10.0, 10.5, 11.0, 11.5, 12.0])

    monkeypatch.setattr(
        "app.ui.widgets.ui_workers.time.monotonic",
        lambda: next(monotonic_values),
    )

    worker.progress.connect(
        lambda processed, total, frame_number, scan_fps: emitted.append(
            (processed, total, frame_number, scan_fps)
        )
    )
    worker.completed.connect(
        lambda issue_frames_by_face, frames_scanned, faces_with_issues, scope_text, elapsed_seconds: (
            completed.append(
                (
                    issue_frames_by_face,
                    frames_scanned,
                    faces_with_issues,
                    scope_text,
                    elapsed_seconds,
                )
            )
        )
    )

    worker.run()

    assert emitted == [
        (1, 3, 10, 2.0),
        (2, 3, 11, 2.0),
        (3, 3, 12, 2.0),
    ]
    assert completed == [({}, 3, 0, "Scanning 1 marked range", 2.0)]


def test_issue_scan_worker_passes_control_defaults_snapshot():
    control_widget = SimpleNamespace(default_value="default-control")
    main_window = SimpleNamespace(
        control={"ControlA": "live-control"},
        parameters={},
        target_faces={},
        parameter_widgets={"ControlA": control_widget, "IgnoredWidget": control_widget},
        videoSeekSlider=SimpleNamespace(value=lambda: 0),
        video_processor=SimpleNamespace(
            _get_issue_scan_ranges=lambda: [(0, 0)],
            describe_issue_scan_scope=lambda _ranges: "Scanning 1 marked range",
            _get_target_input_height=lambda: 256,
            prepare_issue_scan_target_faces_snapshot=lambda *_args, **_kwargs: {},
            scan_issue_frames=None,
        ),
    )
    captured = {}

    def fake_scan_issue_frames(**kwargs):
        captured["control_defaults_snapshot"] = kwargs["control_defaults_snapshot"]
        return {
            "issue_frames_by_face": {},
            "frames_scanned": 1,
            "faces_with_issues": 0,
        }

    main_window.video_processor.scan_issue_frames = fake_scan_issue_frames

    worker = IssueScanWorker(main_window)
    worker.run()

    assert captured["control_defaults_snapshot"] == {"ControlA": "default-control"}


def test_issue_scan_worker_preserves_explicitly_empty_snapshots():
    main_window = SimpleNamespace(
        control={},
        parameters={},
        target_faces={},
        parameter_widgets={},
        videoSeekSlider=SimpleNamespace(value=lambda: 0),
        video_processor=SimpleNamespace(
            _get_issue_scan_ranges=lambda: [(0, 0)],
            describe_issue_scan_scope=lambda _ranges: "Scanning 1 marked range",
            _get_target_input_height=lambda: 256,
            prepare_issue_scan_target_faces_snapshot=lambda *_args, **_kwargs: {},
            scan_issue_frames=None,
        ),
    )
    captured = {}

    def fake_scan_issue_frames(**kwargs):
        captured["base_control"] = kwargs["base_control"]
        captured["base_params"] = kwargs["base_params"]
        captured["target_faces_snapshot"] = kwargs["target_faces_snapshot"]
        captured["control_defaults_snapshot"] = kwargs["control_defaults_snapshot"]
        return {
            "issue_frames_by_face": {},
            "frames_scanned": 1,
            "faces_with_issues": 0,
        }

    main_window.video_processor.scan_issue_frames = fake_scan_issue_frames

    worker = IssueScanWorker(main_window)
    worker.run()

    assert captured == {
        "base_control": {},
        "base_params": {},
        "target_faces_snapshot": {},
        "control_defaults_snapshot": {},
    }


def test_issue_scan_worker_passes_plain_target_face_snapshot_without_widget_methods():
    control_widget = SimpleNamespace(default_value="default-control")
    captured = {}

    class _TargetFaceWithoutEmbeddingAccess:
        def __init__(self):
            self.face_id = "face_1"
            self.cropped_face = None

        def get_embedding(self, _recognition_model):
            raise AssertionError(
                "IssueScanWorker should not call target-face widget methods"
            )

    def fake_prepare_issue_scan_target_faces_snapshot(*_args, **_kwargs):
        return {
            "face_1": {
                "face_id": "face_1",
                "embeddings_by_model": {
                    "arcface_128": {
                        "Opal": "prepared-embedding",
                    }
                },
            }
        }

    main_window = SimpleNamespace(
        control={"ControlA": "live-control"},
        parameters={},
        target_faces={"face_1": _TargetFaceWithoutEmbeddingAccess()},
        parameter_widgets={"ControlA": control_widget},
        videoSeekSlider=SimpleNamespace(value=lambda: 0),
        video_processor=SimpleNamespace(
            _get_issue_scan_ranges=lambda: [(0, 0)],
            describe_issue_scan_scope=lambda _ranges: "Scanning 1 marked range",
            _get_target_input_height=lambda: 256,
            prepare_issue_scan_target_faces_snapshot=fake_prepare_issue_scan_target_faces_snapshot,
            scan_issue_frames=None,
        ),
    )

    def fake_scan_issue_frames(**kwargs):
        captured["target_faces_snapshot"] = kwargs["target_faces_snapshot"]
        return {
            "issue_frames_by_face": {},
            "frames_scanned": 1,
            "faces_with_issues": 0,
        }

    main_window.video_processor.scan_issue_frames = fake_scan_issue_frames

    worker = IssueScanWorker(main_window)
    worker.run()

    assert captured["target_faces_snapshot"] == {
        "face_1": {
            "face_id": "face_1",
            "embeddings_by_model": {
                "arcface_128": {
                    "Opal": "prepared-embedding",
                }
            },
        }
    }


def test_handle_issue_scan_progress_updates_dialog_label_with_fps():
    captured = {}
    dialog = SimpleNamespace(
        setMaximum=lambda value: captured.setdefault("maximum", value),
        setValue=lambda value: captured.setdefault("value", value),
        setLabelText=lambda text: captured.setdefault("label", text),
    )
    main_window = SimpleNamespace(scan_progress_dialog=dialog)

    _handle_issue_scan_progress(
        main_window,
        "Scanning 2 marked ranges",
        12,
        40,
        345,
        7.25,
    )

    assert captured["maximum"] == 40
    assert captured["value"] == 12
    assert captured["label"] == "Scanning 2 marked ranges\n12/40 processed | FPS: 7.2"
