export const meta = {
  name: 'imaging-criteria-apply-sme',
  description: 'Apply the SME accept-pass decisions to each policy: edit criteria.json + resolutions.json to fold in every promote-to-criteria DETAIL that refines an existing code, and apply the opdef revise decisions. Defers items that require a brand-new CPT code. Edits files only; regeneration happens after.',
  phases: [
    { title: 'Apply', detail: 'per policy: edit criteria.json + resolutions.json from the SME review', model: 'opus' },
  ],
}

const TARGETS = args.targets || []
if (!TARGETS.length) throw new Error('args must supply {targets:[{lcd,run_folder}]}')

const RESULT = {
  type: 'object', additionalProperties: false,
  required: ['lcd', 'json_valid', 'criteria_added', 'criteria_modified', 'opdefs_revised', 'deferred_new_codes', 'notes'],
  properties: {
    lcd: { type: 'string' },
    json_valid: { type: 'boolean', description: 'true if criteria.json + resolutions.json still parse after edits' },
    criteria_added: { type: 'integer' },
    criteria_modified: { type: 'integer' },
    opdefs_revised: { type: 'integer' },
    deferred_new_codes: { type: 'array', items: { type: 'string' }, description: 'promote items skipped because they need a brand-new CPT/order type not already in criteria.json' },
    notes: { type: 'string' },
  },
}

function prompt(t) {
  return `Apply the SME accept-pass decisions to policy ${t.lcd}. You are editing the authored criteria in place — carefully, faithfully to the policy.

RUN FOLDER: ${t.run_folder}
READ:
- 3 - Checks/${t.lcd}_sme_review.json   (the decisions: promote_to_criteria[], opdefs[] with accept/revise/reject)
- 3 - Checks/${t.lcd}_sme_review.md      (readable rationale + suggested_text)
- 2 - Working Files/${t.lcd}_criteria.json   (the interchange criteria — EDIT THIS)
- 3 - Checks/${t.lcd}_resolutions.json       (operational definitions — EDIT THIS)
- 4 - Human Outputs/${t.lcd}_criteria_by_code.md  (for current wording/context)

APPLY, in the two JSON files only:
1. PROMOTE-TO-CRITERIA — for every promote_to_criteria item that refines an EXISTING code/order type already present in criteria.json: add a new criterion or modify an existing one, in the interchange schema ({n,title,type,definition,source,list_not_inlined}). Use the item's suggested_text, made Tennr left-side format (declarative; numbered "at least one of the following (1 or 2 or 3): …" for OR; "The patient does NOT have any of the following: …" for exclusion gates; conditional criteria end with "This requirement applies only when …; otherwise this criterion is considered met."; always "patient"; notes inline, never parenthetical; every criterion source-cited to the LCD/article section in policy_basis). When you ADD a criterion, append it with the next n and extend that order type's logic_expression with " AND C<n>". Keep covered-diagnosis list_not_inlined call-outs intact — never inline a big code set.
2. DEFER — if an item requires authoring a BRAND-NEW CPT code / order type that is NOT already in criteria.json (e.g. a code the work-list didn't scope), DO NOT author it. Add its code(s) to deferred_new_codes and skip.
3. OPERATIONAL DEFINITIONS — for each opdefs entry with decision 'revise', update that term's operational_definition in resolutions.json per the note (fix the rule/positives/negatives/time-window as the SME described). Leave 'accept' entries unchanged; there should be no 'reject'.

RULES:
- Edit ONLY ${t.lcd}_criteria.json and ${t.lcd}_resolutions.json. Do not touch rendered docs, machine copies, or other files (they get regenerated afterward).
- After editing, re-read both files with a JSON parser to confirm they still parse. Set json_valid accordingly.
- Everything stays reviewer PENDING. Do not inline large code sets. Do not remove existing criteria unless an item explicitly says to fix a contradiction/stray definition.
- Write a short 3 - Checks/${t.lcd}_sme_applied.md listing exactly what you added/modified/revised and what you deferred.

Return RESULT.`
}

phase('Apply')
const rows = await parallel(TARGETS.map(t => () =>
  agent(prompt(t), { label: `apply:${t.lcd}`, phase: 'Apply', model: 'opus', effort: 'high', agentType: 'general-purpose', schema: RESULT })))

const ok = rows.filter(Boolean)
log(`applied SME edits to ${ok.length}/${TARGETS.length} policies`)
return { applied: ok }
