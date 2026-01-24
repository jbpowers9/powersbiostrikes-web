#!/usr/bin/env python3
"""
Schwab API Integration (Cloud-Compatible Version)
==================================================
OAuth2 authentication and API wrapper for Schwab Trader API.
Modified to work with GitHub Actions using environment variables.

Features:
- OAuth2 flow with automatic token refresh
- Supports SCHWAB_REFRESH_TOKEN environment variable for cloud deployment
- Real-time quotes and option chains

Usage:
    from schwab_api import SchwabAPI

    api = SchwabAPI()
    if api.is_authenticated():
        quotes = api.get_quotes(['AAPL', 'NVDA'])
"""

import os
import json
import base64
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import Optional, Dict, List
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load from environment variables (for GitHub Actions)
SCHWAB_APP_KEY = os.environ.get('SCHWAB_APP_KEY', '')
SCHWAB_APP_SECRET = os.environ.get('SCHWAB_APP_SECRET', '')
SCHWAB_REFRESH_TOKEN = os.environ.get('SCHWAB_REFRESH_TOKEN', '')
SCHWAB_CALLBACK_URL = os.environ.get('SCHWAB_CALLBACK_URL', 'https://127.0.0.1:8000/callback')
SCHWAB_AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
SCHWAB_API_BASE = "https://api.schwabapi.com"

# Token file (for local use) - check multiple locations
_script_dir = os.path.dirname(os.path.abspath(__file__))

def _find_token_file():
    """Find schwab_tokens.json in multiple locations"""
    locations = [
        os.path.join(_script_dir, 'schwab_tokens.json'),  # Same folder as script
        r'C:\biotech-options-v2\schwab_tokens.json',      # Windows biotech folder
        '/mnt/c/biotech-options-v2/schwab_tokens.json',   # WSL biotech folder
    ]
    for loc in locations:
        if os.path.exists(loc):
            return loc
    return locations[0]  # Default to script dir

TOKEN_FILE = _find_token_file()


class SchwabAPI:
    """Schwab API client with OAuth2 authentication"""

    def __init__(self):
        self.app_key = SCHWAB_APP_KEY
        self.app_secret = SCHWAB_APP_SECRET
        self.callback_url = SCHWAB_CALLBACK_URL
        self.auth_url = SCHWAB_AUTH_URL
        self.token_url = SCHWAB_TOKEN_URL
        self.api_base = SCHWAB_API_BASE

        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.account_numbers = []

        # Load saved tokens or use environment variable
        self._load_tokens()

    def _load_tokens(self):
        """Load tokens from file or environment variable"""
        # First try loading from file (local development)
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    expiry = data.get('token_expiry')
                    if expiry:
                        self.token_expiry = datetime.fromisoformat(expiry)
                    self.account_numbers = data.get('account_numbers', [])
                    print("Loaded tokens from file")
                    return
            except Exception as e:
                print(f"Error loading tokens from file: {e}")

        # Fall back to environment variable (GitHub Actions)
        if SCHWAB_REFRESH_TOKEN:
            print("Using SCHWAB_REFRESH_TOKEN from environment")
            self.refresh_token = SCHWAB_REFRESH_TOKEN
            # We don't have an access token yet, it will be refreshed on first use

    def _save_tokens(self):
        """Save tokens to file (only in local mode)"""
        # Don't save in cloud mode - we use env var
        if not os.path.exists(TOKEN_FILE) and SCHWAB_REFRESH_TOKEN:
            print("Running in cloud mode - not saving tokens to file")
            return

        try:
            data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_expiry': self.token_expiry.isoformat() if self.token_expiry else None,
                'account_numbers': self.account_numbers,
                'saved_at': datetime.now().isoformat()
            }
            with open(TOKEN_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving tokens: {e}")

    def is_configured(self) -> bool:
        """Check if API credentials are configured"""
        configured = bool(self.app_key and self.app_secret)
        if not configured:
            print(f"API not configured - APP_KEY: {'set' if self.app_key else 'missing'}, APP_SECRET: {'set' if self.app_secret else 'missing'}")
        return configured

    def is_authenticated(self) -> bool:
        """Check if we have valid tokens"""
        if not self.is_configured():
            return False

        # If we have a valid access token, use it
        if self.access_token:
            if self.token_expiry and datetime.now() >= self.token_expiry:
                # Token expired, try to refresh
                return self._refresh_access_token()
            return True

        # No access token but have refresh token - try to get one
        if self.refresh_token:
            return self._refresh_access_token()

        return False

    def _refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            print("No refresh token available")
            return False

        try:
            credentials = f"{self.app_key}:{self.app_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()

            headers = {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }

            print("Refreshing access token...")
            response = requests.post(self.token_url, headers=headers, data=data)

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')

                # Some APIs return new refresh token
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data['refresh_token']

                expires_in = token_data.get('expires_in', 1800)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

                print("Access token refreshed successfully")
                self._save_tokens()
                return True
            else:
                print(f"Token refresh failed: {response.status_code}")
                print(f"Response: {response.text}")
                self.access_token = None
                return False

        except Exception as e:
            print(f"Error refreshing token: {e}")
            return False

    def _api_request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> Optional[Dict]:
        """Make authenticated API request"""
        if not self.is_authenticated():
            print("Not authenticated - cannot make API request")
            return None

        url = f"{self.api_base}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, json=data)
            else:
                return None

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # Token expired, try refresh
                if self._refresh_access_token():
                    return self._api_request(method, endpoint, params, data)
                return None
            else:
                print(f"API error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            print(f"API request error: {e}")
            return None

    # ===== MARKET DATA =====

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote for single symbol"""
        result = self._api_request('GET', f'/marketdata/v1/quotes/{symbol}')
        if result and symbol in result:
            return result[symbol]
        return result

    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get quotes for multiple symbols"""
        if not symbols:
            return {}

        # Schwab API accepts comma-separated symbols
        symbols_str = ','.join(symbols)
        result = self._api_request('GET', '/marketdata/v1/quotes',
                                   params={'symbols': symbols_str})
        return result or {}

    def get_option_chain(self, symbol: str,
                         contract_type: str = 'ALL',
                         strike_count: int = 10,
                         include_quotes: bool = True,
                         from_date: str = None,
                         to_date: str = None,
                         expiration_date: str = None) -> Optional[Dict]:
        """Get option chain for symbol"""
        params = {
            'symbol': symbol,
            'contractType': contract_type,
            'strikeCount': strike_count,
            'includeQuotes': str(include_quotes).lower()
        }

        if from_date:
            params['fromDate'] = from_date
        if to_date:
            params['toDate'] = to_date
        if expiration_date:
            params['fromDate'] = expiration_date
            params['toDate'] = expiration_date

        result = self._api_request('GET', '/marketdata/v1/chains', params=params)
        return result

    def get_option_quote(self, symbol: str, strike: float, expiration: str,
                         option_type: str = 'CALL') -> Optional[Dict]:
        """Get quote for specific option contract"""
        # Build option symbol (OCC format)
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        exp_str = exp_date.strftime('%y%m%d')
        strike_str = f"{int(strike * 1000):08d}"
        opt_type = 'C' if option_type.upper() == 'CALL' else 'P'

        # Pad symbol to 6 chars
        padded_symbol = f"{symbol:<6}"
        option_symbol = f"{padded_symbol}{exp_str}{opt_type}{strike_str}"

        return self.get_quote(option_symbol)


def test_connection():
    """Test Schwab API connection"""
    api = SchwabAPI()

    print("Schwab API Connection Test")
    print("=" * 40)
    print(f"APP_KEY: {'set' if SCHWAB_APP_KEY else 'missing'}")
    print(f"APP_SECRET: {'set' if SCHWAB_APP_SECRET else 'missing'}")
    print(f"REFRESH_TOKEN: {'set' if SCHWAB_REFRESH_TOKEN else 'missing'}")
    print(f"Configured: {api.is_configured()}")
    print(f"Authenticated: {api.is_authenticated()}")

    if api.is_authenticated():
        # Test getting a quote
        quote = api.get_quote('AAPL')
        if quote:
            print(f"\nAAPL Quote:")
            print(f"  Last: ${quote.get('lastPrice', 'N/A')}")
            print(f"  Bid: ${quote.get('bidPrice', 'N/A')}")
            print(f"  Ask: ${quote.get('askPrice', 'N/A')}")
            return True
    return False


if __name__ == "__main__":
    test_connection()
