"""One error format for the whole API:
{"error": {"code": "...", "message": "...", "fields": [{"field": "email", "message": "..."}]}}"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class DomainError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def _friendly(err: dict) -> str:
    t, ctx = err.get("type", ""), err.get("ctx", {}) or {}
    if t == "missing":
        return "This field is required."
    if t == "string_too_short":
        n = ctx.get("min_length", 1)
        return "This field is required." if n == 1 else f"Must be at least {n} characters."
    if t == "string_too_long":
        return f"Must be at most {ctx.get('max_length')} characters."
    if "email" in t or "email" in err.get("msg", "").lower():
        return "Enter a valid email address."
    if t == "literal_error":
        return f"Invalid value. Allowed: {ctx.get('expected', '')}".replace("'", "")
    return err.get("msg", "Invalid value.")


def _error(status: int, code: str, message: str, fields=None) -> JSONResponse:
    body = {"error": {"code": code, "message": message}}
    if fields is not None:
        body["error"]["fields"] = fields
    return JSONResponse(status_code=status, content=body)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        fields = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": _friendly(e)} for e in exc.errors()]
        return _error(422, "validation_error", "Please fix the highlighted fields.", fields)

    @app.exception_handler(DomainError)
    async def _domain(_: Request, exc: DomainError):
        return _error(exc.status, exc.code, exc.message)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        return _error(exc.status_code, f"http_{exc.status_code}", str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        return _error(500, "internal_error", "Something went wrong on our side. Please try again.")
