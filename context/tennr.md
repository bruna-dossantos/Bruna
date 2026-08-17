# Tennr — what the company does

Tennr automates **prior authorization** for healthcare providers.

The core workflow, in plain terms:
1. A customer (a healthcare provider) submits medical records.
2. Tennr's AI extracts the relevant data from those records.
3. It checks that data against **qualification criteria** — the rules a payer (insurance company) requires to approve a given item.
4. Rules are organized by **HCPCS code** — the billing code for a piece of equipment or a drug (e.g. DME equipment, infusion drugs, PAP/sleep devices, imaging).

## The unit of work: qualification criteria
Bruna's team writes and maintains these criteria. A single "order type" is one code + one payer + its own criteria. When a code's rules differ by payer, it splits into many order types; when they're the same, it can be one with internal OR logic. See [[terminology]].

## How work is tracked
All criteria work is tracked in **Linear**. Two main teams: **DME Criteria** and **Infusion Criteria**. Hierarchy: parent issue (HCPCS code) → child issues (code + payer combos) → customer needs (linked to a customer project). See [[systems]] and [[sources-of-truth]].
