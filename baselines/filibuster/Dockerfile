FROM python:3.9.23-slim-bookworm@sha256:72d2b9b85bf192b477c1b02fbc0e0905b2ac0dd7f8c9355fd39205ad9a1ec43b
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/baselines/sources/filibuster
WORKDIR /workspace
