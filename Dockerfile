FROM python:3.12-slim

# System libraries needed by the Rust compiler and the plotters crate (font rendering)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libfontconfig1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain (non-interactive, default profile)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir numpy matplotlib && pip install --no-cache-dir -e python/

# Build all Rust binaries in release mode
RUN cd rust && cargo build --release

# Default to an interactive shell — override for one-shot runs
CMD ["/bin/bash"]
