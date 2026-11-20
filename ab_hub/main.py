"""Entrypoint do pacote AB-hub."""

from ab_hub.cli.app import app

__all__ = ["app"]

# Permite: python -m ab_hub
if __name__ == "__main__":
    app()
