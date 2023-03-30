import os
import requests
import yaml

from launchpadlib.launchpad import Launchpad
from packaging.version import Version
from packaging.specifiers import SpecifierSet
from pathlib import Path
from time import sleep

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


def get_workflow(workflows, name):
    return next((workflow for workflow in workflows if workflow["name"] == name), None)


GITHUB_WORKSPACE = os.environ.get("GITHUB_WORKSPACE")

if not GITHUB_WORKSPACE:
    raise Exception("`GITHUB_WORKSPACE` not found!")

GITHUB_API_URL = os.environ.get("GITHUB_API_URL")

if not GITHUB_API_URL:
    raise Exception("`GITHUB_API_URL` not found!")

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")

if not GITHUB_REPOSITORY:
    raise Exception("`GITHUB_REPOSITORY` not found!")

GITHUB_PAT = os.environ.get("GITHUB_PAT")

if not GITHUB_PAT:
    raise Exception("`GITHUB_PAT` not found!")

LAUNCHPAD_PROJECT = os.environ.get("LAUNCHPAD_PROJECT")

if not LAUNCHPAD_PROJECT:
    raise Exception("`LAUNCHPAD_PROJECT` not found!")

ARCH = "amd64"


with open(f"{GITHUB_WORKSPACE}/latest_builds/matrix.yml", "r") as f:
    matrix = yaml.load(f, Loader=SafeLoader)

base_actions_url = f"{GITHUB_API_URL}/repos/{GITHUB_REPOSITORY}/actions"
base_workflows_url = f"{base_actions_url}/workflows"
base_runs_url = f"{base_actions_url}/runs"

github_headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"Token {GITHUB_PAT}",
}

s = requests.Session()
s.headers.update(github_headers)

r = s.get(base_workflows_url)

if not r.ok:
    raise Exception("workflows request failed")

workflows = r.json()["workflows"]

cache_dir = f"{Path.home()}/.launchpadlib/cache/"
launchpad = Launchpad.login_anonymously("read-only", "production", cache_dir, version="devel")
launchpad_project = launchpad.projects[LAUNCHPAD_PROJECT]

pypi_releases = {}
builds = []

for name, config in matrix.items():
    print(f"checking '{name}' package(s)")
    github_branch_name = config.get("github_branch", name)
    print(f"  github_branch = {github_branch_name}")
    launchpad_ppa_name = config.get("launchpad_ppa", name)
    print(f"  launchpad_ppa = {launchpad_ppa_name}")
    launchpad_ppa = list(filter(lambda x: x.name == launchpad_ppa_name, launchpad_project.ppas))[0]

    for package in config["packages"]:
        print(f"  checking '{package['name']}' versions")

        published_binaries = launchpad_ppa.getPublishedBinaries(status="Published")
        dist_versions = {
            x.binary_package_version.split("~")[-1]: x.binary_package_version.split("-")[0].replace("~", "")
            for x in published_binaries
            if x.source_package_name == package["name"] and x.display_name.split()[-1] == ARCH
        }

        if package["name"] not in pypi_releases:
            r = requests.get(f"https://pypi.org/pypi/{package['name']}/json")

            if not r.ok:
                raise Exception("pypi request failed")

            resp = r.json()

            available_releases = [Version(k) for k, v in resp["releases"].items() if not any(x["yanked"] for x in v)]
            pypi_releases[package["name"]] = available_releases

        filtered_versions = sorted(
            SpecifierSet(package["version_specifier"]).filter(pypi_releases[package["name"]]), reverse=True
        )

        try:
            latest_pypi_version = filtered_versions[0]
        except IndexError:
            print(f"    '{package['name']}' version matching '{package['version_specifier']}' not found")
            continue

        build_dists = []

        for dist in package["dists"]:
            if dist not in dist_versions.keys() or Version(dist_versions[dist]) < latest_pypi_version:
                build_dists.append(dist)

        if not build_dists:
            print(f"    '{package['name']}' on {package['dists']} is already at '{latest_pypi_version}'")
            continue

        print(f"    adding '{package['name']}' '{latest_pypi_version}' for {build_dists}")
        builds.append([name, build_dists, github_branch_name, latest_pypi_version, launchpad_ppa_name])


for build in builds:
    name, build_dists, github_branch_name, latest_pypi_version, launchpad_ppa_name = build
    print(f"building '{name}' package(s)")
    print(f"  github_branch = {github_branch_name}")
    print(f"  launchpad_ppa = {launchpad_ppa_name}")
    print(f"  building '{package['name']}' versions")

    print(f"    building '{package['name']}' '{latest_pypi_version}' for {build_dists}")

    workflow = get_workflow(workflows, package["name"])

    print(
        f"    running '{workflow['name']}' workflow against '{github_branch_name}' ref for '{launchpad_ppa_name}' ppa"
    )

    run_in_progress = True
    data = {
        "ref": github_branch_name,
        "inputs": {
            "DEB_DIST": " ".join(build_dists),
            "DEB_VERSION": str(latest_pypi_version),
            "LAUNCHPAD_PROJECT": LAUNCHPAD_PROJECT,
            "LAUNCHPAD_PPA": launchpad_ppa_name,
        },
    }
    p = s.post(f"{base_workflows_url}/{workflow['id']}/dispatches", json=data)

    if not p.ok:
        raise Exception("post failed!")

    while run_in_progress:
        sleep(15)
        r = s.get(base_runs_url, params={"per_page": 1})
        if not r.ok:
            print("      workflow query failed")
            continue
        workflow_runs = r.json()["workflow_runs"]
        run_in_progress = any([workflow_run["status"] != "completed" for workflow_run in workflow_runs])
