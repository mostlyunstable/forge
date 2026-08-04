"""Application entry point."""

import uvicorn

from forge.presentation.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("forge.presentation.app:app", host="0.0.0.0", port=8000, reload=True)
