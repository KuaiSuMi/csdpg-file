FROM python:3.9.23-slim-bookworm@sha256:72d2b9b85bf192b477c1b02fbc0e0905b2ac0dd7f8c9355fd39205ad9a1ec43b
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev spin \
    && rm -rf /var/lib/apt/lists/*
ADD source.tar /opt/kivi/
RUN pip install --no-cache-dir -r /opt/kivi/requirements.txt \
    && mkdir -p /opt/kivi/libs/Spin/Src /opt/kivi/results /opt/kivi/temp \
    && ln -s /usr/bin/spin /opt/kivi/libs/Spin/Src/spin
ADD spin.tar /opt/kivi/libs/Spin/
RUN apt-get update && apt-get install -y --no-install-recommends make bison \
    && rm /opt/kivi/libs/Spin/Src/spin \
    && make -C /opt/kivi/libs/Spin/Src \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/kivi/bin
ENTRYPOINT ["python", "kivi_runner.py"]
