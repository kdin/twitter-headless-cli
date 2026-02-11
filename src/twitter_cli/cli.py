"""Twitter CLI - Main application logic."""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Optional, List

import click
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError


AUTH_FILE = Path("auth.json")

# Timeout constants (in milliseconds)
LONG_TIMEOUT = 30000  # 30 seconds
MEDIUM_TIMEOUT = 15000  # 15 seconds
SHORT_TIMEOUT = 10000  # 10 seconds


def get_credentials() -> tuple[str, str]:
    """Get Twitter credentials from environment variables."""
    username = os.getenv("TWITTER_USERNAME")
    password = os.getenv("TWITTER_PASSWORD")
    
    if not username or not password:
        click.echo("Error: TWITTER_USERNAME and TWITTER_PASSWORD environment variables must be set", err=True)
        sys.exit(1)
    
    return username, password


def save_auth_state(context: BrowserContext) -> None:
    """Save authentication state to file."""
    context.storage_state(path=str(AUTH_FILE))
    click.echo(f"Authentication state saved to {AUTH_FILE}")


def load_auth_state() -> Optional[dict]:
    """Load authentication state from file if it exists."""
    if AUTH_FILE.exists():
        with open(AUTH_FILE, 'r') as f:
            return json.load(f)
    return None


def login_to_twitter(page: Page, username: str, password: str) -> bool:
    """Login to Twitter and return success status."""
    try:
        click.echo("Logging in to Twitter...")
        page.goto("https://twitter.com/i/flow/login", wait_until="networkidle", timeout=LONG_TIMEOUT)
        
        # Wait for username input and fill it
        page.wait_for_selector('input[autocomplete="username"]', timeout=SHORT_TIMEOUT)
        page.fill('input[autocomplete="username"]', username)
        page.click('text="Next"')
        
        # Wait for password input and fill it
        page.wait_for_selector('input[name="password"]', timeout=SHORT_TIMEOUT)
        page.fill('input[name="password"]', password)
        page.click('text="Log in"')
        
        # Wait for navigation to complete
        page.wait_for_url("https://twitter.com/home", timeout=LONG_TIMEOUT)
        click.echo("Successfully logged in to Twitter")
        return True
        
    except PlaywrightTimeoutError as e:
        click.echo(f"Error: Login timeout - {str(e)}", err=True)
        return False
    except Exception as e:
        click.echo(f"Error: Login failed - {str(e)}", err=True)
        return False


def get_timeline_tweets(page: Page, username: str) -> List[str]:
    """Fetch timeline tweets from a user's profile."""
    try:
        click.echo(f"Fetching timeline for @{username}...")
        page.goto(f"https://twitter.com/{username}", wait_until="networkidle", timeout=LONG_TIMEOUT)
        
        # Wait for tweets to load
        page.wait_for_selector('article[data-testid="tweet"]', timeout=SHORT_TIMEOUT)
        
        # Extract tweet text
        tweets = []
        tweet_elements = page.query_selector_all('article[data-testid="tweet"]')
        
        for tweet in tweet_elements:
            # Get the tweet text content
            tweet_text_element = tweet.query_selector('[data-testid="tweetText"]')
            if tweet_text_element:
                tweet_text = tweet_text_element.inner_text()
                tweets.append(tweet_text)
        
        return tweets
        
    except PlaywrightTimeoutError as e:
        click.echo(f"Error: Timeout while fetching timeline - {str(e)}", err=True)
        return []
    except Exception as e:
        click.echo(f"Error: Failed to fetch timeline - {str(e)}", err=True)
        return []


@click.group()
def cli():
    """Twitter Headless CLI - Browse Twitter in headless mode."""
    pass


@cli.command("get-timeline")
@click.option("--username", required=True, help="Twitter username to fetch timeline from")
def get_timeline(username: str):
    """Retrieve tweets from a user's timeline."""
    twitter_username, twitter_password = get_credentials()
    
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        
        # Check if we have saved auth state
        auth_state = load_auth_state()
        
        if auth_state:
            click.echo("Using saved authentication state...")
            context = browser.new_context(storage_state=auth_state)
        else:
            context = browser.new_context()
        
        page = context.new_page()
        
        try:
            # If we don't have auth state, login first
            if not auth_state:
                if not login_to_twitter(page, twitter_username, twitter_password):
                    click.echo("Error: Authentication failed", err=True)
                    sys.exit(1)
                save_auth_state(context)
            else:
                # Verify the session is still valid by checking if we're logged in
                try:
                    page.goto("https://twitter.com/home", wait_until="networkidle", timeout=MEDIUM_TIMEOUT)
                except (PlaywrightTimeoutError, Exception) as e:
                    # Session expired or network error, login again
                    click.echo("Session expired, logging in again...")
                    if not login_to_twitter(page, twitter_username, twitter_password):
                        click.echo("Error: Authentication failed", err=True)
                        sys.exit(1)
                    save_auth_state(context)
            
            # Fetch timeline tweets
            tweets = get_timeline_tweets(page, username)
            
            if tweets:
                click.echo(f"\nFound {len(tweets)} tweets:\n")
                for i, tweet in enumerate(tweets, 1):
                    click.echo(f"{i}. {tweet}\n")
            else:
                click.echo("No tweets found or error occurred")
        
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)
        
        finally:
            context.close()
            browser.close()


def main():
    """Entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
