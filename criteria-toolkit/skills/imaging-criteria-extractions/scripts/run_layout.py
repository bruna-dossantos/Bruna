#!/usr/bin/env python3
"""
run_layout.py  —  single source of truth for how a run folder is organized.

One run (one policy) = one folder named for the product/service theme and payor,
with the policy ID appended when we have one:

    MRI Head & Neck - Medicare (L37373)/
    ├── README.md              ← START HERE (status + review list + file index)
    ├── 1 - Policy Source/     ← the source LCD / NCD / article PDFs
    ├── 2 - Working Files/     ← interchange criteria, rule inventory/locations, traceability data
    ├── 3 - Checks/            ← close-loop report, resolutions, accepted gaps, resolved, coverage
    ├── 4 - Human Outputs/     ← criteria doc(s), extraction doc(s), click-through traceability
    └── 5 - Machine Outputs/   ← platform JSON, machine md, extraction CSV, code files

`organize_run.py` and `close_loop.py --organize` both import this so the buckets
never drift between them.
"""

import re

# bucket keys → the subfolder name on disk (numbered so they sort in workflow order)
POLICY = "1 - Policy Source"
WORKING = "2 - Working Files"
CHECKS = "3 - Checks"
HUMAN = "4 - Human Outputs"
MACHINE = "5 - Machine Outputs"

SUBFOLDERS = [POLICY, WORKING, CHECKS, HUMAN, MACHINE]

# ordered (suffix → bucket); first suffix a filename endswith wins. Most-specific
# suffixes come first so e.g. *_criteria.PLATFORM.json never falls into *_criteria.json.
SUFFIX_MAP = [
    ("_criteria.PLATFORM.json", MACHINE),
    ("_criteria_MACHINE_full_codes.md", MACHINE),
    ("_criteria.resolved.json", CHECKS),
    ("_criteria_by_code.docx", HUMAN),
    ("_criteria_by_code.pdf", HUMAN),
    ("_criteria_by_code.md", HUMAN),
    ("_criteria.json", WORKING),
    ("_rule_inventory.json", WORKING),
    ("_rule_inventory.md", WORKING),
    ("_rule_locations.json", WORKING),
    ("_traceability.json", WORKING),
    ("_traceability.html", HUMAN),
    ("_close_loop_report.md", CHECKS),
    ("_resolutions.json", CHECKS),
    ("_accepted_gaps.json", CHECKS),
    ("_coverage_gaps.md", CHECKS),
    ("_resolver_report.md", CHECKS),
    ("_ambiguous_terms.json", CHECKS),
    ("_extraction_fields_by_code.docx", HUMAN),
    ("_extraction_fields_by_code.md", HUMAN),
    ("_extraction_fields_by_code.pdf", HUMAN),
    ("_extraction_fields.csv", MACHINE),
    ("_group1_dx_codes.csv", MACHINE),
    ("_group1_dx_codes.json", MACHINE),
    ("_group1_dx_codes.txt", MACHINE),
]


def bucket_for(filename):
    """Return the subfolder a generated file belongs in, or None if unrecognized.

    Any unrecognized *.pdf is treated as a policy source (the LCD/NCD/article);
    everything else unrecognized returns None (left in place, flagged in README).
    """
    name = filename
    for suffix, bucket in SUFFIX_MAP:
        if name.endswith(suffix):
            return bucket
    if name.lower().endswith(".pdf"):
        return POLICY
    return None


_SAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def run_folder_name(theme, payor, policy_id=None):
    """`Theme - Payor (ID)` when an ID is present, else `Theme - Payor`.

    Per the naming rule: include the policy identifier when we have one; when we
    don't, the caller should pass a more specific payor (e.g. plan / line of
    business) so two runs for the same payer can't collide.
    """
    base = f"{theme.strip()} - {payor.strip()}"
    if policy_id and str(policy_id).strip():
        base += f" ({str(policy_id).strip()})"
    return _SAFE.sub("-", base).strip()
