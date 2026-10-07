import argparse
import os
import requests
import sys
import yaml

from dataclasses import dataclass
from launchpadlib.launchpad import Launchpad
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version
from pathlib import Path
from time import monotonic, sleep

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


ARCH = "amd64"
MATRIX = Path(__file__).resolve().parent / "matrix.yml"
HTTP_TIMEOUT = 30  # seconds per request
POLL_INTERVAL = 30  # seconds between checks on the dispatched runs
RUN_TIMEOUT = 2 * 60 * 60  # seconds to wait for the dispatched runs before giving up on them


@dataclass
class Build:
    package: str
    version: Version
    dists: list[str]
    github_branch: str
    launchpad_ppa: str
    run_url: str | None = None
    result: str | None = None  # the run's conclusion ("success", "failure", ...) or why there is none


def env(name):
    value = os.environ.get(name)
    if not value:
        sys.exit(f"`{name}` not found!")
    return value


def published_versions(ppa):
    """Highest published version of each source package per dist, e.g. {("ansible-core", "noble"): Version("2.21.5")}."""
    versions = {}
    for pb in ppa.getPublishedBinaries(status="Published"):
        if pb.display_name.split()[-1] != ARCH:
            continue
        dist = pb.binary_package_version.split("~")[-1]
        try:
            version = Version(pb.binary_package_version.split("-")[0].replace("~", ""))
        except InvalidVersion:
            continue
        key = (pb.source_package_name, dist)
        if key not in versions or version > versions[key]:
            versions[key] = version
    return versions


def pypi_versions(session, package):
    """All non-yanked releases of a package on PyPI."""
    r = session.get(f"https://pypi.org/pypi/{package}/json", timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    versions = []
    for version, files in r.json()["releases"].items():
        if any(f["yanked"] for f in files):
            continue
        try:
            versions.append(Version(version))
        except InvalidVersion:
            continue
    return versions


def plan_builds(matrix, launchpad_project, pypi, errors):
    """Compare each matrix entry's PPA with PyPI and return the builds needed to catch up."""
    ppas = {ppa.name: ppa for ppa in launchpad_project.ppas}
    published = {}
    pypi_releases = {}
    builds = []

    for name, config in matrix.items():
        print(f"checking '{name}' package(s)")
        github_branch = config.get("github_branch", name)
        print(f"  github_branch = {github_branch}")
        launchpad_ppa = config.get("launchpad_ppa", name)
        print(f"  launchpad_ppa = {launchpad_ppa}")

        if launchpad_ppa not in ppas:
            print(f"  ERROR: PPA '{launchpad_ppa}' not found")
            errors.append(f"'{name}': PPA '{launchpad_ppa}' not found in the Launchpad project")
            continue

        if launchpad_ppa not in published:
            published[launchpad_ppa] = published_versions(ppas[launchpad_ppa])

        for package in config["packages"]:
            package_name = package["name"]
            print(f"  checking '{package_name}' versions")

            if package_name not in pypi_releases:
                try:
                    pypi_releases[package_name] = pypi_versions(pypi, package_name)
                except requests.RequestException as e:
                    print(f"    ERROR: PyPI request failed: {e}")
                    errors.append(f"'{name}': PyPI request for '{package_name}' failed: {e}")
                    continue

            matching = sorted(SpecifierSet(package["version_specifier_set"]).filter(pypi_releases[package_name]), reverse=True)
            if not matching:
                print(f"    '{package_name}' version matching '{package['version_specifier_set']}' not found")
                continue
            latest = matching[0]

            build_dists = []
            for dist in package["dists"]:
                current = published[launchpad_ppa].get((package_name, dist))
                if current is None:
                    print(f"    '{dist}' version not found")
                    build_dists.append(dist)
                elif current < latest:
                    print(f"    '{dist}' version '{current}' < '{latest}'")
                    build_dists.append(dist)

            if not build_dists:
                print(f"    '{package_name}' on {package['dists']} is already at '{latest}'")
                continue

            print(f"    adding '{package_name}' '{latest}' for {build_dists}")
            builds.append(Build(package_name, latest, build_dists, github_branch, launchpad_ppa))

    return builds


def dispatch_build(github, actions_url, workflow_id, build, launchpad_project):
    """Dispatch one build and return the API URL of the run it started (None if GitHub did not say)."""
    data = {
        "ref": build.github_branch,
        "inputs": {
            "DEB_DIST": " ".join(build.dists),
            "DEB_VERSION": str(build.version),
            "LAUNCHPAD_PROJECT": launchpad_project,
            "LAUNCHPAD_PPA": build.launchpad_ppa,
        },
        "return_run_details": True,
    }
    r = github.post(f"{actions_url}/workflows/{workflow_id}/dispatches", json=data, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    if r.status_code != 200:
        build.result = f"dispatched, but GitHub returned HTTP {r.status_code} without run details"
        return None

    run = r.json()
    build.run_url = run["html_url"]
    print(f"    dispatched {build.run_url}")
    return run["run_url"]


def wait_for_builds(github, runs):
    """Poll the dispatched runs ({run API URL: Build}) together, recording each conclusion as it completes."""
    deadline = monotonic() + RUN_TIMEOUT
    while runs and monotonic() < deadline:
        sleep(POLL_INTERVAL)
        for run_url, build in list(runs.items()):
            try:
                r = github.get(run_url, timeout=HTTP_TIMEOUT)
                r.raise_for_status()
            except requests.RequestException as e:
                print(f"checking {build.run_url} failed, will retry: {e}")
                continue
            status = r.json()
            if status["status"] == "completed":
                build.result = status["conclusion"]
                print(f"'{build.package}' '{build.version}' for '{build.launchpad_ppa}' completed: {build.result} {build.run_url}")
                del runs[run_url]

    for build in runs.values():
        build.result = f"still running after {RUN_TIMEOUT // 60} minutes"


def report(builds, errors, dry_run):
    """Print a summary table (also written to the GitHub job summary when available)."""
    lines = ["## latest builds", ""]
    if builds:
        lines += ["| package | version | dists | PPA | branch | result |", "| --- | --- | --- | --- | --- | --- |"]
        for b in builds:
            result = "dry run" if dry_run else b.result
            if b.run_url:
                result = f"[{result}]({b.run_url})"
            lines.append(f"| {b.package} | {b.version} | {' '.join(b.dists)} | {b.launchpad_ppa} | {b.github_branch} | {result} |")
    else:
        lines.append("Nothing to build.")
    if errors:
        lines += ["", "### errors", ""] + [f"- {e}" for e in errors]

    summary = "\n".join(lines) + "\n"
    print("\n" + summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(summary)


def main():
    parser = argparse.ArgumentParser(description="Dispatch builds for PPAs that are behind PyPI.")
    parser.add_argument("--dry-run", action="store_true", help="only report what would be built; GitHub is not contacted")
    args = parser.parse_args()

    launchpad_project = env("LAUNCHPAD_PROJECT")

    with open(MATRIX) as f:
        matrix = yaml.load(f, Loader=SafeLoader)

    cache_dir = f"{Path.home()}/.launchpadlib/cache/"
    launchpad = Launchpad.login_anonymously("read-only", "production", cache_dir, version="devel")

    errors = []
    builds = plan_builds(matrix, launchpad.projects[launchpad_project], requests.Session(), errors)

    if args.dry_run:
        report(builds, errors, dry_run=True)
        return 1 if errors else 0

    actions_url = f"{env('GITHUB_API_URL')}/repos/{env('GITHUB_REPOSITORY')}/actions"
    github = requests.Session()
    github.headers.update({"Accept": "application/vnd.github+json", "Authorization": f"Bearer {env('GITHUB_TOKEN')}"})

    r = github.get(f"{actions_url}/workflows", params={"per_page": 100}, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    workflows = {workflow["name"]: workflow["id"] for workflow in r.json()["workflows"]}

    runs = {}
    for build in builds:
        print(f"building '{build.package}' '{build.version}' for {build.dists}")
        print(f"  github_branch = {build.github_branch}")
        print(f"  launchpad_ppa = {build.launchpad_ppa}")
        if build.package not in workflows:
            build.result = f"no '{build.package}' workflow found"
            continue
        try:
            run_url = dispatch_build(github, actions_url, workflows[build.package], build, launchpad_project)
        except (requests.RequestException, KeyError) as e:
            build.result = f"dispatch failed: {e!r}"
            continue
        if run_url:
            runs[run_url] = build

    wait_for_builds(github, runs)

    report(builds, errors, dry_run=False)
    return 1 if errors or any(build.result != "success" for build in builds) else 0


if __name__ == "__main__":
    sys.exit(main())
