#!/usr/bin/env bash

sudo apt-get -y remove ansible || true
sudo apt-get -y remove ansible-base || true
sudo apt-get -y remove ansible-core || true
sudo apt-get -y autoremove
