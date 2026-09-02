export const meta = {
  name: 'imaging-criteria-batch',
  description: 'Generate Tennr criteria across many policies at once: per policy author criteria + resolutions (Opus), run the deterministic downstream to a finished draft package, verify independently (Opus), then a batch dashboard.',
  phases: [
    { title: 'Author', detail: 'per policy: extract text, author criteria.json + resolutions in Tennr format, run close_loop --best-effort --render --organize', model: 'opus' },
    { title: 'QA', detail: 'independent skeptic verifies each finished run', model: 'opus' },
    { title: 'Summary', detail: 'roll up a batch dashboard', model: 'haiku' },
  ],
}

// ---- config (paths are absolute; args supplies the work-list) ----
// Resolve the skill root portably: explicit arg > installed-plugin env var > repo dev fallback.
const PLUGIN_ROOT = (typeof process !== 'undefined' && process.env && process.env.CLAUDE_PLUGIN_ROOT) || ''
const SKILL = args.skill_root
  || (PLUGIN_ROOT ? `${PLUGIN_ROOT}/skills/full-criteria-factory` : '')
  || '/Users/brunadossantos/Claude/os/plugins/full-criteria-factory/skills/full-criteria-factory'
const PYV = SKILL + '/.venv/bin/python'   // venv: docx/pdf/pdfplumber (run setup.sh once per install)
const ROOT = args.root                     // batch output root dir
const POLICIES = args.policies || []       // [{lcd,title,payer,ncd_baseline,article,service_line,plan_category,theme,codes:[...],pdfs:[...],codes_csv?}]

if (!ROOT || !POLICIES.length) throw new Error('args must supply {root, policies:[…]}')

// ---- structured-output schemas ----
const AUTHOR_RESULT = {
  type: 'object', additionalProperties: false,
  required: ['lcd', 'ok', 'run_folder', 'converged', 'n_criteria', 'n_pending', 'n_clinical_gaps', 'codes_count', 'codes_source', 'explorer_built', 'notes'],
  properties: {
    lcd: { type: 'string' },
    ok: { type: 'boolean', description: 'true if a run folder was produced' },
    run_folder: { type: 'string', description: 'absolute path to the organized run folder, or "" on failure' },
    converged: { type: 'string', description: 'the close-loop Converged line' },
    n_criteria: { type: 'integer' },
    n_pending: { type: 'integer', description: 'auto-stubbed terms + auto-accepted gaps needing review' },
    n_clinical_gaps: { type: 'integer' },
    codes_count: { type: 'integer' },
    codes_source: { type: 'string', enum: ['provided', 'extracted-PENDING', 'none'] },
    explorer_built: { type: 'boolean' },
    notes: { type: 'string', description: 'anything a reviewer must know (short)' },
  },
}
const QA_RESULT = {
  type: 'object', additionalProperties: false,
  required: ['lcd', 'verdict', 'coverage_ok', 'format_ok', 'checksum_ok', 'top_issues'],
  properties: {
    lcd: { type: 'string' },
    verdict: { type: 'string', enum: ['pass', 'review', 'fail'] },
    coverage_ok: { type: 'boolean', description: 'every clinical rule in the inventory is covered' },
    format_ok: { type: 'boolean', description: 'criteria follow Tennr left-side format (declarative numbered AND/OR, exclusion gates, patient terminology)' },
    checksum_ok: { type: 'boolean', description: 'machine copy code checksum passed (or n/a)' },
    top_issues: { type: 'array', items: { type: 'string' }, description: 'ranked, most important first; empty if clean' },
  },
}

function authorPrompt(p) {
  const out = `${ROOT}/${p.lcd}_flat`
  const rulePdfs = [p.lcd_pdf, ...(p.ncd_pdfs || [])].filter(Boolean)
  const kind = p.codes_kind || 'covered'   // 'covered' | 'noncovered' (negative policy)
  return `You are authoring Tennr qualification criteria for ONE Medicare policy, then running the deterministic downstream to a finished draft package. Work headlessly; do not ask questions.

POLICY: ${p.lcd} — ${p.title || ''}
Payer: ${p.payer || 'Medicare'} | NCD baseline: ${p.ncd_baseline || 'none'} | Article: ${p.article || 'none'}
Codes to cover (author criteria for each): ${JSON.stringify(p.codes)}
Rule-source PDFs (LCD + NCD — use for policy text + the explorer overlay): ${JSON.stringify(rulePdfs)}
Article PDF (code tables — use ONLY for the dx code set): ${p.article_pdf || '(none)'}
${p.codes_csv ? `Authoritative dx code CSV (use as --codes): ${p.codes_csv}` : 'No dx code CSV provided — extract the covered ICD-10 set from the Article PDF (see step 2).'}
Flat working dir (create it): ${out}

READ FIRST (the format + schema you must follow):
- ${SKILL}/SKILL.md  (esp. "Interchange format", "Core principles" incl. the Tennr left-side format, and Steps 0/2/3/10)
- ${SKILL}/authoring-rules/quality-rules.md  (the canonical left-side rules — READ THIS; it defines exclusions-as-gates, no-parentheticals, numbered AND/OR, patient terminology)
- ${SKILL}/examples/  (real criteria.json shapes)

STEPS (run from ${SKILL}; $PYV = ${PYV}, $PY = python3):
1. mkdir -p "${out}". Extract text from the RULE-SOURCE PDFs (LCD + NCD) with pdfplumber via $PYV into "${out}/${p.lcd}_policy.txt" (concatenate, label each). This is $SRC — the clinical rules live here, NOT in the Article.
2. CODE SET → "${out}/${p.lcd}_dx_codes.csv" (CSV header exactly: icd10_code,description):
   ${p.codes_csv ? `copy the provided authoritative CSV ${p.codes_csv} to that path (it is already in icd10_code,description form).` : `extract the covered ICD-10-CM codes from the Article PDF ("${p.article_pdf}") — the "ICD-10-CM Codes that Support Medical Necessity" / Group tables — with pdfplumber; dedupe; write rows as icd10_code,description. Record the count. This is PENDING review (parsing may be imperfect); prefer a provided authoritative CSV.`}
3. Step 0: $PY scripts/extract_policy_rules.py --policy "${out}/${p.lcd}_policy.txt" --out-json "${out}/${p.lcd}_rule_inventory.json" --out-md "${out}/${p.lcd}_rule_inventory.md"
4. AUTHOR "${out}/${p.lcd}_criteria.json" in the interchange schema. policy block = {lcd:"${p.lcd}", title, payer, ncd_baseline, article, service_line:"${p.service_line || ''}", plan_category:"${p.plan_category || 'MEDICARE'}"}. One entry per code in ${JSON.stringify(p.codes.map(c => c.code))} — author a full criteria set for EACH code (they share most criteria; vary by contrast/modality where the policy does). Cover EVERY clinical INDICATION/EXCLUSION/LIMITATION rule from the inventory.
   ${kind === 'noncovered' ? `CODE-SET IS NON-COVERED (negative policy): "${out}/${p.lcd}_dx_codes.csv" is the list of ICD-10 codes that do NOT support medical necessity. There is NO positive covered set. Author the diagnosis criterion as an EXCLUSION GATE — "The patient's sole indication is NOT one of the following non-covered diagnoses" — referencing the set via list_not_inlined {what:"non-covered ICD-10 (deny when sole indication)", count, location:"${p.lcd}_dx_codes.csv"}. build_machine_copy will inline these into the platform copy so the exclusion is enforceable.` : `CODE-SET IS COVERED: "${out}/${p.lcd}_dx_codes.csv" is the covered ICD-10 set; author the covered-diagnosis criterion normally, referencing it via list_not_inlined when too large.`} Tennr left-side format: declarative numbered AND/OR ("The patient's medical records must document at least one of the following (1 or 2 or 3): …"), exclusions as "The patient does NOT have any of the following: …" gates, conditional criteria end with a pass-through ("This requirement applies only when …; otherwise this criterion is considered met."), always "patient", notes inline (never parenthetical), every criterion source-cited, all reviewer PENDING. Inline verbatim code lists; if a set is too large, use a list_not_inlined {what,count,location:"${p.lcd}_dx_codes.csv"} call-out — never genericize.
5. Step 2: $PY scripts/build_order_types.py "${out}/${p.lcd}_criteria.json" --out "${out}/${p.lcd}_criteria.json"
6. Step 3: $PY scripts/resolve_ambiguous_terms.py detect "${out}/${p.lcd}_criteria.json" --out "${out}/${p.lcd}_terms.json"; author operational definitions for the decisive undefined terms into "${out}/${p.lcd}_resolutions.json" (schema per the resolver; every one reviewer PENDING). If none needed, write [].
7. echo '[]' > "${out}/${p.lcd}_accepted_gaps.json"
7b. EXTRACTION FIELDS (author these — the Tennr JSON defaults to them). Write "${out}/${p.lcd}_extraction_authored.json" = { "fields": { "<code>::<n>": [ {label, description, tag} ] } } covering every NON-pure-DOCUMENTATION criterion (key each code+criterion-number pair). Each field is PURE RETRIEVAL — "go get and find" — the decision variables a reviewer must pull to evaluate the criterion (e.g. a scanner-technology criterion → CT Scanner Type, Collimation Value, Rotational Speed, Number of Slices; a covered-diagnosis/indication criterion → one fetch-field per condition/finding/value). HARD RULE: a field's label/description may contain NO threshold or rule value (no ">=5", "<0.9", "or more", "at least 64", interval math), NO judgment word (qualifies, meets, abnormal, adequate, significant, severe, suspicion, appropriate), and NO conditional (if, when, whether, unless) — all logic stays in the criterion. Description = imperative "Find/Locate the … . May be recorded as …". tag ∈ {Medical Record, Diagnostic Test Result, Physician Written Order, Labs, EMR Info, Authorization, Letter of Medical Necessity, Insurance Verification, Proof of Delivery, Certification Statement, Reference Document} (clinical facts=Medical Record; imaging/scanner/contrast values=Diagnostic Test Result; the order=Physician Written Order; labs=Labs). Then grep the file for the banned words and fix any hit. close_loop (next step) auto-uses this file.
8. DOWNSTREAM (one command, best-effort always finishes + organizes):
   $PY scripts/close_loop.py "${out}/${p.lcd}_criteria.json" --inventory "${out}/${p.lcd}_rule_inventory.json" --resolutions "${out}/${p.lcd}_resolutions.json" --codes "${out}/${p.lcd}_dx_codes.csv" --accepted-gaps "${out}/${p.lcd}_accepted_gaps.json" --out-dir "${out}" --pyv ${PYV} --pdfs ${rulePdfs.map(x => `"${x}"`).join(' ')} --best-effort --organize --theme "${p.theme || p.title || p.lcd}" --payor "${p.payer || 'Medicare'}" --policy-id "${p.lcd}"
9. Locate the organized run folder (created by --organize under ${ROOT} or ${out}'s parent) and read its ${p.lcd}_close_loop_report.md for the Converged line + NEEDS REVIEW counts.

Return the AUTHOR_RESULT. n_pending = auto-stubbed terms + auto-accepted gaps from the close-loop report. codes_source = ${p.codes_csv ? "'provided'" : "'extracted-PENDING'"}. explorer_built = whether ${p.lcd}_criteria_explorer.html exists in the run folder. If any step hard-fails, set ok=false and put the error in notes.`
}

function qaPrompt(p, a) {
  return `Independently verify the finished criteria draft for policy ${p.lcd}. You did NOT author it. Be a skeptic.
Run folder: ${a.run_folder}
Checks:
1. Coverage — read the rule inventory (2 - Working Files/${p.lcd}_rule_inventory.json) and the coverage report (3 - Checks/${p.lcd}_coverage_gaps.md). Is every CLINICAL rule covered by a criterion? (coverage_ok)
2. Tennr format — open the criteria doc (4 - Human Outputs/${p.lcd}_criteria_by_code.md) and spot-check: declarative numbered AND/OR, exclusions as "does NOT have" gates, "patient" (never member/beneficiary), no parenthetical notes, every criterion source-cited. (format_ok)
3. Machine copy — did the code checksum pass (5 - Machine Outputs present, build did not abort)? If no code set applied, checksum_ok = true with a note. (checksum_ok)
4. Read the close-loop report NEEDS REVIEW section — list the most important things a human must fix.
Return QA_RESULT: verdict pass (clean) / review (drafts fine, needs human sign-off) / fail (broken or major coverage miss). top_issues ranked, most important first.`
}

phase('Author')
const authored = await pipeline(
  POLICIES,
  (p) => agent(authorPrompt(p), { label: `author:${p.lcd}`, phase: 'Author', model: 'opus', effort: 'high', agentType: 'general-purpose', schema: AUTHOR_RESULT }),
  (a, p) => (a && a.ok)
    ? agent(qaPrompt(p, a), { label: `qa:${p.lcd}`, phase: 'QA', model: 'opus', effort: 'high', agentType: 'general-purpose', schema: QA_RESULT }).then(qa => ({ ...a, qa }))
    : a,
)

const rows = authored.filter(Boolean)
log(`authored ${rows.length}/${POLICIES.length} policies`)

phase('Summary')
const summary = await agent(
  `Write a batch dashboard to "${ROOT}/_BATCH_SUMMARY.md" (and a simple self-contained "${ROOT}/_BATCH_SUMMARY.html"). One row per policy with: LCD, title, Converged, #criteria, #PENDING (needs review), #clinical gaps, codes (count + source: provided/extracted-PENDING/none), explorer built?, QA verdict, top QA issue, run-folder path. Add a short header: how many policies, how many passed QA vs need review vs failed, and a one-line "review these first" pointing at the worst. Keep it scannable. Here is the data:\n${JSON.stringify(rows, null, 2)}`,
  { label: 'batch-summary', phase: 'Summary', model: 'haiku', effort: 'low', agentType: 'general-purpose' },
)

return { policies: rows, summary_path: `${ROOT}/_BATCH_SUMMARY.md`, rows }
