import os
import threading
import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.search import router as search_router
from app.api.analytics import router as analytics_router
from app.api.products import router as product_router

# ---------------------------------------------------------------------------
# DIAGNOSTIC: module-level identifiers
# Printed once per process/worker when this module is first imported.
# If this block appears N times in logs with different PIDs → N workers.
# If it appears N times with the SAME PID → module is being re-imported
# (circular import or reload), which would reset all singleton globals.
# ---------------------------------------------------------------------------
_LIFESPAN_COUNT = 0
_MODULE_LOAD_PID = os.getpid()
_MODULE_LOAD_TIME = datetime.datetime.utcnow().isoformat()

print(
    f"\n[main.py MODULE IMPORT]"
    f" pid={_MODULE_LOAD_PID}"
    f" time={_MODULE_LOAD_TIME}"
    f" WEB_CONCURRENCY={os.environ.get('WEB_CONCURRENCY', 'not set')}"
    f" PORT={os.environ.get('PORT', 'not set')}",
    flush=True,
)


def _rss_mb() -> str:
    """Return current process RSS in MB, or 'unavailable'."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return f"{int(line.split()[1]) / 1024:.1f} MB"
    except Exception:
        pass
    try:
        import psutil
        return f"{psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB"
    except Exception:
        pass
    return "unavailable"


# ---------------------------------------------------------------------------
# DIAGNOSTIC MIDDLEWARE: logs every OPTIONS request BEFORE CORSMiddleware
# runs, so we can see exactly what the browser sent.
# This middleware is added AFTER CORSMiddleware (meaning it runs BEFORE it
# in the Starlette middleware stack — outermost = last added).
# ---------------------------------------------------------------------------
class OptionsDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            print(
                f"\n[OPTIONS DEBUG] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                f"\n  method:  {request.method}"
                f"\n  url:     {request.url}"
                f"\n  path:    {request.url.path}"
                f"\n  Origin:  {request.headers.get('origin', '<MISSING>')}"
                f"\n  Access-Control-Request-Method:  {request.headers.get('access-control-request-method', '<MISSING>')}"
                f"\n  Access-Control-Request-Headers: {request.headers.get('access-control-request-headers', '<MISSING>')}"
                f"\n  Host:    {request.headers.get('host', '<MISSING>')}"
                f"\n  All headers: {dict(request.headers)}"
                f"\n[OPTIONS DEBUG] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
                flush=True,
            )

        response: Response = await call_next(request)

        if request.method == "OPTIONS":
            print(
                f"\n[OPTIONS DEBUG RESPONSE] >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                f"\n  status:  {response.status_code}"
                f"\n  url:     {request.url}"
                f"\n  response headers: {dict(response.headers)}"
                f"\n[OPTIONS DEBUG RESPONSE] <<<<<<<<<<<<<<<<<<<<<<<<<<<<",
                flush=True,
            )

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _LIFESPAN_COUNT
    _LIFESPAN_COUNT += 1

    pid = os.getpid()
    count = _LIFESPAN_COUNT
    thread = threading.current_thread().name
    ts = datetime.datetime.utcnow().isoformat()

    print(
        f"\n[LIFESPAN START #{count}]"
        f" pid={pid}"
        f" app_id={id(app)}"
        f" thread={thread}"
        f" time={ts}"
        f" module_load_pid={_MODULE_LOAD_PID}"
        f" same_process={'YES' if pid == _MODULE_LOAD_PID else 'NO-NEW-PROCESS'}"
        f" WEB_CONCURRENCY={os.environ.get('WEB_CONCURRENCY', 'not set')}"
        f" rss={_rss_mb()}",
        flush=True,
    )

    # ------------------------------------------------------------------
    # PRE-LOAD: TextSearchService
    # ------------------------------------------------------------------
    from app.api.search import get_text_service, get_image_service

    rss_before = _rss_mb()
    print(
        f"[LIFESPAN #{count}] pid={pid} Loading TextSearchService... rss_before={rss_before}",
        flush=True,
    )
    try:
        svc = get_text_service()
        print(
            f"[LIFESPAN #{count}] pid={pid} TextSearchService ready. "
            f"id={id(svc)} rss_after={_rss_mb()}",
            flush=True,
        )
    except Exception as e:
        print(
            f"[LIFESPAN #{count}] pid={pid} TextSearchService FAILED: {e}",
            flush=True,
        )

    # ------------------------------------------------------------------
    # PRE-LOAD: ImageSearchService
    # ------------------------------------------------------------------
    rss_before = _rss_mb()
    print(
        f"[LIFESPAN #{count}] pid={pid} Loading ImageSearchService... rss_before={rss_before}",
        flush=True,
    )
    try:
        svc = get_image_service()
        print(
            f"[LIFESPAN #{count}] pid={pid} ImageSearchService ready. "
            f"id={id(svc)} rss_after={_rss_mb()}",
            flush=True,
        )
    except Exception as e:
        print(
            f"[LIFESPAN #{count}] pid={pid} ImageSearchService FAILED: {e}",
            flush=True,
        )

    # ------------------------------------------------------------------
    # DIAGNOSTIC: dump CORS config + registered routes at startup
    # ------------------------------------------------------------------
    print(
        f"\n[LIFESPAN #{count}] pid={pid} ===== CORS CONFIGURATION =====",
        flush=True,
    )
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            print(
                f"  allow_origins:      {middleware.kwargs.get('allow_origins', '<not set>')}"
                f"\n  allow_origin_regex: {middleware.kwargs.get('allow_origin_regex', '<not set>')}"
                f"\n  allow_methods:      {middleware.kwargs.get('allow_methods', '<not set>')}"
                f"\n  allow_headers:      {middleware.kwargs.get('allow_headers', '<not set>')}"
                f"\n  allow_credentials:  {middleware.kwargs.get('allow_credentials', '<not set>')}",
                flush=True,
            )
    print(
        f"\n[LIFESPAN #{count}] pid={pid} ===== REGISTERED ROUTES =====",
        flush=True,
    )
    for route in app.routes:
        methods = getattr(route, "methods", None)
        print(f"  {methods or 'N/A':30s} {route.path}", flush=True)
    print(
        f"[LIFESPAN #{count}] pid={pid} ================================\n",
        flush=True,
    )

    print(
        f"[LIFESPAN #{count}] pid={pid} Startup complete. "
        f"rss_final={_rss_mb()} Accepting requests.",
        flush=True,
    )

    yield

    print(
        f"[LIFESPAN #{count}] pid={pid} Shutdown.",
        flush=True,
    )


app = FastAPI(
    title="GenAI Product Discovery System",
    lifespan=lifespan,
)

# --- CORS middleware (original config — NOT modified) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gen-ai-group-project-git-main-adx19s-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Debug middleware: added AFTER CORS so it wraps OUTSIDE it ---
# Starlette processes middleware in reverse add-order, so this runs first.
app.add_middleware(OptionsDebugMiddleware)

app.include_router(search_router)
app.include_router(analytics_router)
app.include_router(product_router)


@app.get("/")
def root():
    return {
        "message": "Product Discovery API Running",
        "pid": os.getpid(),
        "lifespan_count": _LIFESPAN_COUNT,
        "rss": _rss_mb(),
    }