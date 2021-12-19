from ubuntu:latest

RUN apt update && apt install --yes python3 python3-pip python3-venv

WORKDIR /project
RUN useradd -m bob && chown bob:bob /project

USER bob

RUN python3 -m venv venv && ./venv/bin/pip install -U pip
ENV PATH="/project/venv/bin:${PATH}"

COPY --chown=bob:bob scripts/ ./
