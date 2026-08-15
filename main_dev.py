"""main_dev.py

Run the API for local development with SSL verification disabled for this
process only. This is useful *only* for local debugging when you are behind a
corporate SSL-intercepting proxy. DO NOT use in production.

Usage:

    python main_dev.py

This file sets an unverified SSL context for the Python process and then
starts Uvicorn using the `app` defined in `main.py`.
"""

import ssl
# DEV ONLY: disable SSL verification for this process
ssl._create_default_https_context = ssl._create_unverified_context

from main import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
