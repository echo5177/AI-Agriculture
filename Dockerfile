# ==============================================================
# Smart Farm AI Engine — Multi-stage Dockerfile
# ==============================================================
# Build:   docker compose build
# Run:     docker compose up -d
# Test:    curl http://localhost:8000/api/v1/health
# ==============================================================

# ---- Stage 1: Builder ----------------------------------------
# Install all Python dependencies in an isolated stage so that
# compilers and pip caches do NOT end up in the final image.
# --------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install CPU-only PyTorch first (avoids pulling the ~2 GB CUDA variant)
RUN pip install --no-cache-dir \
        torch torchvision \
        --index-url https://download.pytorch.org/whl/cpu

ARG CROP_PROFILE=rice

# Then install the remaining runtime dependencies
COPY requirements.txt requirements.txt
COPY requirements/ requirements/

RUN pip install --no-cache-dir -r requirements.txt

RUN if [ "$CROP_PROFILE" = "rice" ]; then \
      pip install --no-cache-dir -r requirements/rice-inference.txt; \
    elif [ "$CROP_PROFILE" = "oil_palm" ]; then \
      pip install --no-cache-dir -r requirements/oil-palm-inference.txt; \
    else \
      echo "Unknown CROP_PROFILE: $CROP_PROFILE"; false; \
    fi


# ---- Stage 2: Runtime ----------------------------------------
# Copy only the installed packages and application code into a
# clean slim image.  No compilers, no pip cache, no test files.
# --------------------------------------------------------------
FROM python:3.11-slim

# Security: run as non-root
RUN useradd --create-home appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages \
                    /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ai_engine/ ./ai_engine/

# Copy model config files (weights are volume-mounted at runtime)
COPY models/ ./models/

# Default environment — overridable via docker-compose or -e flags
ENV MODEL_CHECKPOINT_PATH=/app/models/rice/rice_leaf_classifier/best_model.pth \
    MODEL_LABELS_FILE=/app/models/rice/rice_leaf_classifier/labels.json \
    MODEL_CONFIG_FILE=/app/models/rice/rice_leaf_classifier/config.yaml

EXPOSE 8000

# Health probe for Docker / Kubernetes
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

USER appuser

CMD ["uvicorn", "ai_engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
