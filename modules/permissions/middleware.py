from typing import Callable, Optional

from modules.permissions.rbac import user_has_permission
from modules.audit.logger import audit_log


class AuthorizationMiddleware:
    def __init__(self):
        self._checks: list[tuple[str, str, str]] = []

    def require(self, resource: str, action: str, username: Optional[str] = None):
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                effective_user = username or kwargs.get("username")
                if not effective_user:
                    audit_log(
                        username="unknown",
                        action=f"{resource}:{action}",
                        resource=resource,
                        status="denied",
                        details="Usuário não informado",
                    )
                    raise PermissionError("Usuário não autenticado")

                if not user_has_permission(effective_user, resource, action):
                    audit_log(
                        username=effective_user,
                        action=f"{resource}:{action}",
                        resource=resource,
                        status="denied",
                        details="Permissão negada",
                    )
                    raise PermissionError(
                        f"Usuário '{effective_user}' não tem permissão para {action} em {resource}"
                    )

                return func(*args, **kwargs)

            return wrapper

        return decorator


_middleware = AuthorizationMiddleware()


def authorize(resource: str, action: str):
    return _middleware.require(resource, action)
