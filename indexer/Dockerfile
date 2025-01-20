FROM python:3.11-slim-buster

WORKDIR /usr/src/app

# Install pip first and cache it
RUN pip install --upgrade pip

# Copy only requirements first to leverage cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install and cache huggingface_hub separately
RUN pip install huggingface_hub

# Set args after installations to prevent cache invalidation
ARG EMBEDDING_MODEL_ID
ARG START_INDEXING

# Set the HF cache directory
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface

# Download model - this layer will cache unless EMBEDDING_MODEL_ID changes
RUN huggingface-cli download $EMBEDDING_MODEL_ID --repo-type model --cache-dir $TRANSFORMERS_CACHE

# Copy only necessary files
COPY *.py .
COPY *.json ./

ENV START_INDEXING=${START_INDEXING}
ENV PORT=8000
ENV CURRENT_HOST=0.0.0.0
ENV WORKERS=1

CMD ["sh", "-c", "uvicorn app:app --loop asyncio --reload --workers ${WORKERS} --host $CURRENT_HOST --port $PORT --proxy-headers"]