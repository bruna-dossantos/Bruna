export const meta = {
  name: 'imaging-criteria-sme-accept',
  description: 'Healthcare-SME accept/reject pass over finished criteria run folders: review operational definitions, auto-accepted coverage gaps, and the extraction review worklist; record accept/reject; and flag any clinical detail that belongs IN a criterion (promote-to-criteria). Writes a decisions file per policy.',
  phases: [
    { title: 'SME Review', detail: 'per policy: an SME agent accepts/rejects opdefs + gaps + extraction rows and flags promote-to-criteria', model: 'opus' },
  ],
}

const TARGETS = args.targets || []
if (!TARGETS.length) throw new Error('args must supply {targets:[{lcd,run_folder,theme,payer,lcd_pdf}]}')

const RESULT = {
  type: 'object', additionalProperties: false,
  required: ['lcd', 'wrote_files', 'opdef_accept', 'opdef_revise', 'opdef_reject',
             'gap_confirm_oos', 'gap_promote', 'gap_real_miss', 'promote_to_criteria_count', 'promote_headlines', 'verdict'],
  properties: {
    lcd: { type: 'string' },
    wrote_files: { type: 'boolean', description: 'true if the _sme_review.json and .md were written to 3 - Checks/' },
    opdef_accept: { type: 'integer' }, opdef_revise: { type: 'integer' }, opdef_reject: { type: 'integer' },
    gap_confirm_oos: { type: 'integer', description: 'gaps confirmed genuinely out-of-scope' },
    gap_promote: { type: 'integer', description: 'gaps that are actually clinical detail belonging in a criterion' },
    gap_real_miss: { type: 'integer', description: 'gaps that are a real coverage miss needing a new criterion' },
    promote_to_criteria_count: { type: 'integer' },
    promote_headlines: { type: 'array', items: { type: 'string' }, description: 'short one-line description of each promote-to-criteria item' },
    verdict: { type: 'string', enum: ['clean', 'needs_promotions', 'needs_rework'] },
  },
}

function prompt(t) {
  return `You are a healthcare SME (Medicare medical-necessity + imaging/vascular policy) doing an ACCEPT/REJECT review of a finished, model-authored criteria draft. Everything is currently reviewer:PENDING and nothing has been human-accepted. Be rigorous; you are the sign-off gate.

POLICY: ${t.lcd} — ${t.theme} (${t.payer})
RUN FOLDER: ${t.run_folder}
SOURCE LCD PDF (authoritative): ${t.lcd_pdf || '(use the extracted policy text in the run folder)'}

READ (in the run folder):
- 2 - Working Files/${t.lcd}_rule_inventory.json  (every policy rule, classified)
- 4 - Human Outputs/${t.lcd}_criteria_by_code.md   (the authored criteria)
- 3 - Checks/${t.lcd}_resolutions.json             (operational definitions folded into criteria)
- 3 - Checks/${t.lcd}_accepted_gaps.json + 3 - Checks/${t.lcd}_close_loop_report.md  (auto-accepted / flagged gaps)
- 3 - Checks/${t.lcd}_extraction_review.md + .csv  (recall-concept accept/reject worklist)
- the extracted policy text ${t.lcd}_policy.txt (run-folder root or 2 - Working Files)

DO FOUR THINGS:
1. OPERATIONAL DEFINITIONS — for each entry in resolutions.json, decide accept / revise / reject. A definition is acceptable only if it is faithful to the policy and clinically correct (right time window, right positives/negatives, sensible missing-data handling). Note any that are wrong or invented.
2. AUTO-ACCEPTED GAPS — for each gap the close-loop auto-accepted (or listed as NEEDS REVIEW), classify it: confirm_out_of_scope (credentialing/billing/citation/boilerplate — legitimately not a patient-qualification criterion), promote_to_criterion (it is real clinical detail that belongs IN a criterion), or real_miss (a genuine coverage gap needing a brand-new criterion). accepted_gaps.json being empty means NOTHING was actually signed off — you are doing it now.
3. EXTRACTION WORKLIST — spot-check the must_author and ungrounded rows in the extraction_review: for each, say whether a field should be authored, or whether that detail actually belongs in the CRITERION logic (not an extraction recall field). Do NOT hand-verify the fuzzy_icd rows one by one — just note the count as a bulk task.
4. PROMOTE-TO-CRITERIA — THE KEY OUTPUT. List every clinical detail that is currently missing from or under-captured in the criteria and should be encoded as criterion logic — whether it surfaced as a gap, an extraction row, or a policy rule the criteria under-cover. For each, give: what it is, which code/criterion it belongs in, the policy basis (cite the LCD section), and a suggested Tennr-format criterion sentence.

WRITE two files into "${t.run_folder}/3 - Checks/":
- ${t.lcd}_sme_review.json  — {opdefs:[{term,decision,note}], gaps:[{id,decision,note}], extraction:[{field,decision,note}], promote_to_criteria:[{what,code,criterion,policy_basis,suggested_text}], verdict, summary}
- ${t.lcd}_sme_review.md    — a readable version, promote_to_criteria first.
Use real newlines. Do not modify any other file. Do not edit the criteria themselves — this pass only RECORDS decisions.

Then return RESULT with the counts and a promote_headlines array (one short line per promote-to-criteria item). verdict: clean (accept all, nothing to promote) / needs_promotions (details must move into criteria) / needs_rework (definitions wrong or major coverage miss).`
}

phase('SME Review')
const rows = await parallel(TARGETS.map(t => () =>
  agent(prompt(t), { label: `sme:${t.lcd}`, phase: 'SME Review', model: 'opus', effort: 'high', agentType: 'general-purpose', schema: RESULT })))

const ok = rows.filter(Boolean)
log(`SME-reviewed ${ok.length}/${TARGETS.length} policies`)
return { reviewed: ok }
