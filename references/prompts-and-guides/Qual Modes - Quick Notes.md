# Qual Modes — Quick Reference Notes

*Compiled from Slack, Notion PRDs, Linear, and Google Drive — March 1, 2026*

---

## 🛡️ Full Qual (Current Experience)

- **Persona:** "Zero trust" reviewer — verifies every criterion manually, line by line
- **UX:** Accordion-style UI, user clicks through each criterion one-by-one before proceeding
- **Display:** All criteria, extraction fields, and reasoning shown by default
- **Use case:** Mirrors traditional checklist workflow against 40+ page policy documents
- **Best for:** Medical policy teams, prior auth workflows requiring detailed audit trails, customers who review everything
- **Customer examples:** Vivo, Nationwide (hand-wavy qual persona but leans toward full review)
- **Config:** Original default; new steps will shift to STANDARD_QUAL default post-release (QUA-1231)

---

## 🖱️ Standard Qual — "1-Click" (Balanced Path)

- **Persona:** Trusts Tennr's evaluations on met criteria; focuses attention on what actually needs human input
- **UX:** Auto-confirms met criteria → surfaces only unmet/uncertain items for review
- **Key changes from Full:**
  - Criteria reorganized by status: missing → not met → found (met collapsed by default)
  - No forced confirmation of already-met criteria
  - Auto-advance on action: collapse completed criterion, scroll to next needing attention
  - Saves ~30s per run by eliminating unnecessary confirmations
- **Extraction fields:** Renamed direction toward "info from document" or "supporting evidence" — current "extraction fields" terminology confuses users
- **Shipped:** Released in 7 days (target was 9) — live as of late Feb 2026
- **GA rollout:** April 2026 for broader customer base
- **Target customers:** Majority of users; MSC and Better Night identified as test customers
- **Config:** Singular dropdown in Qualification Hub Config → `STANDARD_QUAL`
- **Key tickets:** QUA-1062 (design exploration, done), QUA-1253 (intermediate loading screen, done), QUA-1252 (indexes for speed, done), QUA-1264 (multiple order types support, ready to build)
- **Known gaps:**
  - Unmet doc criteria in 1-click should drop into expanded unmet doc type for review (QUA-1268, post-MedTrade)
  - Customer-authored criteria ordering (future need)
  - QualHub settings page for display preferences (future)

---

## ⚡ Fast Qual — "0-Click / Zero-Click" (Fully Automated)

- **Persona:** "Full trust" — wants Tennr to auto-pilot the decision when everything is met
- **UX:** Zero user interaction required; auto-advances to next workflow step
- **Fallback:** Drops into 1-Click (Standard) if any criteria are unmet
- **Powered by:** "Speculative Evaluation" engine (Katie Pelton)
  - Doc criteria pre-loaded based on order type/codes → saves ~30s (GA Feb 6)
  - Medical criteria pre-loaded based on order type/codes/documents → saves 60+s (phased rollout Feb 24)
- **Status:** Merged to prod Feb 25, behind feature toggle
- **⚠️ Gating:** Must NOT be configured for customers until validated with qual team — not a fit for every customer
- **Good fit:**
  - Simple DME cases with automated doc types
  - Low-cost drugs feeding into PA submission
  - Consignment workflows with minimal qual requirements
  - Customers where all criteria are routinely fully met
- **Not a fit:**
  - Customers writing their own criteria (needs internal tracker)
  - Complex policy review workflows
- **Customer interest:** LMS wants zero-click demo; Pav confirmed demos ready via Jasper
- **Config:** Mode stored in `qualificationEvaluation` table + output JSON variable payload
- **Key tickets:** QUA-1142 (true no-pause auto-advance, done), QUA-1140 (mode in output JSON, done), QUA-1139 (qualification decision from speculative execution, done), QUA-1173 (configure by order type, pending), QUA-1172 (add to autopilot menu, pending)

---

## 🗡️ Fast PAR (Bonus Mode)

- **Tagline:** "For those who fear nothing"
- **Concept:** Zero-click in all cases — not just when criteria are fully met
- **Status:** Mentioned in roadmap; Jasper noted "one step beyond" fast qual with wider applicability
- **Scope:** Minimal details — separate from Fast Qual's "zero-click only when fully met" scope

---

## Key Dates & Milestones

| What | When | Status |
|------|------|--------|
| Speculative doc criteria | Feb 6, 2026 | ✅ GA |
| Speculative medical criteria | Feb 24, 2026 | ✅ Phased rollout |
| Zero-Click merged to prod | Feb 25, 2026 | ✅ Behind toggle |
| 1-Click Qual shipped | Feb 27, 2026 | ✅ Live |
| MedTrade demo | Feb 18-20, 2026 | ✅ Presented |
| Standard Qual GA | April 2026 | 🔜 Planned |
| Default new steps → STANDARD_QUAL | Post-release | 📋 QUA-1231 |

---

## Source Links

- **PRD (Cursor Plan):** https://www.notion.so/305eb680c7fc808fbe53e897dd930368
- **Qual Lite / Standard Mode:** https://www.notion.so/305eb680c7fc80669a47c4ff6d71eaed
- **Fast Qual Demo (MedTrade):** https://www.notion.so/312eb680c7fc806bad04c2f11c5b54b7
- **Qual Vertical Guide:** https://www.notion.so/2fdeb680c7fc80fa9cbfc84d4ee4b9ee
- **Bug Bash Notes:** https://www.notion.so/312eb680c7fc809399afd24d5f9cca5b
- **Linear Project (Qual Modes):** https://linear.app/tennr-product/project/5478a340-48ae-4822-a46e-0bca81f8ab56
