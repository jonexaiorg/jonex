#!/usr/bin/env python3

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

    cache_dir = "/root/.cache/whisper"
    model_file = os.path.join(cache_dir, f"{model_name}.pt")
    if os.path.isfile(model_file):
        print(f"[1/3] Whisper 模型已存在，跳过: {model_file}")
        return

    print(f"[1/3] 下载 Whisper 模型: {model_name}...")
    import whisper
    whisper.load_model(model_name)
    print(f"  Whisper {model_name} 就绪")


def _mineru_cache_path(model_id: str, source: str) -> str:

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

    model_id = "opendatalab/MinerU2.5-Pro-2605-1.2B"
    source = (
        os.environ.get("MINERU_MODEL_SOURCE")
        or os.environ.get("MINERU_SOURCE")
        or "modelscope"
    )
    cache_path = _mineru_cache_path(model_id, source)

    if os.path.isdir(cache_path) and any(Path(cache_path).iterdir()):
        print(f"[2/3] MinerU 模型已存在，跳过下载: {cache_path}")
        return

    if source == "modelscope":
        print(f"[2/3] 通过 ModelScope 下载 MinerU 模型: {model_id}")
        os.environ.setdefault("MODELSCOPE_CACHE", "/root/.cache/modelscope")
        from modelscope.hub.snapshot_download import snapshot_download

        model_dir = snapshot_download(
            model_id,
            cache_dir=os.environ["MODELSCOPE_CACHE"],
        )
    else:
        print(f"[2/3] 通过 HuggingFace 镜像下载 MinerU 模型: {model_id}")
        from huggingface_hub import snapshot_download

        model_dir = snapshot_download(
            repo_id=model_id,
            cache_dir=os.environ["HF_HUB_CACHE"],
        )
    print(f"  下载到: {model_dir}")
    print(f"  MinerU 模型就绪")


def warmup_paddlex() -> None:

    print("[3/3] 预加载 PaddleX OCR 模型...")
    try:
        import paddlex
        _ = paddlex.create_model("PP-LCNet_x1_0_doc_ori")
        print("  PaddleX OCR 模型就绪")
    except Exception as e:
        print(f"  [INFO] PaddleX warmup skipped: {e}")


def _create_minimal_pdf(path: str) -> None:

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(path, pagesize=A4)
    c.drawString(100, 750, "MinerU Warmup Document")
    c.drawString(100, 730, "This is a minimal PDF to trigger model downloads.")
    c.save()


def show_cache_size() -> None:
    print("\n模型缓存大小:")
    for d in CACHE_DIRS:
        if os.path.isdir(d):
            total = sum(
                f.stat().st_size for f in Path(d).rglob("*") if f.is_file()
            )
            print(f"  {d}: {total / 1024**3:.2f} GB")
        else:
            print(f"  {d}: (not created)")


if __name__ == "__main__":
    print("=== atomic-rag 模型预下载 ===\n")
    download_whisper("base")
    download_mineru_models()
    warmup_paddlex()
    show_cache_size()
    print("\n=== 模型预下载完成 ===")
