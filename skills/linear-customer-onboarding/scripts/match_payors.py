#!/usr/bin/env python3
"""Generate top-K candidate Linear projects for each CSV payor.

This script does NOT make final matching decisions. It produces a
candidate list that the orchestrator (LLM, using the insurance-mapper
skill + references/payor_taxonomy.md) reviews and resolves into a
final payor_matches.csv.

Why candidates, not decisions:
  Pure fuzzy-string matching is wrong constantly for insurance payors —
  it can't disambiguate "Anthem BCBS" (CA vs CO vs CT vs ...), can't
  expand "BCBS" to "Blue Cross Blue Shield", can't notice that
  "Sunshine Health" is a Centene Florida Medicaid MCO (not the
  similarly-named "Sunshine State Healthplan"), can't distinguish
  Medicaid MCO vs Marketplace vs Medicare Advantage. Matching needs
  judgment and reference data, so this script just narrows the field
  and the LLM decides.

Reads:
  ~/Desktop/Customers/<name>/input.csv             (CSV Payor + state hints)
  ~/Desktop/Linear Master Data/insurance_projects.csv

Writes:
  ~/Desktop/Customers/<name>/payor_match_candidates.csv  (top-K w/ scores)
  ~/Desktop/Customers/<name>/payor_matches.csv           (auto-confirmed
                                                          rows + blanks
                                                          for review)

Auto-confirm only when:
  - top score >= 0.95
  - second-best is < 0.80 (clear winner)
  - no state hint in the input requires disambiguation

Everything else stays blank in payor_matches.csv with the candidate
list waiting in payor_match_candidates.csv. The orchestrator fills the
blanks via LLM judgment.

Usage:
  python3 match_payors.py "Comfort Medical"
  python3 match_payors.py "Comfort Medical" --top-k 5
"""
import argparse
import csv
import difflib
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import customer_dir, insurance_projects_path


# --- Acronym expansion ------------------------------------------------------
# Common payor acronyms. The LLM will catch the long tail; this list is just
# the high-frequency ones that fuzzy-string match can't see.
ACRONYM = {
    "bcbs":   "blue cross blue shield",
    "bsbc":   "blue cross blue shield",   # typo seen in source data
    "bcbsa":  "blue cross blue shield association",
    "bx":     "blue cross",
    "bs":     "blue shield",
    "uhc":    "unitedhealthcare",
    "uhg":    "unitedhealth group",
    "abh":    "aetna better health",
    "kp":     "kaiser permanente",
    "kfhp":   "kaiser foundation health plan",
    "csgs":   "cigna",                    # legacy abbrev
    "esi":    "express scripts",
    "ma":     "medicare advantage",
    "mco":    "managed care organization",
    "msho":   "minnesota senior health options",
    "snp":    "special needs plan",
    "dsnp":   "dual eligible special needs plan",
    "fchp":   "fallon community health plan",
    "tps":    "third party administrator",
}

# State name ⇄ abbreviation (lowercased). Used to detect state hints in
# both the input payor strings and the project names.
STATES = {
    "alabama":"al","alaska":"ak","arizona":"az","arkansas":"ar",
    "california":"ca","colorado":"co","connecticut":"ct","delaware":"de",
    "florida":"fl","georgia":"ga","hawaii":"hi","idaho":"id",
    "illinois":"il","indiana":"in","iowa":"ia","kansas":"ks",
    "kentucky":"ky","louisiana":"la","maine":"me","maryland":"md",
    "massachusetts":"ma","michigan":"mi","minnesota":"mn",
    "mississippi":"ms","missouri":"mo","montana":"mt","nebraska":"ne",
    "nevada":"nv","new hampshire":"nh","new jersey":"nj",
    "new mexico":"nm","new york":"ny","north carolina":"nc",
    "north dakota":"nd","ohio":"oh","oklahoma":"ok","oregon":"or",
    "pennsylvania":"pa","rhode island":"ri","south carolina":"sc",
    "south dakota":"sd","tennessee":"tn","texas":"tx","utah":"ut",
    "vermont":"vt","virginia":"va","washington":"wa",
    "west virginia":"wv","wisconsin":"wi","wyoming":"wy",
    "district of columbia":"dc","puerto rico":"pr",
}
STATE_ABBR = {v: k for k, v in STATES.items()}


def extract_state(s):
    """Pull state hints out of a payor or project name. Returns set of
    full state names found."""
    s = s.lower()
    found = set()
    for full in STATES:
        # match as a whole word (avoids matching "or" inside "florida")
        if re.search(rf"\b{re.escape(full)}\b", s):
            found.add(full)
    # 2-letter abbreviations bracketed by spaces, parens, or punctuation
    for abbr, full in STATE_ABBR.items():
        # avoid matching abbreviations inside larger words by requiring
        # boundary chars on both sides
        if re.search(rf"(?<![a-z]){abbr}(?![a-z])", s):
            found.add(full)
    return found


# --- Normalization ----------------------------------------------------------
NOISE_PREFIXES = ("dnu-", "dnu ", "old ", "legacy ", "do not use ", "do not use-")
NOISE_TOKENS   = {"the", "of", "inc", "inc.", "llc", "co", "company",
                  "corporation", "corp", "plan", "plans", "health",
                  "healthcare", "the", "a", "an"}

def expand_acronyms(s):
    out = []
    for tok in re.findall(r"[a-z0-9]+", s.lower()):
        out.append(ACRONYM.get(tok, tok))
    return " ".join(out)

def norm(s):
    s = (s or "").lower().strip()
    for prefix in NOISE_PREFIXES:
        if s.startswith(prefix):
            s = s[len(prefix):].lstrip()
    # acronym expansion BEFORE removing noise tokens, since expansion
    # may add 'health' etc.
    s = expand_acronyms(s)
    toks = [t for t in re.findall(r"[a-z0-9]+", s)
            if t not in NOISE_TOKENS]
    return " ".join(toks)


# --- Scoring ----------------------------------------------------------------
def token_jaccard(a, b):
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def score(payor_norm, proj_norm):
    """Combined score: 0.6 * sequence ratio + 0.4 * token jaccard."""
    if not payor_norm or not proj_norm:
        return 0.0
    seq = difflib.SequenceMatcher(None, payor_norm, proj_norm).ratio()
    jac = token_jaccard(payor_norm, proj_norm)
    return 0.6 * seq + 0.4 * jac


# --- Project + input loaders ------------------------------------------------
def load_projects():
    rows = []
    with open(insurance_projects_path()) as f:
        for r in csv.DictReader(f):
            name = r["Name"]
            rows.append({
                "name": name,
                "uuid": r["UUID"],
                "norm": norm(name),
                "states": extract_state(name),
            })
    return rows


def load_payors_with_hints(in_path):
    """Return {payor_string: {"count": int, "state_hints": set, "row": dict}}.
    state_hints are pulled from any column we can recognize: explicit
    'State' column, parens in the payor name itself, or 'Plan State'."""
    out = {}
    with open(in_path) as f:
        for r in csv.DictReader(f):
            p = (r.get("CSV Payor") or "").strip()
            if not p:
                continue
            d = out.setdefault(p, {"count": 0, "state_hints": set(),
                                   "sample_row": dict(r)})
            d["count"] += 1
            # pull explicit state column if present
            for col in ("State", "Plan State", "Payor State"):
                v = (r.get(col) or "").strip()
                if v:
                    d["state_hints"] |= extract_state(v)
            # pull from the payor name itself
            d["state_hints"] |= extract_state(p)
    return out


# --- Main -------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("customer_name")
    ap.add_argument("--top-k", type=int, default=5,
                    help="candidates per payor (default 5)")
    ap.add_argument("--auto-threshold", type=float, default=0.95,
                    help="top score required for auto-confirm (default 0.95)")
    ap.add_argument("--auto-margin", type=float, default=0.15,
                    help="min margin between top-1 and top-2 for auto "
                         "(default 0.15)")
    args = ap.parse_args()

    cdir = customer_dir(args.customer_name)
    in_path = os.path.join(cdir, "input.csv")
    if not os.path.exists(in_path):
        sys.exit(f"missing {in_path}")

    payors = load_payors_with_hints(in_path)
    projects = load_projects()
    print(f"loaded {sum(d['count'] for d in payors.values())} rows / "
          f"{len(payors)} unique payors / {len(projects)} projects",
          file=sys.stderr)

    cand_rows = []
    final_rows = []
    auto_confirmed = 0
    needs_review = 0
    no_match = 0

    for payor in sorted(payors):
        d = payors[payor]
        p_norm = norm(payor)
        scored = []
        for proj in projects:
            s = score(p_norm, proj["norm"])
            # state hint bonus / penalty: if input has a state hint and
            # project has different states named, push it down
            shared_states = d["state_hints"] & proj["states"]
            if d["state_hints"] and proj["states"]:
                if shared_states:
                    s += 0.10  # bonus for state alignment
                elif not shared_states:
                    s -= 0.20  # penalty for state collision
            scored.append((s, proj))
        scored.sort(key=lambda x: -x[0])
        top = scored[:args.top_k]

        for rank, (s, proj) in enumerate(top, 1):
            cand_rows.append({
                "CSV Payor":        payor,
                "N Rows":           d["count"],
                "State Hints":      ",".join(sorted(d["state_hints"])) or "",
                "Rank":             rank,
                "Candidate Project": proj["name"],
                "Candidate UUID":   proj["uuid"],
                "Score":            f"{s:.3f}",
                "Project States":   ",".join(sorted(proj["states"])) or "",
            })

        # Decide auto vs review
        top_score = top[0][0] if top else 0.0
        runner_up = top[1][0] if len(top) > 1 else 0.0
        margin    = top_score - runner_up
        decision  = "review"
        chosen_name, chosen_uuid = "", ""

        if top_score >= args.auto_threshold and margin >= args.auto_margin:
            # state guard: if input has a state hint and the chosen
            # project doesn't include it, force review even at high score
            if d["state_hints"] and top[0][1]["states"] and \
               not (d["state_hints"] & top[0][1]["states"]):
                decision = "review-state-mismatch"
            else:
                decision = "auto"
                chosen_name = top[0][1]["name"]
                chosen_uuid = top[0][1]["uuid"]
                auto_confirmed += 1

        if top_score < 0.50:
            decision = "no-match"
            no_match += 1
        elif decision == "review" or decision == "review-state-mismatch":
            needs_review += 1

        final_rows.append({
            "CSV Payor":      payor,
            "Matched Project": chosen_name,
            "Project UUID":   chosen_uuid,
            "Confidence":     f"{top_score:.3f}",
            "Decision":       decision,
            "Top Candidates": " | ".join(
                f"{p['name']} ({s:.2f})" for s, p in top[:3]),
            "State Hints":    ",".join(sorted(d["state_hints"])) or "",
            "N Rows":         d["count"],
        })

    # write candidates
    cpath = os.path.join(cdir, "payor_match_candidates.csv")
    with open(cpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "CSV Payor","N Rows","State Hints","Rank",
            "Candidate Project","Candidate UUID","Score","Project States"])
        w.writeheader(); w.writerows(cand_rows)

    # write final (with blanks where review needed)
    fpath = os.path.join(cdir, "payor_matches.csv")
    with open(fpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "CSV Payor","Matched Project","Project UUID","Confidence",
            "Decision","Top Candidates","State Hints","N Rows"])
        w.writeheader(); w.writerows(final_rows)

    print(f"\nwrote {cpath}", file=sys.stderr)
    print(f"wrote {fpath}", file=sys.stderr)
    print(f"  auto-confirmed:  {auto_confirmed}", file=sys.stderr)
    print(f"  needs review:    {needs_review}", file=sys.stderr)
    print(f"  no match (<.50): {no_match}", file=sys.stderr)
    if needs_review or no_match:
        print(f"\n  → hand the 'review' rows to the orchestrator (insurance-",
              file=sys.stderr)
        print(f"    mapper + references/payor_taxonomy.md). The candidates",
              file=sys.stderr)
        print(f"    list and state hints are in {cpath}.", file=sys.stderr)


if __name__ == "__main__":
    main()
