"""Excepções personalizadas do AB-hub."""


class ABHubError(Exception):
    """Excepção base para todos os erros do AB-hub."""


class AuthenticationError(ABHubError):
    """Levantada quando a autenticação falha ou o token está em falta/inválido."""


class ConfigurationError(ABHubError):
    """Levantada quando a configuração é inválida ou está em falta."""


class GitHubAPIError(ABHubError):
    """Levantada em problemas de comunicação com a API do GitHub."""

    def __init__(self, message: str, status_code: int | None = None, response: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(GitHubAPIError):
    """Levantada quando o limite de taxa do GitHub é excedido."""

    def __init__(self, message: str, reset_at: int | None = None):
        super().__init__(message, status_code=403)
        self.reset_at = reset_at


class RepositoryNotFoundError(ABHubError):
    """Levantada quando um repositório pedido não é encontrado localmente ou remotamente."""


class DatabaseError(ABHubError):
    """Levantada em falhas relacionadas com a base de dados."""


class ScanError(ABHubError):
    """Levantada quando uma operação de análise falha."""
