# cmake-git-version
Example C / C++ project that uses CMake to build and git for version numbers

## Dependencies

* Git
* Python (>=3.5)
* [GitVersion](https://gitversion.net/)

## Usage

Manually:
    python gitversion2c.py commithash.c.gitver.template -o version.c

You can also integrate with make or cmake, put it into some pre-build step.

## Philosophy & Concepts

[Semantic Versioning](https://semver.org/) a standard for describing software
