# Verify Ansible PPA Locally Using Docker

`main.sh` script perform basic tests to verify that the Ansible package installed from ppa:ansible/ansible-* is functioning as expected.

## Requirements

- Docker

### Getting started

- Clone [this](https://github.com/ansible-community/ppa.git) repo.
```
git clone https://github.com/ansible-community/ppa.git
```

```
cd ppa/test/
```

- `main.sh` requires two arguments: Ubuntu Code Name and Launchpad PPA Name. Based on the provided ubuntu code name, `main.sh` will start a docker container and run the `test/script.lib` script to verify the Ansible PPA package.

Display help:
```
./main.sh -h
```

Usage:
```
./main.sh -c impish -p ansible
```

Example Loop to Test [Published Version Matrix](https://github.com/ansible-community/ppa/issues/1)

```
for CODE_NAME in trusty xenial bionic focal impish jammy; do
  for PPA in ansible testing-ansible; do
    echo "running ${CODE_NAME} with ${PPA}";
    ./main.sh -c ${CODE_NAME} -p ${PPA}
  done
done
```