#!/usr/bin/env bash

cat > "${HOME}"/.dput.cf << EOF
[${LAUNCHPAD_PPA}]
fqdn = ppa.launchpad.net
method = ftp
incoming = ${LAUNCHPAD_PROJECT}/ubuntu/${LAUNCHPAD_PPA}/
login = anonymous
allow_unsigned_uploads = 0
EOF
