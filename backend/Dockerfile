FROM ubuntu:22.04 AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"\
    POETRY_VERSION=2.1.0 \
    DEBIAN_FRONTEND=noninteractive

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
ENV PYTHONPATH="${PYSETUP_PATH}"

# Install whisper.cpp dependencies and essential packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-numpy \
    # Essential build dependencies
    gcc \
    g++ \
    python3-dev \
    git \
    build-essential \
    cmake \
    # Audio processing dependencies
    ffmpeg \
    # Requirements for FastAPI app
    curl \
    iproute2 \
    # Boost libraries for ur_rtde
    libboost-all-dev \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Clone and build whisper.cpp from source
WORKDIR /opt
RUN git clone https://github.com/ggml-org/whisper.cpp.git
WORKDIR /opt/whisper.cpp

# Configure, build and install whisper.cpp
RUN cmake -B build && \
    cmake --build build --config Release

# Download the base.en model (142 MiB) - multilingual speech recognition model
# This saves the model to /opt/whisper.cpp/models/ggml-base.en.bin
RUN ./models/download-ggml-model.sh base.en && \
    ls -la models/ggml-base.en.bin && \
    echo "Whisper base.en model successfully downloaded ($(du -h models/ggml-base.en.bin | cut -f1))"

# Clone and build piper TTS
WORKDIR /opt
RUN git clone https://github.com/rhasspy/piper.git

# Clone and build piper-phonemize from source
RUN git clone https://github.com/rhasspy/piper-phonemize.git
WORKDIR /opt/piper-phonemize

# Build piper-phonemize
RUN cmake -B build -DCMAKE_INSTALL_PREFIX=/usr/local && \
    cmake --build build --config Release && \
    cmake --install build

# Copy the built libraries to the piper directory with correct paths
RUN mkdir -p /opt/piper/lib/Linux-$(uname -m)/piper_phonemize && \
    cp -r /usr/local/lib/libpiper_phonemize* /opt/piper/lib/Linux-$(uname -m)/piper_phonemize/ && \
    if [ -d "/usr/local/include/piper_phonemize" ]; then \
    cp -r /usr/local/include/piper_phonemize /opt/piper/lib/Linux-$(uname -m)/piper_phonemize/; \
    else \
    echo "piper_phonemize include directory not found, checking alternatives..."; \
    find /usr/local/include -name "*piper*" -type d || echo "No piper include directories found"; \
    fi

# Now build piper with the locally built phonemize library
WORKDIR /opt/piper
RUN cmake -Bbuild -DCMAKE_INSTALL_PREFIX=/usr/local && \
    cmake --build build --config Release && \
    cmake --install build

# Make sure the libraries are in standard locations
RUN mkdir -p /usr/local/lib/piper_phonemize && \
    cp -r /opt/piper/lib/Linux-$(uname -m)/piper_phonemize/* /usr/local/lib/piper_phonemize/ && \
    ldconfig 2>/dev/null || true

# Clone and build ur_rtde from source
WORKDIR /opt
RUN git clone https://gitlab.com/sdurobotics/ur_rtde.git
WORKDIR /opt/ur_rtde
# Initialize pybind11 submodule for Python bindings
RUN git submodule update --init --recursive
RUN mkdir build && cd build && \
    cmake .. -DPYTHON_BINDINGS=ON -DBUILD_PYTHON_MODULE=ON && \
    make -j4 && \
    make install && \
    ldconfig

# Set environment variables for shared libraries
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib/piper_phonemize:/usr/local/lib/ur_rtde"

# Create user
RUN addgroup --gid 1000 appuser && adduser --uid 1000 --system --ingroup appuser appuser

WORKDIR $PYSETUP_PATH

RUN chown -R appuser /opt
USER appuser

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy project dependency files
COPY --chown=appuser ./pyproject.toml ./poetry.lock ./

# Configure Poetry
RUN poetry install --no-root

# ------------------------------------------------------------------------------------
# 'development' stage installs all dev deps and can be used to develop code
FROM base AS development

# Install dev libs
WORKDIR $PYSETUP_PATH
COPY --chown=appuser ./pyproject.toml ./poetry.lock ./
RUN poetry install --no-root

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
