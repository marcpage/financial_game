![status sheild](https://img.shields.io/static/v1?label=status&message=starting...&color=inactive&style=plastic)
![GitHub](https://img.shields.io/github/license/marcpage/financial_game?style=plastic)
[![commit sheild](https://img.shields.io/github/last-commit/marcpage/financial_game?style=plastic)](https://github.com/marcpage/financial_game/commits)
[![activity sheild](https://img.shields.io/github/commit-activity/m/marcpage/financial_game?style=plastic)](https://github.com/marcpage/financial_game/commits)
![GitHub top language](https://img.shields.io/github/languages/top/marcpage/financial_game?style=plastic)
[![size sheild](https://img.shields.io/github/languages/code-size/marcpage/financial_game?style=plastic)](https://github.com/marcpage/financial_game)
[![issues sheild](https://img.shields.io/github/issues-raw/marcpage/financial_game?style=plastic)](https://github.com/marcpage/financial_game/issues)
[![follow sheild](https://img.shields.io/github/followers/marcpage?label=Follow&style=social)](https://github.com/marcpage?tab=followers)
[![watch sheild](https://img.shields.io/github/watchers/marcpage/financial_game?label=Watch&style=social)](https://github.com/marcpage/financial_game/watchers)

# financial_game

Website that hosts a real-life financial game

# Contributions

Before submitting, make sure to run `black`, `pylint`, and `flake8` and ensure test coverage is at 100%.
If you're on macOS or Linux, you can just run `python3 pr_build.py format` which will do all this for you.

# Runing the server

On macOS or Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 -m financial_game
```

On Windows:
```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py -m financial_game
```

It will create:
- **macOS**: `~/Library/Preferences/financial_game.yaml`
- **Linux**: `~/.financial_game.yaml`
- **Windows**: `%LOCALAPPDATA%\financial_game.yaml`

You can use a different location by specifying `--settings <path to yaml file>`.
This file contains many of the parameters you can pass (or did pass) on the command line.
To get the full list of options on the command line: `python3 -m financial_game --help`.
