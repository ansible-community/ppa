#!/usr/bin/env bash

sudo apt-get update

sudo apt-get -y install gpg gpg-agent

printenv SIGNING_KEY > "${HOME}"/signing.key
printenv SIGNING_PASSPHRASE > "${HOME}"/signing.passphrase
printenv SIGNING_OWNERTRUST > "${HOME}"/signing.ownertrust

gpg --import --pinentry-mode loopback --passphrase-file "${HOME}"/signing.passphrase "${HOME}"/signing.key
gpg --import-ownertrust "${HOME}"/signing.ownertrust
