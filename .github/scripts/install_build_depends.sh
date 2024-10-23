#!/usr/bin/env bash

sudo apt-get update

sudo apt-get -y install \
    debhelper \
    devscripts \
    dh-python \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-venv \
    wget
