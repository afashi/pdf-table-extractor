# 阶段1：构建基础镜像
FROM python:3.12-slim as builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 优化构建过程：合并层和清理
RUN apt-get update -qqy && \
    apt-get install -qqy --no-install-recommends \
    build-essential libpq-dev && \
    pip install --no-cache-dir uv && \
    uv venv /opt/venv

# 精确复制依赖文件
COPY requirements.txt pyproject.toml ./

# 使用缓存安装依赖
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ -f pyproject.toml ]; then \
        uv pip install --no-cache-dir .; \
    elif [ -f requirements.txt ]; then \
        uv pip install --no-cache-dir -r requirements.txt; \
    else \
        echo "ERROR: No dependencies file found" >&2 && exit 1; \
    fi && \
    # 清理构建依赖
    apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 阶段2：生产镜像
FROM python:3.12-slim as runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONHASHSEED=random

# 设置工作目录和权限
WORKDIR /app
RUN groupadd -r appgroup && \
    useradd --no-log-init -r -g appgroup appuser && \
    mkdir -p /app/{logs,static} && \
    chown -R appuser:appgroup /app

# 复制虚拟环境
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# 最后复制应用代码以利用缓存
COPY --chown=appuser:appgroup ./src ./src
# 考虑移除.env，改用环境变量注入
# COPY --chown=appuser:appgroup ./.env ./

# 设置健康检查（需要curl）
USER root
RUN apt-get update -qqy && \
    apt-get install -qqy --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
USER appuser

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]