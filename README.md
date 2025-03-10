# fuji-x-weekly-simulation-profiles

**Built with**

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)

**Repo Status**

[![fortnightly scrape status](https://img.shields.io/github/actions/workflow/status/namtonthat/fuji-x-weekly-simulation-profiles/on-fortnightly-scrape.yml?branch=main)](https://github.com/namtonthat/fuji-x-weekly-simulation-profiles/actions/workflows/on-fornightly-scrape.yml?query=branch%3Amain)
[![License](https://img.shields.io/github/license/namtonthat/fuji-x-weekly-simulation-profiles)](https://img.shields.io/github/license/namtonthat/fuji-x-weekly-simulation-profiles)

### Purpose

- Auto scraping the [www.fujixweekly.com](https://www.fujixweekly.com) for `Fuji X` simulation profiles every fornight
- A simple CLI tool to copy the `.FP1` files over to `X Raw Studio` app with ease using CLI and Python (works for mac OS).
  ![CLI screenshot](media/cli-screenshot.png)

### Getting Started

```
# Setting up your environment
make install
```

### Installing Profiles to `FujiX` App

1. Make a blank profile; this is so that the serial number is registered and can be copied over with the template `.fp1` file.

   a. Open `Fujifilm X Raw Studio` App.

   b. Create a base profile named `_Base Profile` so it appears first. (It doesn't have to, I've just done it for convenience)

2. Run

```
# Copy the files from fuji_profiles into your local environment
make copy
```

![CLI in action](media/cli-full.gif)

- This will start the CLI command prompt to copy the `FujiProfiles` over to your computer.

### Reingestion

In the case that the profiles aren't being parsed correctly, you can force a reingestion by running `make clean` which removes the `./cached` profiles. This is automated to run every fortnight.

```
# To force a reingestion, run
make clean
```

## Motivations

- [plamf repo](https://github.com/plamf/fuji-x-weekly-simulation-profiles)
- Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
