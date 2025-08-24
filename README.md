# NextGen API Python Library

A Python client library for the NextGen Healthcare API.

## Setup
1. Copy `.env.example` to `.env`
2. Add your NextGen API credentials
3. Install dependencies: `pip install -r requirements.txt`

## Usage
```python
from nextgen_api import NextGenClient

client = NextGenClient()
codes = client.master.get_codes()