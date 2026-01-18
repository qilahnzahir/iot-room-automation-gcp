import os
import streamlit.web.cli as stcli
import sys

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        f"--server.port={port}",
        "--server.address=0.0.0.0",
        "--server.headless=true"
    ]
    sys.exit(stcli.main())
