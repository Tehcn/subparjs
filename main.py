import requests
import tarfile
from distutils.dir_util import copy_tree, mkpath
from distutils.errors import DistutilsFileError
from shutil import rmtree
from os import remove
import json

added_deps = []
names = []


def download(package: str, version: str):
    url = f"https://registry.npmjs.com/{package}/-/{package}-{version}.tgz"
    if len(package.split("/")) > 1:
        url = f"https://registry.npmjs.com/{package}/-/{package.split('/')[1]}-{version}.tgz"
        mkpath(f"./node_modules/{package.split('/')[0]}")
    data = requests.get(url)
    try:
        with open(f"./node_modules/{package}-{version}.tgz", "xb") as f:
            f.write(data.content)
    except FileExistsError:
        with open(f"./node_modules/{package}-{version}.tgz", "wb") as f:
            f.write(data.content)


def extract(package: str, version: str):
    tar = tarfile.open(f"./node_modules/{package}-{version}.tgz")
    tar.extractall(f"./node_modules/{package}-{version}-tmp")
    tar.close()

    try:
        copy_tree(
            f"./node_modules/{package}-{version}-tmp/package",
            f"./node_modules/{package}-{version}",
        )
    except DistutilsFileError:
        try:
            copy_tree(
                f"./node_modules/{package}-{version}-tmp/{package.split('/')[1]}",
                f"./node_modules/{package}-{version}",
            )
        except:
            print(f"failed to extract {package}@{version}")
            exit(1)

    rmtree(f"./node_modules/{package}-{version}-tmp")
    remove(f"./node_modules/{package}-{version}.tgz")


def get_latest_version(package: str) -> str:
    return requests.get(f"https://registry.npmjs.com/{package}/latest").json()[
        "version"
    ]


def install(package: str, version: str):
    global added_deps
    global names
    if package in names:
        return
    if version.lower() == "latest":
        version = get_latest_version(package)
        print(f"adding {package}@{version}")
        download(package, version)
        extract(package, version)
    else:
        print(f"adding {package}@{version}")
        download(package, version)
        extract(package, version)

    added_deps.append((package, version))
    names.append(package)

    # recursively install dependencies
    deps = read_dependencies(f"./node_modules/{package}-{version}")

    if len(deps) > 0:
        for dep in deps:
            install(dep[0], dep[1])


def parse_version(package: str, version: str):
    if ">=" in version or version == "latest" or version == "*":
        return get_latest_version(package)
    if len(version.split(".")) < 3:
        version += ".0" * (3 - len(version.split(".")))
    return version.strip("^>=<!~").replace("x", "0")


def read_dependencies(directory: str):
    packages = []
    with open(f"{directory}/package.json") as f:
        # try:
        pkg = json.loads(f.read())
        if "dependencies" in pkg:
            deps = pkg["dependencies"]
            for dep in deps.items():
                packages.append((dep[0], parse_version(dep[0], dep[1])))
        if "devDependencies" in pkg:
            dev_deps = pkg["devDependencies"]
            for dep in dev_deps.items():
                packages.append((dep[0], parse_version(dep[0], dep[1])))
    return packages


install("@tehcn/log4js", "latest")
print(f"Added {len(added_deps)} packages.")
for dep in added_deps:
    print(f"installed {dep[0]}@{dep[1]}")
