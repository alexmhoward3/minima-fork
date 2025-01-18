FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /usr/src/app

# Install system dependencies including Rust
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && . $HOME/.cargo/env

RUN mkdir -p /usr/src/app/local_files

ARG EMBEDDING_MODEL_ID
ARG EMBEDDING_SIZE
ARG START_INDEXING
ARG RERANKER_MODEL
ARG CHUNK_SIZE
ARG CHUNK_OVERLAP

# Download models
RUN pip install huggingface_hub
RUN huggingface-cli download $EMBEDDING_MODEL_ID --repo-type model
RUN huggingface-cli download $RERANKER_MODEL --repo-type model

# Install Python dependencies
COPY requirements.txt .
ENV PATH="/root/.cargo/bin:${PATH}"
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables
ENV EMBEDDING_MODEL_ID=${EMBEDDING_MODEL_ID}
ENV EMBEDDING_SIZE=${EMBEDDING_SIZE}
ENV START_INDEXING=${START_INDEXING}
ENV CHUNK_SIZE=${CHUNK_SIZE}
ENV CHUNK_OVERLAP=${CHUNK_OVERLAP}

RUN echo "EMBEDDING_MODEL_ID is $EMBEDDING_MODEL_ID"
RUN echo "EMBEDDING_SIZE is $EMBEDDING_SIZE"
RUN echo "START_INDEXING is $START_INDEXING"

ENV PORT 8000
ENV CURRENT_HOST 0.0.0.0
ENV WORKERS 1

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]