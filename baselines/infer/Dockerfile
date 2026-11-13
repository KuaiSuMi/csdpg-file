FROM eclipse-temurin:17-jdk-noble@sha256:1bedb04434bd275ef072355e9caec2a22be5240fbe82ad51a59323f2bbcab4a6
ADD infer-linux-x86_64-v1.3.0.tar.xz /opt/
ENV PATH="/opt/infer-linux-x86_64-v1.3.0/bin:${PATH}"
WORKDIR /workspace
ENTRYPOINT ["infer"]
