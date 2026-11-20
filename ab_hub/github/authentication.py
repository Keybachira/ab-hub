"""GitHub authentication helpers with resilient storage backends."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Optional

from ab_hub.core.config import get_settings
from ab_hub.core.exceptions import AuthenticationError
from ab_hub.core.logger import get_logger

logger = get_logger(__name__)

SERVICE_NAME = "ab-hub"
USERNAME = "github-token"


def _config_dir() -> Path:
    """User config directory for AB-hub credentials."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = base / "ab-hub"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _token_file() -> Path:
    return _config_dir() / "credentials.json"


def _read_file_token() -> Optional[str]:
    path = _token_file()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        token = data.get("github_token")
        return token.strip() if isinstance(token, str) and token.strip() else None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read credential file: %s", exc)
        return None


def _write_file_token(token: str) -> None:
    path = _token_file()
    data = {"github_token": token, "storage": "file"}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        # Restrict permissions on Unix
        if os.name != "nt":
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except Exception:  # noqa: BLE001
        pass


def _delete_file_token() -> bool:
    path = _token_file()
    if path.exists():
        path.unlink(missing_ok=True)
        return True
    return False


def _keyring_get() -> Optional[str]:
    try:
        import keyring
        token = keyring.get_password(SERVICE_NAME, USERNAME)
        return token.strip() if token else None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Keyring get unavailable: %s", exc)
        return None


def _keyring_set(token: str) -> bool:
    try:
        import keyring
        keyring.set_password(SERVICE_NAME, USERNAME, token)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("Keyring set unavailable: %s", exc)
        return False


def _keyring_delete() -> bool:
    try:
        import keyring
        keyring.delete_password(SERVICE_NAME, USERNAME)
        return True
    except Exception:  # noqa: BLE001
        return False


def get_token() -> Optional[str]:
    """
    Retrieve GitHub token from (in order):
    1. GITHUB_TOKEN environment variable
    2. AB_HUB_GITHUB_TOKEN / settings (.env)
    3. System keyring
    4. Local config file (~/.config/ab-hub/credentials.json)
    """
    # 1. Environment
    token = os.getenv("GITHUB_TOKEN") or os.getenv("AB_HUB_GITHUB_TOKEN")
    if token and token.strip():
        return token.strip()

    # 2. Settings / .env
    try:
        settings = get_settings()
        if settings.github_token and settings.github_token.strip():
            return settings.github_token.strip()
    except Exception:  # noqa: BLE001
        pass

    # 3. Keyring
    token = _keyring_get()
    if token:
        return token

    # 4. File fallback
    return _read_file_token()


def set_token(token: str) -> str:
    """
    Store token securely.
    Tries keyring first; falls back to a restricted local file.
    Returns the storage backend used: "keyring" | "file"
    """
    token = token.strip()
    if not token:
        raise AuthenticationError("O token não pode estar vazio.")

    # Basic format sanity check (don't reject fine-grained tokens)
    if len(token) < 20:
        raise AuthenticationError(
            "O token parece demasiado curto. Cole um Token de Acesso Pessoal do GitHub completo."
        )

    if _keyring_set(token):
        # Also clear any old file token to avoid confusion
        _delete_file_token()
        logger.info("Token stored in system keyring")
        return "keyring"

    # Fallback to file
    try:
        _write_file_token(token)
        logger.info("Token stored in local config file (keyring unavailable)")
        return "ficheiro"
    except Exception as exc:  # noqa: BLE001
        raise AuthenticationError(
            f"Não foi possível guardar o token (keyring e ficheiro falharam): {exc}"
        ) from exc


def delete_token() -> None:
    """Remove stored credentials from all backends."""
    _keyring_delete()
    removed_file = _delete_file_token()
    if removed_file:
        logger.info("Token removed from local config file")
    else:
        logger.info("Logout completed")


def require_token() -> str:
    """Return a valid token or raise a clear AuthenticationError."""
    token = get_token()
    if not token:
        raise AuthenticationError(
            "Nenhum token GitHub encontrado.\n"
            "  → Execute:  ab-hub autenticacao entrar\n"
            "  → Ou defina a variável de ambiente:  export GITHUB_TOKEN=ghp_..."
        )
    return token


def token_source() -> str:
    """Indica de onde vem o token actual (para o UI de estado)."""
    if os.getenv("GITHUB_TOKEN") or os.getenv("AB_HUB_GITHUB_TOKEN"):
        return "ambiente"
    try:
        settings = get_settings()
        if settings.github_token:
            return "ficheiro_env"
    except Exception:  # noqa: BLE001
        pass
    if _keyring_get():
        return "keyring"
    if _read_file_token():
        return "ficheiro"
    return "nenhum"
