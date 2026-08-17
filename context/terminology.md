# Terminology & shorthand

## Bruna's shorthand
- **criteria** = qualification criteria for HCPCS codes
- **payors / payers** = insurance companies
- **DR** = direct report
- **1:1** = one-on-one meeting with a direct report
- **SKU channel** = Slack channel for a specific product (e.g. `#sku-infusion`)
- **Garcia** = RevOps analytics skill (named after a person/concept)
- **GYLT** = "Get Your Life Together", the original EA skill-development project (archived)

## Domain terms
- **HCPCS code** — the billing code for an item or drug (e.g. E0601 for a PAP device). The top-level unit criteria are organized around.
- **Order type** — the qualification unit: one code + one payer + its own criteria. A code splits into many order types when payer rules differ, or stays one with internal OR logic when they don't.
- **Prior authorization (prior auth / PA)** — the payer's approval a provider must get before an item is covered.
- **DME** — durable medical equipment. **Infusion** — infused/injectable drugs. **PAP** — sleep/airway devices.
- **Payer / policy** — the insurer and the coverage rules it publishes (Medicare LCD/NCD + articles, Medicaid, Medicare Advantage, commercial CPBs).
- **RCM** — revenue cycle management: claims, denials, eligibility, billing, the money side of care.
- **CARC / RARC** — the standardized reason codes on a claim denial.

See [[tennr]] for how these fit together and [[sources-of-truth]] for where the authoritative data lives.
