import os
import requests

from bs4 import BeautifulSoup
from launchpadlib.launchpad import Launchpad
from packaging.version import Version
from packaging.specifiers import SpecifierSet
from pathlib import Path


DEB_DISTS = os.environ.get("DEB_DIST").split()
DEB_NAME = os.environ.get("DEB_NAME")
DEB_VERSION_SPECIFIER = os.environ.get("DEB_VERSION_SPECIFIER")
DEB_ARCH = os.environ.get("DEB_ARCH")
LAUNCHPAD_PPA = os.environ.get("LAUNCHPAD_PPA")
LAUNCHPAD_PROJECT = os.environ.get("LAUNCHPAD_PROJECT")
GITHUB_ENV = os.environ.get("GITHUB_ENV")


if not all([DEB_DISTS, DEB_NAME, DEB_VERSION_SPECIFIER, DEB_ARCH, LAUNCHPAD_PPA, LAUNCHPAD_PROJECT, GITHUB_ENV]):
    raise Exception("missing vars!")

r = requests.get(f"https://pypi.org/rss/project/{DEB_NAME}/releases.xml")

if not r.ok:
    raise Exception("request failed")

soup = BeautifulSoup(r.content, "xml")

filtered_versions = sorted(
    SpecifierSet(DEB_VERSION_SPECIFIER).filter([Version(item.title.text) for item in soup.find_all("item")]),
    reverse=True,
)
latest_pypi_version = filtered_versions[0]

cache_dir = f"{Path.home()}/.launchpadlib/cache/"
launchpad = Launchpad.login_anonymously("read-only", "production", cache_dir, version="devel")

project = launchpad.projects[LAUNCHPAD_PROJECT]
ppa = list(filter(lambda x: x.name == LAUNCHPAD_PPA, project.ppas))[0]
published_binaries = ppa.getPublishedBinaries(status="Published")
dist_versions = {
    x.binary_package_version.split("~")[-1]: x.binary_package_version.split("-")[0].replace("~", "")
    for x in published_binaries
    if x.source_package_name == DEB_NAME and x.display_name.split()[-1] == DEB_ARCH
}

build_dists = []

for dist in DEB_DISTS:
    if dist not in dist_versions.keys() or Version(dist_versions[dist]) < latest_pypi_version:
        build_dists.append(dist)

if build_dists:
    with open(GITHUB_ENV, "a") as f:
        f.write(f"DEB_VERSION={latest_pypi_version}\nDEB_DIST={' '.join(build_dists)}")
