


from fastapi import Request, Response
from fastapi.responses import JSONResponse

from jonex_core.common.config import get_config


def _valid_internal_tokens() -> set[str]:

    raw = get_config().LLMGW_INTERNAL_TOKENS
    if not raw:
        return set()
    return {t.strip() for t in raw.split(",") if t.strip()}


async def token_swap(request: Request, call_next):


    if request.url.path == "/health":
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    api_key_header = request.headers.get("X-API-Key", "")

    incoming = ""
    if auth_header.startswith("Bearer "):
        incoming = auth_header[len("Bearer "):].strip()
    elif api_key_header:
        incoming = api_key_header.strip()

    valid_tokens = _valid_internal_tokens()
    if not incoming or (valid_tokens and incoming not in valid_tokens):
        return JSONResponse(
            {"error": "unauthorized", "message": "Invalid internal token"},
            status_code=401,
        )

    request.state.token_id = incoming
    return await call_next(request)