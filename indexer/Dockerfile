FROM python:3.9-slim

# Install build dependencies and clean up in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Install Python packages in one layer
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8000 \
    CURRENT_HOST=0.0.0.0 \
    WORKERS=1

ARG START_INDEXING
ARG CHUNK_SIZE
ARG CHUNK_OVERLAP
ARG CHUNK_STRATEGY
ARG TOP_K=3
ARG EMBEDDING_MODEL_ID
ARG RERANKER_MODEL

ENV START_INDEXING=${START_INDEXING} \
    CHUNK_SIZE=${CHUNK_SIZE} \
    CHUNK_OVERLAP=${CHUNK_OVERLAP} \
    CHUNK_STRATEGY=${CHUNK_STRATEGY} \
    TOP_K=${TOP_K}

# Download models during image build
RUN pip install --no-cache-dir huggingface_hub && \
    python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('${EMBEDDING_MODEL_ID}', repo_type='model'); \
    snapshot_download('${RERANKER_MODEL}', repo_type='model')"

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Environment variables:"\n\
echo "TOP_K=$TOP_K"\n\
echo "START_INDEXING=$START_INDEXING"\n\
echo "CHUNK_SIZE=$CHUNK_SIZE"\n\
echo "CHUNK_OVERLAP=$CHUNK_OVERLAP"\n\
if python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then\n\
    echo "GPU detected, using CUDA"\n\
    export DEVICE="cuda"\n\
else\n\
    echo "No GPU detected, using CPU"\n\
    export DEVICE="cpu"\n\
fi\n\
uvicorn app:app --loop asyncio --reload --workers ${WORKERS} --host $CURRENT_HOST --port $PORT --proxy-headers' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]