#!/usr/bin/env bash

sudo apt -y remove ansible || true
sudo apt -y remove ansible-base || true
sudo apt -y remove ansible-core || true
sudo apt -y autoremove

sudo apt-get udpate
sudo apt -y install gpg gpg-agent wget

cat > "${HOME}"/.dput.cf << EOF
[${LAUNCHPAD_PPA}]
fqdn = ppa.launchpad.net
method = ftp
incoming = ${LAUNCHPAD_PROJECT}/ubuntu/${LAUNCHPAD_PPA}/
login = anonymous
allow_unsigned_uploads = 0
EOF

printenv SIGNING_KEY > "${HOME}"/signing.key
printenv SIGNING_PASSPHRASE > "${HOME}"/signing.passphrase
printenv SIGNING_OWNERTRUST > "${HOME}"/signing.ownertrust

gpg --import --batch --pinentry-mode loopback --passphrase-file "${HOME}"/signing.passphrase "${HOME}"/signing.key
gpg --import-ownertrust "${HOME}"/signing.ownertrust
