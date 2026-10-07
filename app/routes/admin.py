"""Admin portal — password-protected, SMS internal use only.

Routes:
    GET  /admin                          → redirect to /admin/dashboard or /admin/login
    GET  /admin/login                    → login form
    POST /admin/login                    → validate password, set session cookie
    GET  /admin/logout                   → clear cookie, redirect to login
    GET  /admin/dashboard                → search log table
    GET  /admin/search/{key}             → full detail: raw JSON + summary
    GET  /admin/download/{key}/json      → download raw JSON file
    GET  /admin/download/{key}/csv       → download summary as CSV
    POST /admin/delete/{key}             → delete a search record

{key} is a URL-encoded Redis key (audit:{ts}:{cm_id}).

Auth: signed session cookie using itsdangerous (Starlette transitive dep).
      Cookie name: admin_session, value: signed "authenticated" token.
      If ADMIN_PASSWORD is not set, the portal returns 503.
"""

from __future__ import annotations

import csv
import io
import json
import secrets

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer, BadSignature

from app import config
from app.services import audit_log

router = APIRouter(prefix="/admin")

# Injected by main.py at startup
templates: Jinja2Templates | None = None

_COOKIE_NAME = "admin_session"
_COOKIE_VALUE = "authenticated"
_COOKIE_MAX_AGE = 60 * 60 * 8  # 8 hours


def _serializer() -> URLSafeSerializer:
    secret = config.ADMIN_PASSWORD or secrets.token_hex(32)
    return URLSafeSerializer(secret, salt="admin-cookie")


def _make_cookie(response: Response) -> None:
    token = _serializer().dumps(_COOKIE_VALUE)
    response.set_cookie(
        _COOKIE_NAME,
        token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,  # set to True when Railway HTTPS is confirmed
    )


def _clear_cookie(response: Response) -> None:
    response.delete_cookie(_COOKIE_NAME)


def _is_authenticated(request: Request) -> bool:
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        return False
    try:
        return _serializer().loads(token) == _COOKIE_VALUE
    except BadSignature:
        return False


def _check_configured() -> HTMLResponse | None:
    if not config.ADMIN_PASSWORD:
        return HTMLResponse(
            "<h1>503 — Admin portal not configured</h1>"
            "<p>Set the ADMIN_PASSWORD environment variable to enable the admin portal.</p>",
            status_code=503,
        )
    return None


def _login_redirect() -> RedirectResponse:
    return RedirectResponse("/admin/login", status_code=302)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_class=RedirectResponse)
async def admin_root():
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    err = _check_configured()
    if err:
        return err
    if _is_authenticated(request):
        return RedirectResponse("/admin/dashboard", status_code=302)
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, password: str = Form(...)):
    err = _check_configured()
    if err:
        return err
    if not secrets.compare_digest(password, config.ADMIN_PASSWORD):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Incorrect password."},
            status_code=401,
        )
    response = RedirectResponse("/admin/dashboard", status_code=302)
    _make_cookie(response)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse("/admin/login", status_code=302)
    _clear_cookie(response)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    err = _check_configured()
    if err:
        return err
    if not _is_authenticated(request):
        return _login_redirect()
    searches = await audit_log.fetch_all(limit=200)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "searches": searches},
    )


@router.get("/search/{encoded_key:path}", response_class=HTMLResponse)
async def search_detail(request: Request, encoded_key: str):
    err = _check_configured()
    if err:
        return err
    if not _is_authenticated(request):
        return _login_redirect()
    row = await audit_log.fetch_one(encoded_key)
    if not row:
        return HTMLResponse("<h1>404 — Record not found</h1>", status_code=404)
    try:
        raw_obj = json.loads(row["raw_json"])
        raw_pretty = json.dumps(raw_obj, indent=2, default=str)
    except Exception:
        raw_pretty = row.get("raw_json", "")
    return templates.TemplateResponse(
        "admin/detail.html",
        {"request": request, "row": row, "raw_pretty": raw_pretty},
    )


@router.get("/download/{encoded_key:path}/json")
async def download_json(request: Request, encoded_key: str):
    if not _is_authenticated(request):
        return _login_redirect()
    row = await audit_log.fetch_one(encoded_key)
    if not row:
        return HTMLResponse("<h1>404 — Record not found</h1>", status_code=404)
    try:
        raw_obj = json.loads(row["raw_json"])
        content = json.dumps(raw_obj, indent=2, default=str)
    except Exception:
        content = row.get("raw_json", "")
    filename = f"{row['artist_name'].replace(' ', '_')}_raw.json"
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/download/{encoded_key:path}/csv")
async def download_csv(request: Request, encoded_key: str):
    if not _is_authenticated(request):
        return _login_redirect()
    row = await audit_log.fetch_one(encoded_key)
    if not row:
        return HTMLResponse("<h1>404 — Record not found</h1>", status_code=404)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric", "value"])
    for line in row.get("summary", "").splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            metric, _, value = line.partition(":")
            writer.writerow([metric.strip(), value.strip()])
        else:
            writer.writerow([line, ""])
    filename = f"{row['artist_name'].replace(' ', '_')}_summary.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/delete/{encoded_key:path}")
async def delete_record(request: Request, encoded_key: str):
    if not _is_authenticated(request):
        return _login_redirect()
    await audit_log.delete_one(encoded_key)
    return RedirectResponse("/admin/dashboard", status_code=302)
