"""Shared helpers for the linear-customer-onboarding skill scripts.

Keeps GraphQL transport, rate-limit handling, and path resolution in one
place so the per-stage scripts stay focused on their step.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = "https://api.linear.app/graphql"
TOKEN_PATH = os.path.expanduser("~/.linear_token")

DESKTOP        = os.path.expanduser("~/Desktop")
MASTER_DIR     = os.path.join(DESKTOP, "Linear Master Data")
CUSTOMERS_DIR  = os.path.join(DESKTOP, "Customers")

# Estimates
PARENT_ESTIMATE   = 2  # S
CUSTOMER_ESTIMATE = 1  # XS


def get_token():
    if not os.path.exists(TOKEN_PATH):
        sys.exit(f"missing {TOKEN_PATH} — write your Linear personal API "
                 f"token there (one line, no prefix)")
    return open(TOKEN_PATH).read().strip()


def gql(query, variables=None, token=None):
    """Single GraphQL request. Returns the parsed JSON or raises."""
    token = token or get_token()
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Authorization": token, "Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=30)


def gql_with_retry(query, variables, token, on_rate_limit_msg=""):
    """GraphQL request with full Linear-aware retry policy.

    Handles:
      - HTTP 429 (sleeps Retry-After or 60s)
      - HTTP 400 with extensions.code=RATELIMITED (Linear's hourly-cap
        signal — sleeps 60min, resumes)
      - HTTP 5xx (exponential backoff up to 30s)
      - GraphQL `extensions.code=RATELIMITED` errors (sleeps 30s)
      - URLError / TimeoutError (exponential backoff)

    Returns the parsed JSON `data` field, or raises RuntimeError on a
    permanent failure.
    """
    backoff = 1.0
    for _ in range(8):
        try:
            resp = gql(query, variables, token)
            data = json.loads(resp.read().decode())
            if "errors" in data:
                err = data["errors"][0]
                msg = err.get("message", "")
                code = err.get("extensions", {}).get("code")
                if "rate" in msg.lower() or code == "RATELIMITED":
                    print(f"  rate-limited (gql); sleep 30s {on_rate_limit_msg}",
                          file=sys.stderr)
                    time.sleep(30); continue
                raise RuntimeError(f"GraphQL error: {msg}")
            return data["data"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                ra = e.headers.get("Retry-After")
                s = int(ra) if ra and ra.isdigit() else 60
                print(f"  HTTP 429; sleep {s}s", file=sys.stderr)
                time.sleep(s); continue
            if e.code >= 500:
                print(f"  HTTP {e.code}; backoff {backoff:.1f}s",
                      file=sys.stderr)
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            body = e.read().decode("utf-8", errors="replace")
            # Linear returns hourly-cap 'RATELIMITED' as HTTP 400, not 429.
            # Sleep ~hourly window then resume.
            if e.code == 400 and "RATELIMITED" in body:
                print(f"  HTTP 400 RATELIMITED (hourly cap); sleep 60min",
                      file=sys.stderr)
                time.sleep(3600); continue
            raise RuntimeError(f"HTTP {e.code}: {body}")
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  network error {e}; backoff {backoff:.1f}s",
                  file=sys.stderr)
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
            continue
    raise RuntimeError("Exhausted retries")


def customer_dir(name):
    """Path to ~/Desktop/Customers/<name>/, validated."""
    p = os.path.join(CUSTOMERS_DIR, name)
    if not os.path.isdir(p):
        sys.exit(f"customer folder not found: {p}\n"
                 f"create it with `mkdir -p \"{p}\"` and put input.csv inside")
    return p


def load_config(name):
    """Read customer_config.json. Exits with helpful error if missing."""
    cfg_path = os.path.join(customer_dir(name), "customer_config.json")
    if not os.path.exists(cfg_path):
        sys.exit(f"missing {cfg_path}\n"
                 f"see SKILL.md step 2 — create with team / customer_id / "
                 f"customer_project_id")
    return json.load(open(cfg_path))


def team_labels_path(team):
    """team in {dme, infusion} → master labels CSV path."""
    fname = {"dme": "dme_team_labels.csv",
             "infusion": "infusion_team_labels.csv"}.get(team)
    if not fname:
        sys.exit(f"unknown team: {team!r}; expected 'dme' or 'infusion'")
    p = os.path.join(MASTER_DIR, fname)
    if not os.path.exists(p):
        sys.exit(f"missing {p} — run refresh_linear_data.py first")
    return p


def insurance_projects_path():
    p = os.path.join(MASTER_DIR, "insurance_projects.csv")
    if not os.path.exists(p):
        sys.exit(f"missing {p} — run refresh_linear_data.py first")
    return p


def workflow_states_path():
    p = os.path.join(MASTER_DIR, "workflow_states.csv")
    if not os.path.exists(p):
        sys.exit(f"missing {p} — run refresh_linear_data.py first")
    return p
