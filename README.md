# fuji-x-weekly-simulation-profiles

**Built with**

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![python](https://img.shields.io/badge/Python-3.11-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)

**Repo Status**

[![fortnightly scrape status](https://img.shields.io/github/actions/workflow/status/namtonthat/fuji-x-weekly-simulation-profiles/on-fortnightly-scrape.yml?branch=main)](https://github.com/namtonthat/fuji-x-weekly-simulation-profiles/actions/workflows/on-fornightly-scrape.yml?query=branch%3Amain)
[![License](https://img.shields.io/github/license/namtonthat/fuji-x-weekly-simulation-profiles)](https://img.shields.io/github/license/namtonthat/fuji-x-weekly-simulation-profiles)

### Purpose

- Auto scraping the [www.fujixweekly.com](https://www.fujixweekly.com) for `Fuji X` simulation profiles every fornight
- Copy the `.FP1` files over to `X Raw Studio` app with ease using CLI and Python

### Getting Started

```
# Setting up your environment
make install
```

### Installing Profiles to `FujiX` App

```
# Copy the files from fuji_profiles into your local environment
make copy
```

- This will start the CLI command prompt to copy the `FujiProfiles` over to your computer.

### Reingestion

In the case that the profiles aren't being parsed correctly, you can force a reingestion by running `make clean` which removes the `./cached` profiles. This is automated to run every fortnight.

```
# To force a reingestion, run
make clean
```

## Motivations

- [plamf repo](https://github.com/plamf/fuji-x-weekly-simulation-profiles)
- Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
