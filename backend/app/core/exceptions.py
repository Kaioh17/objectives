class AppError(Exception):
    """Domain error mapped to an HTTP response in main.py."""

    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class BadGatewayError(AppError):
    """An upstream service (Google) failed."""

    status_code = 502
