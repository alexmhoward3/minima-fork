FROM python:3.9-slim

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y git

ARG EMBEDDING_MODEL_ID
ARG START_INDEXING
ARG RERANKER_MODEL
ARG CHUNK_SIZE
ARG CHUNK_OVERLAP
ARG CHUNK_STRATEGY

RUN pip install huggingface_hub
RUN huggingface-cli download $EMBEDDING_MODEL_ID --repo-type model
RUN huggingface-cli download $RERANKER_MODEL --repo-type model

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV START_INDEXING=${START_INDEXING}
RUN echo "START_INDEXING is $START_INDEXING"

ENV CHUNK_SIZE=${CHUNK_SIZE}
ENV CHUNK_OVERLAP=${CHUNK_OVERLAP}
ENV CHUNK_STRATEGY=${CHUNK_STRATEGY}

ENV PORT=8000
ENV CURRENT_HOST=0.0.0.0
ENV WORKERS=1

# Create entrypoint script
RUN echo '#!/bin/bash\n\
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
