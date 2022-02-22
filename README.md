# ppa

## Repo Overview

This repo uses GitHub Actions & Workflows to generate / upload Debian & Ubuntu builds to the https://launchpad.net/~ansible PPAs. See https://github.com/ansible-community/ppa/issues/1 for the latest PPA / Ansible / Ubuntu version matrix.

## Repo Structure

### Branches

Along with the `main` branch, there is currently a branch for each major Ansible release. This is due to the build differences between versions of Ansible.

```
% git branch
  ansible-2.8
  ansible-2.9
  ansible-2.10
  ansible-3
  ansible-4
  ansible-5
* main
```

### Files / Directories

```
(main) % tree -L 3 -a .
.
├── .github
│   └── workflows
│       └── latest_builds.yml
├── LICENSE
├── README.md
├── latest_builds
│   ├── latest_builds.py
│   ├── matrix.yml
│   └── requirements.txt
```

```
(ansible-5) % tree -L 4 -a .
.
├── .github
│   ├── actions
│   │   ├── action.yml
│   │   └── setup.sh
│   └── workflows
│       ├── ansible-core.yml
│       ├── ansible.yml
│       └── resolvelib.yml
├── LICENSE
├── README.md
├── ansible
│   ├── debian
│   │   └── control
│   └── templates
│       └── changelog
├── ansible-core
│   └── debian
│       ├── changelog
│       └── control
├── resolvelib
│   ├── debian
│   │   ├── compat
│   │   ├── control
│   │   ├── copyright
│   │   ├── docs
│   │   ├── patches
│   │   │   └── series
│   │   ├── rules
│   │   ├── source
│   │   │   ├── format
│   │   │   └── local-options
│   │   └── watch
│   └── templates
│       ├── changelog
│       └── hard_code_version
```

## GitHub Actions / Workflows

Currently, GitHub will only run `cron` scheduled workflows on the `main` branch (also note: `cron` scheduled workflows are disabled after 60 days of "inactivity"). So instead of running each of the individual branches as their own scheduled workflow, we use the `latest_builds.yml` workflow on the `main` branch to kick off builds on the other branches (via the repo `secret` `PAT` (GitHub Personal Access Token)) as necessary.

The `latest_builds.yml` workflow uses the `latest_builds/requirements.txt` file to install the required packages and then runs the `latest_builds/latest_builds.py` script. The `latest_builds/latest_builds.py` script uses the `latest_builds/matrix.yml` to compare PyPI and against the various https://launchpad.net/~ansible PPAs to see if a new build is necessary. If a new build is necessary it triggers the appropriate workflow on the appropriate branch.

### `.github/actions/{action.yml,setup.sh}`

These files take care of the common `.dput.cf` generation and gpg key setup.

### `.github/workflows/{ansible-core,ansible,resolvelib}.yml`

These files handle the respective builds.

### Triggering Jobs Manually

Manual runs of the `latest_builds.yml` workflow can be triggered via the GitHub Actions UI and manual runs of the specific branch / workflows can be triggered via the GitHub API. For more information about triggering jobs manually via the GitHub API; see the following example:

```
# First GET the workflows:

% curl --location --request GET 'https://api.github.com/repos/ansible-community/ppa/actions/workflows'
{
  "total_count": 5,
  "workflows": [
    {
      "id": 7276924,
      "node_id": "MDg6V29ya2Zsb3c3Mjc2OTI0",
      "name": "ansible-base",
      "path": ".github/workflows/ansible-base.yml",
      "state": "active",
      "created_at": "2021-03-29T16:04:44.000Z",
      "updated_at": "2021-03-29T16:04:44.000Z",
      "url": "https://api.github.com/repos/ansible-community/ppa/actions/workflows/7276924",
      "html_url": "https://github.com/ansible-community/ppa/blob/main/.github/workflows/ansible-base.yml",
      "badge_url": "https://github.com/ansible-community/ppa/workflows/ansible-base/badge.svg"
    },
    {
      "id": 7276925,
      "node_id": "MDg6V29ya2Zsb3c3Mjc2OTI1",
      "name": "ansible",
      "path": ".github/workflows/ansible.yml",
      "state": "active",
      "created_at": "2021-03-29T16:04:44.000Z",
      "updated_at": "2021-03-29T16:04:44.000Z",
      "url": "https://api.github.com/repos/ansible-community/ppa/actions/workflows/7276925",
      "html_url": "https://github.com/ansible-community/ppa/blob/main/.github/workflows/ansible.yml",
      "badge_url": "https://github.com/ansible-community/ppa/workflows/ansible/badge.svg"
    },
    {
      "id": 8751539,
      "node_id": "MDg6V29ya2Zsb3c4NzUxNTM5",
      "name": "resolvelib",
      "path": ".github/workflows/resolvelib.yml",
      "state": "active",
      "created_at": "2021-05-04T03:28:11.000Z",
      "updated_at": "2021-05-04T03:28:11.000Z",
      "url": "https://api.github.com/repos/ansible-community/ppa/actions/workflows/8751539",
      "html_url": "https://github.com/ansible-community/ppa/blob/main/.github/workflows/resolvelib.yml",
      "badge_url": "https://github.com/ansible-community/ppa/workflows/resolvelib/badge.svg"
    },
    {
      "id": 8751740,
      "node_id": "MDg6V29ya2Zsb3c4NzUxNzQw",
      "name": "ansible-core",
      "path": ".github/workflows/ansible-core.yml",
      "state": "active",
      "created_at": "2021-05-04T03:46:52.000Z",
      "updated_at": "2021-05-04T03:46:52.000Z",
      "url": "https://api.github.com/repos/ansible-community/ppa/actions/workflows/8751740",
      "html_url": "https://github.com/ansible-community/ppa/blob/main/.github/workflows/ansible-core.yml",
      "badge_url": "https://github.com/ansible-community/ppa/workflows/ansible-core/badge.svg"
    },
    {
      "id": 13724938,
      "node_id": "W_kwDOFNAryM4A0W0K",
      "name": "latest builds",
      "path": ".github/workflows/latest_builds.yml",
      "state": "active",
      "created_at": "2021-09-30T21:15:42.000Z",
      "updated_at": "2021-12-22T19:23:39.000Z",
      "url": "https://api.github.com/repos/ansible-community/ppa/actions/workflows/13724938",
      "html_url": "https://github.com/ansible-community/ppa/blob/main/.github/workflows/latest_builds.yml",
      "badge_url": "https://github.com/ansible-community/ppa/workflows/latest%20builds/badge.svg"
    }
  ]
}

# Then (for example) to generate new 5.3.0-2ppa~focal & 5.3.0-2ppa~impish builds for the ansible-5 PPA, you could make the following POST request. Note the 7276925 workflow ID used from the previous request to denote the ansible (.github/workflows/ansible.yml) workflow.

% curl --location --request POST 'https://api.github.com/repos/ansible-community/ppa/actions/workflows/7276925/dispatches' \
--header 'Authorization: token ghp_ACTUAL_GITHUB_PAT_TOKEN_GOES_HERE' \
--header 'Content-Type: application/json' \
--data-raw '    {
        "ref": "ansible-5",
        "inputs": {
            "DEB_DIST": "focal impish",
            "DEB_VERSION": "5.3.0",
            "DEB_RELEASE": "2ppa",
            "LAUNCHPAD_PROJECT": "~ansible",
            "LAUNCHPAD_PPA": "ansible-5"
        }
    }'
```

### Post DATA Reference

| Name | Description |
| --- | --- |
| `ref` | Branch to use <br> Ex: `ansible-5` References https://github.com/ansible-community/ppa/tree/ansible-5 |
| `DEB_DIST` | Ubuntu short code name <br> Ex: `impish` |
| `DEB_VERSION` | Version <br> Ex: `5.3.0` |
| `DEB_RELEASE` | Deb release number <br> Ex: `2ppa` |
| `LAUNCHPAD_PROJECT` | Name of the Launchpad Project to use <br> Ex: `~ansible` would reference https://launchpad.net/~ansible |
| `LAUNCHPAD_PPA` | Name of the PPA under the Launchpad Project to use <br> Ex: `ansible-5` with the `LAUNCHPAD_PROJECT` value of `~ansible` would reference https://launchpad.net/~ansible/+archive/ubuntu/ansible-5 |

## Repo Requirements

### Secrets

| Name | Description | Example |
| --- | --- | --- |
| `DEBSIGN_KEYID` | Deb signing key ID | `4697549E1287BC6A1A481B98DE6FE1F1C7DBF004` |
| `LAUNCHPAD_PROJECT` | Launchpad project name | `~ansible` |
| `PAT` | GitHub PAT for starting additional workflows (only requires the `public_repo` scope) | `ghp_ACTUAL_GITHUB_PAT_TOKEN_GOES_HERE` |
| `SIGNING_KEY` | Armored signing key | <pre>-----BEGIN PGP PRIVATE KEY BLOCK-----<br/><br/>xcaGBGFLvFkBEADQbd7DocOo9XzMo5PD<br/>RX4Nxw4UHWJGjzdBZgmKzk+vLuTR+Cr8<br/>...<br/>tTtohAGXcR9EYhHemdVrew==<br/>=4DaA<br/>-----END PGP PRIVATE KEY BLOCK-----</pre> |
| `SIGNING_OWNERTRUST` | Import-able ownertrust string | `4697549E1287BC6A1A481B98DE6FE1F1C7DBF004:6:` |
| `SIGNING_PASSPHRASE` | Signing key passphrase | `PASSPHRASE_USED_FOR_SIGNING_KEY` |