"""Convenience entry point: `python -m server.main` or `python server/main.py`."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8765, reload=True)
