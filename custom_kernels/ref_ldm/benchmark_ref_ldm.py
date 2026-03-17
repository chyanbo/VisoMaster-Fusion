"""
Benchmark — ReF-LDM custom kernels vs ORT baseline.

Tests three model components separately:
  VAE Encoder  : (1,3,512,512)f32  -> (1,8,64,64)f32
  VAE Decoder  : (1,8,64,64)f32   -> (1,3,512,512)f32
  UNet denoiser: (1,16,64,64)f32  + K/V -> (1,8,64,64)f32

Usage (from repo root):
    .venv\\Scripts\\python custom_kernels\\ref_ldm\\benchmark_ref_ldm.py

Optional env vars:
    ONNX_DIR=model_assets          path to ONNX model files
    WARMUP=50                      warm-up iterations
    ITERS=200                      timed iterations
"""

from __future__ import annotations

import os
import sys
import time
import pathlib

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).parent.parent.parent
ONNX_DIR = pathlib.Path(os.environ.get("ONNX_DIR", ROOT / "model_assets"))
WARMUP = int(os.environ.get("WARMUP", 50))
ITERS = int(os.environ.get("ITERS", 200))

ENC_ONNX = str(ONNX_DIR / "ref_ldm_vae_encoder.onnx")
DEC_ONNX = str(ONNX_DIR / "ref_ldm_vae_decoder.onnx")
UNET_ONNX = str(ONNX_DIR / "ref_ldm_unet_external_kv.onnx")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ms(elapsed_s: float, iters: int) -> float:
    return elapsed_s / iters * 1000.0


def _bench(fn, warmup=WARMUP, iters=ITERS) -> float:
    """Return ms/iter (GPU-timed)."""
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(iters):
        fn()
    torch.cuda.synchronize()
    return _ms(time.perf_counter() - t0, iters)


def _ort_session(onnx_path: str, provider: str = "CUDAExecutionProvider"):
    import onnxruntime as ort

    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(onnx_path, sess_options=opts, providers=[provider])


def _trt_ep_options():
    return {
        "trt_engine_cache_enable": True,
        "trt_engine_cache_path": "tensorrt-engines",
        "trt_timing_cache_enable": True,
        "trt_timing_cache_path": "tensorrt-engines",
        "trt_dump_ep_context_model": True,
        "trt_ep_context_file_path": "tensorrt-engines",
        "trt_layer_norm_fp32_fallback": True,
        "trt_max_workspace_size": 8589934592,
        "trt_builder_optimization_level": 5,
    }


def _ctx_engine_exists(ctx_path) -> bool:
    """Return True if the engine file referenced by the ctx.onnx is present."""
    try:
        import onnx as _onnx

        m = _onnx.load(str(ctx_path))
        for node in m.graph.node:
            if node.op_type == "EPContext":
                for attr in node.attribute:
                    if attr.name == "ep_cache_context":
                        rel = attr.s.decode("utf-8", "replace")
                        # engine path is relative to the ctx file's directory
                        engine_abs = ctx_path.parent / rel
                        return engine_abs.exists()
    except Exception:
        pass
    return False


def _patch_ctx_engine(ctx_path, new_engine_rel: str):
    """Return a temporary ctx.onnx path with ep_cache_context replaced."""
    import onnx as _onnx
    import tempfile
    import pathlib

    m = _onnx.load(str(ctx_path))
    for node in m.graph.node:
        if node.op_type == "EPContext":
            for attr in node.attribute:
                if attr.name == "ep_cache_context":
                    attr.s = new_engine_rel.encode("utf-8")
    tmp = pathlib.Path(tempfile.mktemp(suffix=".onnx"))
    _onnx.save(m, str(tmp))
    return tmp


def _ort_trt_session(onnx_path: str, ctx_name: str):
    """Create an ORT session with TensorRT EP (same config as the application).

    Load strategy (in order):
    1. Pre-compiled _ctx.onnx  — instant if engine file is present.
    2. Engine exists but hash mismatch — patch ctx to point to the right engine.
    3. Rebuild from original ONNX with trt_builder_optimization_level=3 (fast).

    Imports tensorrt first so nvinfer DLLs are in-process before ORT's TRT provider
    DLL tries to resolve them (mirrors models_processor.py startup).
    """
    import onnxruntime as ort
    import os as _os

    # Pre-load nvinfer DLLs — identical to what models_processor.py does at startup.
    try:
        import tensorrt  # noqa: F401  — side-effect: loads nvinfer_10.dll
    except Exception as _e:
        print(f"  [WARN] Could not import tensorrt: {_e}")

    if "TensorrtExecutionProvider" not in ort.get_available_providers():
        return None, "TensorrtExecutionProvider not in ort.get_available_providers()"

    ctx_path = ROOT / "tensorrt-engines" / ctx_name
    engine_dir = ROOT / "tensorrt-engines" / "tensorrt-engines"
    tmp_ctx = None  # track any temp file we create

    if ctx_path.exists() and _ctx_engine_exists(ctx_path):
        load_path = str(ctx_path)  # fast path: engine in place
    else:
        # Try to find a matching engine by probing candidate files in size order
        # (largest engines are more likely to be a complex model like UNet).
        candidates = sorted(
            [f for f in engine_dir.glob("*.engine") if "main_graph" in f.name],
            key=lambda f: f.stat().st_size,
            reverse=True,
        )
        # Exclude engines already claimed by encoder/decoder ctx files
        claimed = set()
        for other_ctx in (ROOT / "tensorrt-engines").glob("*_ctx.onnx"):
            if other_ctx == ctx_path:
                continue
            try:
                import onnx as _o

                _m = _o.load(str(other_ctx))
                for _n in _m.graph.node:
                    if _n.op_type == "EPContext":
                        for _a in _n.attribute:
                            if _a.name == "ep_cache_context":
                                claimed.add(
                                    _a.s.decode("utf-8", "replace").replace("\\", "/")
                                )
            except Exception:
                pass

        load_path = None
        for cand in candidates:
            rel = "tensorrt-engines/" + cand.name
            if rel.replace("/", "\\") in claimed or rel in claimed:
                continue  # already used by another model
            # Patch ctx to point at this candidate and try loading below
            if ctx_path.exists():
                tmp_ctx = _patch_ctx_engine(ctx_path, rel.replace("/", "\\"))
                load_path = str(tmp_ctx)
            break

        if load_path is None:
            # No candidate found — rebuild from ONNX (optimization_level=3 for speed)
            print(
                f"  [INFO] No cached engine for {ctx_name}; building TRT engine "
                f"(level=3, may take several minutes)..."
            )
            load_path = onnx_path

    opts = _trt_ep_options()
    if load_path == onnx_path:
        opts = {**opts, "trt_builder_optimization_level": 3}

    _prev = _os.getcwd()
    _os.chdir(str(ROOT))
    try:
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess = ort.InferenceSession(
            load_path,
            so,
            providers=[
                ("TensorrtExecutionProvider", opts),
                ("CUDAExecutionProvider", {"device_id": "0"}),
                ("CPUExecutionProvider", {}),
            ],
        )
    except Exception as _e:
        if tmp_ctx is not None and load_path == str(tmp_ctx):
            # Candidate engine didn't match — fall back to rebuild
            _os.chdir(_prev)
            tmp_ctx.unlink(missing_ok=True)
            tmp_ctx = None
            print("  [INFO] Candidate engine mismatch; rebuilding (level=3)...")
            opts = {**_trt_ep_options(), "trt_builder_optimization_level": 3}
            _os.chdir(str(ROOT))
            try:
                so2 = ort.SessionOptions()
                so2.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                sess = ort.InferenceSession(
                    onnx_path,
                    so2,
                    providers=[
                        ("TensorrtExecutionProvider", opts),
                        ("CUDAExecutionProvider", {"device_id": "0"}),
                        ("CPUExecutionProvider", {}),
                    ],
                )
            except Exception as _e2:
                return None, str(_e2)
            finally:
                _os.chdir(_prev)
        else:
            return None, str(_e)
    finally:
        _os.chdir(_prev)
        if tmp_ctx is not None:
            tmp_ctx.unlink(missing_ok=True)
    return sess, None


def _print_row(tier, label, ms_val, ref_ms):
    speedup = ref_ms / ms_val if ms_val > 0 else float("nan")
    print(f"  Tier {tier} | {label:<42} | {ms_val:8.2f} ms | {speedup:6.2f}x")


# ---------------------------------------------------------------------------
# VAE Encoder benchmark
# ---------------------------------------------------------------------------
def bench_encoder():
    print("\n=== VAE Encoder (1,3,512,512) -> (1,8,64,64) ===")
    print(f"  warm-up={WARMUP}, iters={ITERS}\n")
    print(f"  {'Tier':<6} | {'Method':<42} | {'ms':>8} | {'speedup':>7}")
    print(f"  {'-' * 6}-+-{'-' * 42}-+-{'-' * 8}-+-{'-' * 7}")

    inp = torch.randn(1, 3, 512, 512, dtype=torch.float32, device="cuda")

    # Tier 0  — ORT FP32 CUDA EP
    sess0 = _ort_session(ENC_ONNX, "CUDAExecutionProvider")
    inp_np = inp.cpu().numpy()
    in_name = sess0.get_inputs()[0].name
    out_name = sess0.get_outputs()[0].name
    t0 = _bench(lambda: sess0.run([out_name], {in_name: inp_np}))
    _print_row("0", "ORT FP32 CUDA EP", t0, t0)

    # Tier 0b — ORT TensorRT EP (same provider config as the application)
    t0b = t0
    sess0b, err0b = _ort_trt_session(ENC_ONNX, "ref_ldm_vae_encoder_ctx.onnx")
    if sess0b is None:
        print(f"  Tier 0b | ORT TensorRT EP — skipped ({err0b})")
    else:
        t0b = _bench(lambda: sess0b.run([out_name], {in_name: inp_np}))
        _print_row("0b", "ORT TensorRT EP FP32 (app default)", t0b, t0)

    # Tier 1  — PyTorch FP32
    sys.path.insert(0, str(ROOT))
    from custom_kernels.ref_ldm.ref_ldm_torch import RefLDMEncoderTorch

    enc_fp32 = (
        RefLDMEncoderTorch.from_onnx(ENC_ONNX, compute_dtype=torch.float32)
        .cuda()
        .eval()
    )
    with torch.no_grad():
        t1 = _bench(lambda: enc_fp32(inp))
    _print_row("1", "PyTorch FP32 pure ops", t1, t0)

    # Tier 2  — PyTorch FP16 + Triton GroupNorm+SiLU
    enc_fp16 = (
        RefLDMEncoderTorch.from_onnx(ENC_ONNX, compute_dtype=torch.float16)
        .cuda()
        .eval()
    )
    with torch.no_grad():
        t2 = _bench(lambda: enc_fp16(inp))
    _print_row("2", "PyTorch FP16 + Triton GroupNorm+SiLU", t2, t0)

    # Tier 3  — FP16 + Triton + CUDA graph
    from custom_kernels.ref_ldm.ref_ldm_torch import build_cuda_graph_runner

    runner = build_cuda_graph_runner(enc_fp16, inp_shape=(1, 3, 512, 512))
    t3 = _bench(lambda: runner(inp))
    _print_row("3", "PyTorch FP16 + Triton + CUDA graph", t3, t0)

    # Tier 4  — FP16 + Triton + CUDA graph + NHWC (channels-last)
    enc_cl = (
        RefLDMEncoderTorch.from_onnx(ENC_ONNX, compute_dtype=torch.float16)
        .cuda()
        .eval()
    )
    enc_cl.to_channels_last()
    runner_cl = build_cuda_graph_runner(enc_cl, inp_shape=(1, 3, 512, 512))
    t4 = _bench(lambda: runner_cl(inp))
    _print_row("4", "FP16 + Triton + CUDA graph + NHWC", t4, t0)

    # Tier 5 — torch.compile + CUDA graph (Linux only)
    # torch.compile + Triton causes a hard native segfault (access violation in
    # libtriton.pyd during Inductor codegen) on Windows — cannot be caught by try/except.
    if sys.platform == "win32":
        print("  Tier 5 | torch.compile — skipped (not supported on Windows)")
    else:
        try:
            enc_c5 = (
                RefLDMEncoderTorch.from_onnx(ENC_ONNX, compute_dtype=torch.float16)
                .cuda()
                .eval()
            )
            enc_c5 = torch.compile(enc_c5, mode="reduce-overhead", fullgraph=False)
            with torch.no_grad():
                for _ in range(5):  # trigger compilation
                    enc_c5(inp)
            runner_c5 = build_cuda_graph_runner(enc_c5, inp_shape=(1, 3, 512, 512))
            t5 = _bench(lambda: runner_c5(inp))
            _print_row("5", "FP16 + Triton + CUDA graph + compile", t5, t0)
        except Exception as e:
            print(f"  Tier 5 | torch.compile — skipped ({type(e).__name__}: {e})")

    print()
    return t0, t0b


# ---------------------------------------------------------------------------
# VAE Decoder benchmark
# ---------------------------------------------------------------------------
def bench_decoder():
    print("\n=== VAE Decoder (1,8,64,64) -> (1,3,512,512) ===")
    print(f"  warm-up={WARMUP}, iters={ITERS}\n")
    print(f"  {'Tier':<6} | {'Method':<42} | {'ms':>8} | {'speedup':>7}")
    print(f"  {'-' * 6}-+-{'-' * 42}-+-{'-' * 8}-+-{'-' * 7}")

    lat = torch.randn(1, 8, 64, 64, dtype=torch.float32, device="cuda")

    # Tier 0  — ORT FP32 CUDA EP
    sess0 = _ort_session(DEC_ONNX, "CUDAExecutionProvider")
    lat_np = lat.cpu().numpy()
    in_name = sess0.get_inputs()[0].name
    out_name = sess0.get_outputs()[0].name
    t0 = _bench(lambda: sess0.run([out_name], {in_name: lat_np}))
    _print_row("0", "ORT FP32 CUDA EP", t0, t0)

    # Tier 0b — ORT TensorRT EP (same provider config as the application)
    t0b = t0
    sess0b, err0b = _ort_trt_session(DEC_ONNX, "ref_ldm_vae_decoder_ctx.onnx")
    if sess0b is None:
        print(f"  Tier 0b | ORT TensorRT EP — skipped ({err0b})")
    else:
        t0b = _bench(lambda: sess0b.run([out_name], {in_name: lat_np}))
        _print_row("0b", "ORT TensorRT EP FP32 (app default)", t0b, t0)

    # Tier 1  — PyTorch FP32
    from custom_kernels.ref_ldm.ref_ldm_torch import RefLDMDecoderTorch

    dec_fp32 = (
        RefLDMDecoderTorch.from_onnx(DEC_ONNX, compute_dtype=torch.float32)
        .cuda()
        .eval()
    )
    with torch.no_grad():
        t1 = _bench(lambda: dec_fp32(lat))
    _print_row("1", "PyTorch FP32 pure ops", t1, t0)

    # Tier 2  — PyTorch FP16 + Triton GroupNorm+SiLU
    dec_fp16 = (
        RefLDMDecoderTorch.from_onnx(DEC_ONNX, compute_dtype=torch.float16)
        .cuda()
        .eval()
    )
    with torch.no_grad():
        t2 = _bench(lambda: dec_fp16(lat))
    _print_row("2", "PyTorch FP16 + Triton GroupNorm+SiLU", t2, t0)

    # Tier 3  — FP16 + Triton + CUDA graph
    from custom_kernels.ref_ldm.ref_ldm_torch import build_cuda_graph_runner

    runner = build_cuda_graph_runner(dec_fp16, inp_shape=(1, 8, 64, 64))
    t3 = _bench(lambda: runner(lat))
    _print_row("3", "PyTorch FP16 + Triton + CUDA graph", t3, t0)

    # Tier 4  — FP16 + Triton + CUDA graph + NHWC (channels-last)
    dec_cl = (
        RefLDMDecoderTorch.from_onnx(DEC_ONNX, compute_dtype=torch.float16)
        .cuda()
        .eval()
    )
    dec_cl.to_channels_last()
    runner_cl = build_cuda_graph_runner(dec_cl, inp_shape=(1, 8, 64, 64))
    t4 = _bench(lambda: runner_cl(lat))
    _print_row("4", "FP16 + Triton + CUDA graph + NHWC", t4, t0)

    # Tier 5 — torch.compile + CUDA graph (Linux only)
    if sys.platform == "win32":
        print("  Tier 5 | torch.compile — skipped (not supported on Windows)")
    else:
        try:
            dec_c5 = (
                RefLDMDecoderTorch.from_onnx(DEC_ONNX, compute_dtype=torch.float16)
                .cuda()
                .eval()
            )
            dec_c5 = torch.compile(dec_c5, mode="reduce-overhead", fullgraph=False)
            with torch.no_grad():
                for _ in range(5):
                    dec_c5(lat)
            runner_c5 = build_cuda_graph_runner(dec_c5, inp_shape=(1, 8, 64, 64))
            t5 = _bench(lambda: runner_c5(lat))
            _print_row("5", "FP16 + Triton + CUDA graph + compile", t5, t0)
        except Exception as e:
            print(f"  Tier 5 | torch.compile — skipped ({type(e).__name__}: {e})")

    print()
    return t0, t0b


# ---------------------------------------------------------------------------
# UNet benchmark
# ---------------------------------------------------------------------------
def _build_dummy_kv_map():
    """Build a representative K/V map for the UNet benchmark.

    UNet: mc=160, mult=(1,2,2,4), nhc=32  ->  n_heads = ch // 32
      Level 1 (32×32, 320ch):  input 4-5,  output 3-5  -> n_heads=10
      Level 2 (16×16, 320ch):  input 7-8,  output 6-8  -> n_heads=10
      Level 3 (8×8,  640ch):   input 10-11, middle, output 0-2 -> n_heads=20
    External seq_len is arbitrary (64 reference tokens used here).
    """
    # (path, n_heads)
    ch_per_head = 32
    seq_len = 64
    attn_blocks = [
        # Level 1 — 320ch -> 10 heads
        ("input_blocks.4.1.attention", 10),
        ("input_blocks.5.1.attention", 10),
        # Level 2 — 320ch -> 10 heads
        ("input_blocks.7.1.attention", 10),
        ("input_blocks.8.1.attention", 10),
        # Level 3 — 640ch -> 20 heads
        ("input_blocks.10.1.attention", 20),
        ("input_blocks.11.1.attention", 20),
        ("middle_block.1.attention", 20),
        ("output_blocks.0.1.attention", 20),
        ("output_blocks.1.1.attention", 20),
        ("output_blocks.2.1.attention", 20),
        # Level 2 (decoder) — 320ch -> 10 heads
        ("output_blocks.3.1.attention", 10),
        ("output_blocks.4.1.attention", 10),
        ("output_blocks.5.1.attention", 10),
    ]
    kv_map = {}
    for path, n_heads in attn_blocks:
        kv_map[path] = {
            "k": torch.randn(
                n_heads, ch_per_head, seq_len, device="cuda", dtype=torch.float32
            ),
            "v": torch.randn(
                n_heads, ch_per_head, seq_len, device="cuda", dtype=torch.float32
            ),
        }
    return kv_map


def bench_unet():
    print("\n=== UNet denoiser (1,16,64,64) + K/V -> (1,8,64,64) ===")
    print(f"  warm-up={WARMUP}, iters={ITERS}\n")
    print(f"  {'Tier':<6} | {'Method':<42} | {'ms':>8} | {'speedup':>7}")
    print(f"  {'-' * 6}-+-{'-' * 42}-+-{'-' * 8}-+-{'-' * 7}")

    x = torch.randn(1, 16, 64, 64, dtype=torch.float32, device="cuda")
    ts = torch.tensor([500], dtype=torch.int64, device="cuda")
    kv_map = _build_dummy_kv_map()

    # Tier 0  — ORT FP32 CUDA EP (simplified: no K/V, baseline timing only)
    sess0 = _ort_session(UNET_ONNX, "CUDAExecutionProvider")
    onnx_inputs = sess0.get_inputs()
    _in_names = [i.name for i in onnx_inputs]

    def _build_ort_feeds():
        feeds = {
            "x_noisy_plus_lq_latent": x.cpu().numpy(),
            "timesteps": ts.cpu().numpy(),
            "is_ref_flag_input": np.array([True], dtype=bool),
            "use_reference_exclusive_path_globally_input": np.array([True], dtype=bool),
        }
        # Zero-fill K/V inputs
        for inp in onnx_inputs:
            if inp.name.endswith("_k_ext") or inp.name.endswith("_v_ext"):
                shape = tuple(
                    d if isinstance(d, int) and d > 0 else 1 for d in inp.shape
                )
                feeds[inp.name] = np.zeros(shape, dtype=np.float32)
        return feeds

    feeds = _build_ort_feeds()
    out_name = sess0.get_outputs()[0].name
    t0 = _bench(lambda: sess0.run([out_name], feeds))
    _print_row("0", "ORT FP32 CUDA EP (no K/V)", t0, t0)

    # Tier 0b — ORT TensorRT EP (same provider config as the application)
    t0b = t0
    sess0b, err0b = _ort_trt_session(UNET_ONNX, "ref_ldm_unet_external_kv_ctx.onnx")
    if sess0b is None:
        print(f"  Tier 0b | ORT TensorRT EP — skipped ({err0b})")
    else:
        t0b = _bench(lambda: sess0b.run([out_name], feeds))
        _print_row("0b", "ORT TensorRT EP FP32 (app default)", t0b, t0)

    # Tier 1  — PyTorch FP32
    from custom_kernels.ref_ldm.ref_ldm_torch import RefLDMUNetTorch

    unet_fp32 = (
        RefLDMUNetTorch.from_onnx(UNET_ONNX, compute_dtype=torch.float32).cuda().eval()
    )
    with torch.no_grad():
        t1 = _bench(lambda: unet_fp32(x, ts, kv_map=kv_map, use_exclusive=True))
    _print_row("1", "PyTorch FP32 pure ops", t1, t0)

    # Tier 2  — PyTorch FP16 + Triton GroupNorm+SiLU (no CUDA graph)
    unet_fp16 = (
        RefLDMUNetTorch.from_onnx(UNET_ONNX, compute_dtype=torch.float16).cuda().eval()
    )
    with torch.no_grad():
        t2 = _bench(lambda: unet_fp16(x, ts, kv_map=kv_map, use_exclusive=True))
    _print_row("2", "PyTorch FP16 + Triton GroupNorm+SiLU", t2, t0)

    # Tier 3  — FP16 + Triton + CUDA graph (static K/V buffers)
    from custom_kernels.ref_ldm.ref_ldm_torch import build_unet_cuda_graph_runner

    unet_runner = build_unet_cuda_graph_runner(
        unet_fp16,
        x_shape=(1, 16, 64, 64),
        ts_example=ts,
        kv_map_template=kv_map,
        use_exclusive=True,
    )
    t3 = _bench(lambda: unet_runner(x, ts, kv_map, use_exclusive=True))
    _print_row("3", "FP16 + Triton + CUDA graph", t3, t0)

    # Tier 4  — FP16 + Triton + CUDA graph + NHWC (channels-last Conv2d)
    unet_cl = (
        RefLDMUNetTorch.from_onnx(UNET_ONNX, compute_dtype=torch.float16).cuda().eval()
    )
    unet_cl.to_channels_last()
    unet_cl_runner = build_unet_cuda_graph_runner(
        unet_cl,
        x_shape=(1, 16, 64, 64),
        ts_example=ts,
        kv_map_template=kv_map,
        use_exclusive=True,
    )
    t4 = _bench(lambda: unet_cl_runner(x, ts, kv_map, use_exclusive=True))
    _print_row("4", "FP16 + Triton + CUDA graph + NHWC", t4, t0)

    # Tier 5 — torch.compile + CUDA graph (Linux only)
    if sys.platform == "win32":
        print("  Tier 5 | torch.compile — skipped (not supported on Windows)")
    else:
        try:
            unet_c5 = (
                RefLDMUNetTorch.from_onnx(UNET_ONNX, compute_dtype=torch.float16)
                .cuda()
                .eval()
            )
            unet_c5 = torch.compile(unet_c5, mode="reduce-overhead", fullgraph=False)
            unet_c5_runner = build_unet_cuda_graph_runner(
                unet_c5,
                x_shape=(1, 16, 64, 64),
                ts_example=ts,
                kv_map_template=kv_map,
                use_exclusive=True,
            )
            t5 = _bench(lambda: unet_c5_runner(x, ts, kv_map, use_exclusive=True))
            _print_row("5", "FP16 + Triton + CUDA graph + compile", t5, t0)
        except Exception as e:
            print(f"  Tier 5 | torch.compile — skipped ({type(e).__name__}: {e})")

    print()
    return t0, t0b


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not torch.cuda.is_available():
        print("ERROR: CUDA not available.")
        sys.exit(1)

    dev = torch.cuda.get_device_name(0)
    print(f"\nDevice: {dev}")
    print(f"PyTorch: {torch.__version__}")
    try:
        import triton

        print(f"Triton:  {triton.__version__}")
    except ImportError:
        print("Triton:  not available (FP32 fallback will be used)")
    try:
        import onnxruntime as ort

        print(f"ORT:     {ort.__version__}")
    except ImportError:
        print("ORT:     not available (skipping Tier 0/0b)")
        sys.exit(1)

    # Check ONNX files exist
    for path, name in [
        (ENC_ONNX, "VAE encoder"),
        (DEC_ONNX, "VAE decoder"),
        (UNET_ONNX, "UNet"),
    ]:
        if not pathlib.Path(path).exists():
            print(f"ERROR: {name} ONNX not found: {path}")
            sys.exit(1)

    bench_encoder()
    bench_decoder()
    bench_unet()
