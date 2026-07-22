#!/usr/bin/env python3
"""
Pre-download whisper + mineru models into the image to avoid runtime waiting.

Cache paths:
  whisper  -> /root/.cache/whisper/
  mineru   -> /root/.cache/modelscope/ + /root/.cache/huggingface/
"""
import os
from pathlib import Path

CACHE_DIRS = [
    "/root/.cache/whisper",
    "/root/.cache/modelscope",
    "/root/.cache/huggingface",
    "/root/.cache/torch",
    "/root/.cache/mineru",
]

os.makedirs("/root/.cache", exist_ok=True)
os.makedirs("/root/.cache/huggingface", exist_ok=True)
os.environ["MODELSCOPE_CACHE"] = "/root/.cache/modelscope"
os.environ["HF_HOME"] = "/root/.cache/huggingface"
os.environ["HF_HUB_CACHE"] = "/root/.cache/huggingface"
os.environ["TORCH_HOME"] = "/root/.cache/torch"

def download_whisper(model_name: str = "base") -> None:
    """Download whisper model (skip if cache exists)"""
    cache_dir = "/root/.cache/whisper"
    model_file = os.path.join(cache_dir, f"{model_name}.pt")
    if os.path.isfile(model_file):
        print(f"[1/3] Whisper model already exists, skipping: {model_file}")
        return

    print(f"[1/3] Downloading Whisper model: {model_name}...")
    import whisper
    whisper.load_model(model_name)
    print(f"  Whisper {model_name} ready")

def _mineru_cache_path(model_id: str, source: str) -> str:
    """Return the expected path of the MinerU model in cache (used to check if it has been downloaded)"""
    if source == "modelscope":
        cache_root = os.environ.get("MODELSCOPE_CACHE", "/root/.cache/modelscope")
        return os.path.join(cache_root, model_id)
    else:
        cache_root = os.environ.get("HF_HUB_CACHE", "/root/.cache/huggingface")

        return os.path.join(
            cache_root,
            f"models--{model_id.replace('/', '--')}",
            "snapshots",
        )

def download_mineru_models() -> None:
    """Download MinerU VLM model (skip if cache exists), select download source based on MINERU_SOURCE"""
    model_id = "opendatalab/MinerU2.5-Pro-2605-1.2B"
    source = os.environ.get("MINERU_SOURCE", "huggingface")
    cache_path = _mineru_cache_path(model_id, source)

    if os.path.isdir(cache_path) and any(Path(cache_path).iterdir()):
        print(f"[2/3] MinerU model already exists, skipping download: {cache_path}")
        return

    if source == "modelscope":
        print(f"[2/3] Downloading MinerU model via ModelScope: {model_id}")
        os.environ.setdefault("MODELSCOPE_CACHE", "/root/.cache/modelscope")
        from modelscope.hub.snapshot_download import snapshot_download

        model_dir = snapshot_download(
            model_id,
            cache_dir=os.environ["MODELSCOPE_CACHE"],
        )
    else:
        print(f"[2/3] Downloading MinerU model via HuggingFace mirror: {model_id}")
        from huggingface_hub import snapshot_download

        model_dir = snapshot_download(
            repo_id=model_id,
            cache_dir=os.environ["HF_HUB_CACHE"],
        )
    print(f"  Downloaded to: {model_dir}")
    print(f"  MinerU model ready")

def warmup_paddlex() -> None:
    """Pre-load paddlex OCR model (will be used by docling)"""
    print("[3/3] Pre-loading PaddleX OCR model...")
    try:
        import paddlex
        _ = paddlex.create_model("PP-LCNet_x1_0_doc_ori")
        print("  PaddleX OCR model ready")
    except Exception as e:
        print(f"  [INFO] PaddleX warmup skipped: {e}")

def _create_minimal_pdf(path: str) -> None:
    """Generate a minimal single-page PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(path, pagesize=A4)
    c.drawString(100, 750, "MinerU Warmup Document")
    c.drawString(100, 730, "This is a minimal PDF to trigger model downloads.")
    c.save()

def show_cache_size() -> None:
    print("\nModel cache size:")
    for d in CACHE_DIRS:
        if os.path.isdir(d):
            total = sum(
                f.stat().st_size for f in Path(d).rglob("*") if f.is_file()
            )
            print(f"  {d}: {total / 1024**3:.2f} GB")
        else:
            print(f"  {d}: (not created)")

if __name__ == "__main__":
    print("=== atomic-rag model pre-download ===\n")
    download_whisper("base")
    download_mineru_models()
    warmup_paddlex()
    show_cache_size()
    print("\n=== Model pre-download completed ===")
