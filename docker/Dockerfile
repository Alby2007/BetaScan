FROM node:24-slim@sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20  # pinned digest (rebuilt node:24-slim post disk-corruption)
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates python3 procps && rm -rf /var/lib/apt/lists/*
RUN corepack enable
WORKDIR /repo
