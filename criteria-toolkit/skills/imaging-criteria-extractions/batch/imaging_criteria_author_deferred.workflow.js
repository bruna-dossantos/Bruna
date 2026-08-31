export const meta = {
  name: 'imaging-criteria-author-deferred',
  description: 'Author the SME-deferred new CPT codes into each policy: read the SME review, add a full order type per deferred code (clone the nearest existing code for scope-variants; author fresh from the policy section for genuinely new indication sets). Edits criteria.json only; regeneration happens after.',
  phases: [{ title: 'Author codes', detail: 'per policy: add the deferred CPT order types to criteria.json', model: 'opus' }],
}

const TARGETS = args.targets || []
if (!TARGETS.length) throw new Error('args must supply {targets:[{lcd,run_folder,lcd_pdf}]}')

const RESULT = {
  type: 'object', additionalProperties: false,
  required: ['lcd', 'json_valid', 'codes_added', 'notes'],
  properties: {
    lcd: { type: 'string' },
    json_valid: { type: 'boolean' },
    codes_added: { type: 'array', items: { type: 'string' }, description: 'CPT codes newly authored into criteria.json' },
    notes: { type: 'string' },
  },
}

function prompt(t) {
  return `Author the SME-DEFERRED new CPT codes into policy ${t.lcd}. These are codes the LCD covers that were not in the original work-list; the SME review flagged them to add.

RUN FOLDER: ${t.run_folder}
SOURCE LCD PDF (authoritative): ${t.lcd_pdf || '(use the extracted policy text in the run folder)'}
READ:
- 3 - Checks/${t.lcd}_sme_review.json  (promote_to_criteria items — find the ones that require authoring a BRAND-NEW CPT code / order type)
- 3 - Checks/${t.lcd}_sme_applied.md    (its DEFER section lists the deferred codes)
- 2 - Working Files/${t.lcd}_criteria.json  (EDIT THIS — the interchange criteria)
- 4 - Human Outputs/${t.lcd}_criteria_by_code.md  (existing wording to mirror)
- the extracted policy text ${t.lcd}_policy.txt (run-folder root or 2 - Working Files) — for any genuinely new indication section

FOR EACH deferred new CPT code, add a new code entry (with one order type) to the correct group in criteria.json:
- SCOPE-VARIANT of an existing code (a limited / unilateral / bilateral / upper-vs-lower version — e.g. 93976 vs 93975, 93882 vs 93880, 93926/93930/93931 vs 93925, 77066 vs 77065): CLONE the nearest existing code's full criteria set, then adjust: the code, the description, and only the criteria whose wording is scope-specific (e.g. "limited study", "unilateral", "upper extremity"). Keep the covered-diagnosis list_not_inlined call-out pointing at the same ${t.lcd}_dx_codes.csv.
- GENUINELY NEW indication set that has its own policy section (e.g. transcranial Doppler 93886/93888/93890/93892/93893; cardiac CT structure 75572 / congenital 75573; hemodialysis-access 93990): AUTHOR fresh criteria from that policy section, in Tennr left-side format (declarative; numbered "at least one of the following (1 or 2 or 3): …" for OR; "The patient does NOT have any of the following: …" exclusion gates; conditional criteria end with the pass-through; always "patient"; notes inline; every criterion source-cited to the LCD section). Reference the covered dx via list_not_inlined to ${t.lcd}_dx_codes.csv unless the policy clearly assigns a different code group.

RULES:
- Author ONLY the codes the SME review actually deferred for THIS policy. If none, return codes_added: [] and change nothing.
- Give each new order type a full logic_expression (C1 AND C2 AND …). Everything reviewer PENDING. Never inline a large code set.
- Edit ONLY ${t.lcd}_criteria.json. Re-parse it with a JSON parser afterward; set json_valid accordingly.
- Write 3 - Checks/${t.lcd}_added_codes.md listing each code added and whether it was cloned or authored fresh.

Return RESULT.`
}

phase('Author codes')
const rows = await parallel(TARGETS.map(t => () =>
  agent(prompt(t), { label: `authcode:${t.lcd}`, phase: 'Author codes', model: 'opus', effort: 'high', agentType: 'general-purpose', schema: RESULT })))
const ok = rows.filter(Boolean)
log(`authored deferred codes for ${ok.length}/${TARGETS.length} policies`)
return { authored: ok }
