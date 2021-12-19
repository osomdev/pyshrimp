from ubuntu:latest

RUN apt update && apt install --yes python3 daemontools python3-pip python3-venv python3-pytest

WORKDIR /project
RUN useradd -m bob && chown bob:bob /project

USER bob

RUN python3 -m venv venv \
    && ./venv/bin/pip install -U pip \
    && ./venv/bin/pip install pytest

ENV PATH="/project/venv/bin:${PATH}"

COPY --chown=bob:bob ./ ./
RUN pip install -e .

RUN bash -i