#!/usr/bin/env bash

sudo apt-get update

sudo apt-get -y install \
    build-essential \
    debhelper \
    devscripts \
    dh-python \
    pybuild-plugin-pyproject \
    python3-pip \
    python3-setuptools \
    python3 \
    wget
