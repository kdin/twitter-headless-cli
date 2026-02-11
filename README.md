# twitter-headless-cli

A CLI tool to browse Twitter in headless mode and retrieve timeline tweets.

## Installation

```bash
# Clone the repository
git clone https://github.com/kdin/twitter-headless-cli.git
cd twitter-headless-cli

# Create a virtual environment with uv
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install the package with uv
uv pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Environment Variables

Set your Twitter credentials:

```bash
export TWITTER_USERNAME="your_email@example.com"
export TWITTER_PASSWORD="your_password"
```

## Usage

```bash
# Get timeline tweets from a user
twitter-cli get-timeline --username elonmusk
```

## Features

- Headless browser automation using Playwright
- Session persistence (login state saved to `auth.json`)
- Automatic re-authentication on session expiry
- Error handling for missing credentials and network issues

## Session Management

- First run: Logs in and saves session to `auth.json`
- Subsequent runs: Uses saved session (skips login)
- Auto-relogin if session expires