FROM ubuntu:24.04 AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv" \
    DEBIAN_FRONTEND=noninteractive

ENV PATH="$VENV_PATH/bin:$PATH"
ENV PYTHONPATH="${PYSETUP_PATH}"

# Install essential packages for Python whisper, piper, and beeai
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    # Build dependencies for Python packages
    gcc \
    g++ \
    git \
    build-essential \
    # Audio processing dependencies for whisper and piper
    ffmpeg \
    # Additional libraries that may be needed
    libasound2-dev \
    portaudio19-dev \
    # Requirements for FastAPI app
    curl \
    # CA certificates for HTTPS connections
    ca-certificates \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates



# Create user and home directory
RUN useradd --uid 1001 --system --create-home --shell /bin/bash appuser

WORKDIR $PYSETUP_PATH

RUN chown -R appuser /opt
USER appuser

# Set home directory for appuser
ENV HOME=/home/appuser

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/appuser/.local/bin:$PATH"

# Copy project dependency files
COPY --chown=appuser ./pyproject.toml ./

# Generate lock file and install dependencies using uv
RUN uv lock && uv sync --no-install-project

# ------------------------------------------------------------------------------------
# 'development' stage installs all dev deps and can be used to develop code
FROM base AS development

# Install dev libs
WORKDIR $PYSETUP_PATH
COPY --chown=appuser ./pyproject.toml ./
RUN uv lock && uv sync --no-install-project --group dev

WORKDIR /home/appuser

COPY --chown=appuser . .
RUN chmod +x scripts/*

EXPOSE 8009
ENTRYPOINT ["/home/appuser/scripts/docker-entrypoint.sh"]
CMD ["python3", "-m", "app.main"]

# ------------------------------------------------------------------------------------
# 'release' stage uses the clean 'base' stage and copies
# in only our runtime deps that were installed in the 'base'
FROM base AS release

WORKDIR /home/appuser

COPY --chown=appuser . .
RUN chmod +x scripts/*

EXPOSE 8009
ENTRYPOINT ["/home/appuser/scripts/docker-entrypoint.sh"]
CMD ["python3", "-m", "app.main"]
