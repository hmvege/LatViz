# FROM ubuntu:20.04 as build
FROM python:3.6.15-bullseye as build

ARG SETUPTOOLS_SCM_PRETEND_VERSION

ADD . /src/latviz/

RUN apt-get update && apt-get install -y \
    g++ \
    python3-dev \
    python3-venv \
    ffmpeg \
    imagemagick \
 && apt-get autoclean

RUN cd /src/latviz
RUN python3 -m venv /venv
RUN /venv/bin/pip install --upgrade pip

WORKDIR /src/latviz

RUN cd /src/latviz
RUN /venv/bin/pip install -r /src/latviz/requirements.txt
    # /venv/bin/pip install .
RUN /venv/bin/python /src/latviz/setup.py install


ENV PYTHONBUFFERED 1
ENV PATH="/venv/bin:${PATH}"
ENTRYPOINT ["/venv/bin/latviz"]