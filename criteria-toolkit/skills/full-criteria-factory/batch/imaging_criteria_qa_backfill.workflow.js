export const meta = {
  name: 'imaging-criteria-qa-backfill',
  description: 'Backfill independent QA for finished criteria run folders that missed their QA verdict (transient failures), then regenerate one master batch dashboard across ALL run folders in the root.',
  phases: [
    { title: 'QA', detail: 'independent skeptic verifies each named run folder', model: 'opus' },
    { title: 'Dashboard', detail: 'roll up a master dashboard across every run folder', model: 'haiku' },
  ],
}

const ROOT = args.root
const TARGETS = args.targets || []   // [{lcd, run_folder}]
if (!ROOT) throw new Error('args must supply {root, targets:[{lcd,run_folder}]}')

const QA_RESULT = {
  type: 'object', additionalProperties: false,
  required: ['lcd', 'verdict', 'coverage_ok', 'format_ok', 'checksum_ok', 'top_issues'],
  properties: {
    lcd: { type: 'string' },
    verdict: { type: 'string', enum: ['pass', 'review', 'fail'] },
    coverage_ok: { type: 'boolean' },
    format_ok: { type: 'boolean' },
    checksum_ok: { type: 'boolean' },
    top_issues: { type: 'array', items: { type: 'string' } },
  },
}

function qaPrompt(t) {
  return `Independently verify the finished criteria draft for policy ${t.lcd}. You did NOT author it. Be a skeptic.
Run folder: ${t.run_folder}
Checks:
1. Coverage — read the rule inventory (2 - Working Files/${t.lcd}_rule_inventory.json) and the close-loop report (3 - Checks/${t.lcd}_close_loop_report.md). Is every CLINICAL rule covered by a criterion or an explicitly-accepted gap? (coverage_ok)
2. Tennr format — open the criteria doc (4 - Human Outputs/${t.lcd}_criteria_by_code.md) and spot-check: declarative numbered AND/OR, exclusions as "does NOT have" gates, "patient" (never member/beneficiary), no parenthetical notes, every criterion source-cited. (format_ok)
3. Machine copy — did the code checksum pass (5 - Machine Outputs present, build did not abort)? If no code set, checksum_ok=true with a note. (checksum_ok)
4. Read the close-loop report NEEDS REVIEW section — list the most important things a human must fix.
Return QA_RESULT: verdict pass (clean) / review (drafts fine, needs human sign-off) / fail (broken or major coverage miss). top_issues ranked, most important first.`
}

phase('QA')
const qa = await parallel(TARGETS.map(t => () =>
  agent(qaPrompt(t), { label: `qa:${t.lcd}`, phase: 'QA', model: 'opus', effort: 'high', agentType: 'general-purpose', schema: QA_RESULT })
    .then(v => ({ ...t, qa: v }))))

const rows = qa.filter(Boolean)
log(`backfilled QA for ${rows.length}/${TARGETS.length} policies`)

phase('Dashboard')
const dash = await agent(
  `Regenerate the MASTER batch dashboard for this criteria batch. Write "${ROOT}/_BATCH_SUMMARY.md" and a self-contained "${ROOT}/_BATCH_SUMMARY.html".
STEP 1: list every organized run folder directly under "${ROOT}" (folders whose name ends in "(L…)"). There should be ~22.
STEP 2: for EACH run folder, read "3 - Checks/<LCD>_close_loop_report.md" for the Converged line + NEEDS REVIEW counts, and note whether "4 - Human Outputs/<LCD>_criteria_explorer.html" exists and whether "5 - Machine Outputs/" has the PLATFORM.json.
STEP 3: fold in these freshly-backfilled QA verdicts (match by LCD):
${JSON.stringify(rows.map(r => ({ lcd: r.lcd, qa: r.qa })), null, 2)}
For any run folder NOT in that list, its QA verdict was already recorded in a per-wave summary — mark QA as "prior-wave" if you cannot determine it from the folder.
Build one scannable table: LCD, theme/payer (from folder name), Converged, #PENDING (needs review), codes count, explorer built?, QA verdict, top QA issue. Header: total policies, how many pass vs review vs fail, and a one-line "review these first" pointing at the worst (fails, then coverage_ok=false, then highest PENDING). Keep it scannable. Also list the one KNOWN-EXCLUDED policy at the bottom: L36460 (CGS Bone Mass) — skipped, its LCD source PDF was not in the input folder.`,
  { label: 'master-dashboard', phase: 'Dashboard', model: 'haiku', effort: 'low', agentType: 'general-purpose' },
)

return { qa_backfilled: rows, dashboard: `${ROOT}/_BATCH_SUMMARY.md` }
