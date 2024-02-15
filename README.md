# Rowing Data

Scraping tool to download 10 years of workout history as `*.fit` files. You will be all able to download them in Garmin Connect.

## Usage

It is preferable to use the script inside a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade requests
```

Example:

```bash
python retrieveHistory.py myUser myPassword ${HOME}/Downloads
```
