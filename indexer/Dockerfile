FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y git

ARG EMBEDDING_MODEL_ID
ARG START_INDEXING
ARG RERANKER_MODEL
ARG CHUNK_SIZE
ARG CHUNK_OVERLAP

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

ENV PORT 8000
ENV CURRENT_HOST 0.0.0.0
ENV WORKERS 1

CMD ["sh", "-c", "uvicorn app:app --loop asyncio --reload --workers ${WORKERS} --host $CURRENT_HOST --port $PORT --proxy-headers"]
