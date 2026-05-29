"""End-to-end tester for the deployed ALEP Intranet.

Runs a battery of checks against the live Railway backend + frontend and the
Supabase Storage media. Prints a human-readable report and exits with code 0
on full pass, 1 if anything failed.

Usage:
    python scripts/test_live_site.py
    python scripts/test_live_site.py --backend https://...  --frontend https://...

Designed to be the canonical "is the live site healthy?" check. Safe to run
on any machine that has `httpx` installed (or just stdlib if you remove the
httpx import — currently uses httpx for nicer HTTP handling).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Callable

import httpx

DEFAULT_BACKEND = "https://backend-production-2684.up.railway.app"
DEFAULT_FRONTEND = "https://frontend-production-372c.up.railway.app"
SUPABASE_ORIGIN = "https://jidnubbyrzprkkvrkycm.supabase.co"


# ---------- minimal test framework ----------


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    suggestion: str = ""


@dataclass
class Report:
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, r: CheckResult) -> None:
        self.checks.append(r)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def render(self) -> str:
        lines: list[str] = []
        n_pass = sum(1 for c in self.checks if c.passed)
        lines.append(
            f"\n{'='*72}\nTested {len(self.checks)} item(s) — "
            f"{n_pass} pass, {len(self.checks)-n_pass} fail"
            f"\n{'='*72}\n"
        )
        for c in self.checks:
            mark = "PASS" if c.passed else "FAIL"
            lines.append(f"[{mark}] {c.name}")
            if c.detail:
                for line in c.detail.splitlines():
                    lines.append(f"        {line}")
            if not c.passed and c.suggestion:
                lines.append(f"   -> suggestion: {c.suggestion}")
        return "\n".join(lines)


def check(name: str, suggestion: str = "") -> Callable:
    def deco(fn: Callable[..., tuple[bool, str]]):
        def wrapped(report: Report, *args, **kwargs):
            try:
                ok, detail = fn(*args, **kwargs)
            except Exception as e:
                ok, detail = False, f"exception: {type(e).__name__}: {e}"
            report.add(CheckResult(name=name, passed=ok, detail=detail, suggestion=suggestion))
            return ok

        return wrapped

    return deco


# ---------- individual checks ----------


@check(
    "backend /health returns {status: ok}",
    suggestion="Backend not deployed or env vars (DATABASE_URL/SECRET_KEY) missing. Check Railway logs.",
)
def check_backend_health(backend: str) -> tuple[bool, str]:
    r = httpx.get(f"{backend}/health", timeout=20)
    detail = f"HTTP {r.status_code} body={r.text[:80]}"
    return (r.status_code == 200 and r.json().get("status") == "ok"), detail


@check(
    "backend /api/v1/pages/tree returns 3 top-level sections",
    suggestion="Database may be empty (seed not run) or DATABASE_URL points at wrong DB.",
)
def check_backend_tree(backend: str) -> tuple[bool, str]:
    r = httpx.get(f"{backend}/api/v1/pages/tree", timeout=30)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}: {r.text[:120]}"
    data = r.json()
    if not isinstance(data, list):
        return False, f"unexpected payload: {str(data)[:120]}"
    titles = [n.get("title") for n in data]
    detail = f"top-level: {titles}"
    return (len(data) == 3), detail


@check(
    "backend /api/v1/pages/by-path/operacao-interna/seguros returns content",
    suggestion="Seed/import may not have populated content_blocks. Run import_extracted_content.py.",
)
def check_backend_page(backend: str) -> tuple[bool, str]:
    r = httpx.get(f"{backend}/api/v1/pages/by-path/operacao-interna/seguros", timeout=30)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}: {r.text[:120]}"
    data = r.json()
    blocks = data.get("blocks", [])
    body_len = len(blocks[0]["body"]) if blocks else 0
    detail = f"page='{data.get('page',{}).get('title')}' blocks={len(blocks)} first_body_len={body_len}"
    return (len(blocks) >= 1 and body_len > 200), detail


@check(
    "backend OpenAPI doc reachable",
    suggestion="If 404, FastAPI didn't start or API_V1_PREFIX is misconfigured.",
)
def check_backend_openapi(backend: str) -> tuple[bool, str]:
    r = httpx.get(f"{backend}/api/v1/openapi.json", timeout=20)
    return (r.status_code == 200), f"HTTP {r.status_code}"


@check(
    "frontend root returns HTML 200 from inside the container",
    suggestion="If 404 from Railway edge: container isn't bound to $PORT. If dist/index.html missing: build didn't run.",
)
def check_frontend_html(frontend: str) -> tuple[bool, str]:
    r = httpx.get(f"{frontend}/", timeout=30)
    is_html = "text/html" in r.headers.get("content-type", "")
    server = r.headers.get("server", "")
    body_snippet = r.text[:120].replace("\n", " ")
    edge_404 = (r.status_code == 404 and "railway-edge" in server.lower())
    detail = (
        f"HTTP {r.status_code} server='{server}' "
        f"len={len(r.text)} snippet={body_snippet!r}"
    )
    return (r.status_code == 200 and is_html and "<div id=\"app\"" in r.text), detail


@check(
    "frontend serves the JS bundle (production hashed asset)",
    suggestion="Vite build didn't produce /assets/index-*.js — check build logs on Railway.",
)
def check_frontend_bundle(frontend: str) -> tuple[bool, str]:
    r = httpx.get(f"{frontend}/", timeout=30)
    if r.status_code != 200:
        return False, f"root HTTP {r.status_code}"
    m = re.search(r'/assets/[A-Za-z0-9_./-]+\.js', r.text)
    if not m:
        return False, "no /assets/*.js reference found in index.html"
    asset_url = f"{frontend}{m.group(0)}"
    r2 = httpx.get(asset_url, timeout=30)
    return (r2.status_code == 200 and len(r2.content) > 1000), f"asset={m.group(0)} bytes={len(r2.content)}"


@check(
    "frontend → backend wiring: bundle references the backend URL",
    suggestion="VITE_API_URL was empty at build time. Verify the env var, then redeploy frontend.",
)
def check_frontend_api_wiring(frontend: str, backend: str) -> tuple[bool, str]:
    r = httpx.get(f"{frontend}/", timeout=30)
    if r.status_code != 200:
        return False, "frontend root not 200"
    m = re.search(r'/assets/[A-Za-z0-9_./-]+\.js', r.text)
    if not m:
        return False, "no JS bundle"
    bundle = httpx.get(f"{frontend}{m.group(0)}", timeout=30).text
    # The Vite-baked URL appears inside the bundle. Compare host (not exact path).
    backend_host = httpx.URL(backend).host
    if backend_host and backend_host in bundle:
        return True, f"bundle references '{backend_host}'"
    # Fallback: did Vite at least inline some Railway URL?
    found = re.findall(r"https://[A-Za-z0-9-]+\.up\.railway\.app", bundle)
    return (False, f"backend host '{backend_host}' not found in bundle; Railway URLs found in bundle: {set(found)}")


@check(
    "Supabase Storage image is publicly reachable",
    suggestion="Bucket may have been turned back to private. Set MediaGeral to Public in Supabase dashboard.",
)
def check_supabase_image() -> tuple[bool, str]:
    url = (
        f"{SUPABASE_ORIGIN}/storage/v1/object/public/MediaGeral/intranet/"
        "conhecimento-alep__historia-e-percurso__p4_n1.png"
    )
    r = httpx.head(url, timeout=20)
    ctype = r.headers.get("content-type", "")
    return (r.status_code == 200 and ctype.startswith("image/")), f"HTTP {r.status_code} ctype={ctype}"


@check(
    "browser flow: API call from frontend perspective (CORS preflight)",
    suggestion="If failing, BACKEND_CORS_ORIGINS doesn't include the frontend domain.",
)
def check_cors(frontend: str, backend: str) -> tuple[bool, str]:
    # Simulate a browser preflight: OPTIONS with Origin header.
    r = httpx.request(
        "OPTIONS",
        f"{backend}/api/v1/pages/tree",
        headers={
            "Origin": frontend.rstrip("/"),
            "Access-Control-Request-Method": "GET",
        },
        timeout=20,
    )
    allow_origin = r.headers.get("access-control-allow-origin", "")
    ok = r.status_code in (200, 204) and (allow_origin == frontend.rstrip("/") or allow_origin == "*")
    return ok, f"HTTP {r.status_code} allow-origin='{allow_origin}'"


# ---------- driver ----------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default=DEFAULT_BACKEND)
    ap.add_argument("--frontend", default=DEFAULT_FRONTEND)
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    print(f"Backend  : {args.backend}")
    print(f"Frontend : {args.frontend}\n")

    rep = Report()
    check_backend_health(rep, args.backend)
    check_backend_tree(rep, args.backend)
    check_backend_page(rep, args.backend)
    check_backend_openapi(rep, args.backend)
    check_frontend_html(rep, args.frontend)
    check_frontend_bundle(rep, args.frontend)
    check_frontend_api_wiring(rep, args.frontend, args.backend)
    check_supabase_image(rep)
    check_cors(rep, args.frontend, args.backend)

    if args.json:
        out = {
            "all_passed": rep.all_passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail, "suggestion": c.suggestion}
                for c in rep.checks
            ],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(rep.render())

    return 0 if rep.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
