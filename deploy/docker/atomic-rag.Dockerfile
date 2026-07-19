

















FROM python:3.12.13-slim AS base

WORKDIR /app


RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone


RUN sed -i 's|^URIs: http://deb.debian.org/debian|URIs: http://mirrors.cloud.tencent.com/debian|' /etc/apt/sources.list.d/debian.sources
RUN sed -i 's|^URIs: http://deb.debian.org/debian-security|URIs: http://mirrors.cloud.tencent.com/debian-security|' /etc/apt/sources.list.d/debian.sources


RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    ffmpeg \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    fonts-wqy-microhei \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*


RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com




RUN pip config set global.timeout 300 \
    && pip config set global.retries 10


ARG MINERU_SOURCE=modelscope



ARG RAG_PROFILE=full


ENV HF_ENDPOINT=https://hf-mirror.com \
    HF_HOME=/root/.cache/huggingface \
    HF_HUB_CACHE=/root/.cache/huggingface \
    MODELSCOPE_CACHE=/root/.cache/modelscope \
    TORCH_HOME=/root/.cache/torch \
    PYTHONPATH=/app \
    CAPABILITY_NAME=rag.lightrag \
    CAPABILITY_KIND=atomic \
    MINERU_SOURCE=${MINERU_SOURCE} \
    MINERU_MODEL_SOURCE=${MINERU_SOURCE}






COPY Reference/Rag-anything/ /opt/raganything/

RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "$RAG_PROFILE" = "slim" ]; then \
      echo "[RAG_PROFILE=slim] 安装精简依赖（online/selfhost，无 torch/mineru）"; \
      pip install -e "/opt/raganything[image,text]"; \
    else \
      echo "[RAG_PROFILE=full] 安装完整依赖（含本地 mineru CLI 与音视频 ASR）"; \
      pip install -e "/opt/raganything[all,local]"; \
    fi


COPY requirements.txt /tmp/requirements-base.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-base.txt


COPY deploy/docker/atomic-rag-requirements.txt /tmp/requirements-rag.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-rag.txt



RUN --mount=type=cache,target=/root/.cache/pip \
    pip install 'pydantic>=2.0,<3.0' pydantic-settings


ARG SKIP_MODEL_DOWNLOAD=true
COPY deploy/docker/download_models.py /tmp/download_models.py
RUN --mount=type=cache,target=/root/.cache/whisper \
    --mount=type=cache,target=/root/.cache/huggingface \
    --mount=type=cache,target=/root/.cache/modelscope \
    --mount=type=cache,target=/root/.cache/torch \
    if [ "$SKIP_MODEL_DOWNLOAD" != "true" ]; then \
      python /tmp/download_models.py && rm /tmp/download_models.py; \
    else \
      echo "[SKIP] 模型预下载跳过"; \
      rm -f /tmp/download_models.py; \
    fi





RUN --mount=type=bind,target=/build-context \
    missing=""; \
    if [ ! -f /build-context/jonex_core/__init__.py ]; then \
      missing="${missing} jonex_core/__init__.py"; \
    fi; \
    if [ ! -f /build-context/deploy/start_capability.py ]; then \
      missing="${missing} deploy/start_capability.py"; \
    fi; \
    if [ -n "${missing}" ]; then \
      echo "[ERROR] 构建上下文缺失平台源码文件，终止构建：${missing}" >&2; \
      echo "[ERROR] 请在仓库根目录（构建上下文）下确认上述文件存在后重试。" >&2; \
      exit 1; \
    fi; \
    echo "[OK] 平台源码校验通过：jonex_core/、deploy/start_capability.py"


RUN mkdir -p /app/output /app/rag_storage
COPY jonex_core/ /app/jonex_core/
COPY deploy/start_capability.py /app/

EXPOSE 8000


CMD ["python", "start_capability.py"]
