FROM node:24-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates python3 procps && rm -rf /var/lib/apt/lists/*
RUN corepack enable
WORKDIR /repo
