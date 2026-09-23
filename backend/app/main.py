from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.limiter import limiter
from app.api.routes import router


app = FastAPI(
    title="Intelligent Analytics Query Engine",
    version="1.0.0",
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.include_router(router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "rate_limiting": "enabled",
        "storage": "redis",
    }