FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Set CUDA environment variables
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility
ENV CUDA_LAUNCH_BLOCKING=1

WORKDIR /usr/src/app
RUN pip install --upgrade pip

ARG EMBEDDING_MODEL_ID
ARG START_INDEXING

RUN pip install huggingface_hub
RUN huggingface-cli download $EMBEDDING_MODEL_ID --repo-type model

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV START_INDEXING=${START_INDEXING}
RUN echo "START_INDEXING is $START_INDEXING"

ENV PORT 8000
ENV CURRENT_HOST 0.0.0.0
ENV WORKERS 1

CMD ["sh", "-c", "uvicorn app:app --loop asyncio --reload --workers ${WORKERS} --host $CURRENT_HOST --port $PORT --proxy-headers"]
