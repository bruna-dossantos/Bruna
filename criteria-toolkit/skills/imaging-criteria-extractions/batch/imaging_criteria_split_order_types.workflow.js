export const meta = {
  name: 'imaging-criteria-split-order-types',
  description: 'Split a bundled order type into separate order types, one per distinct clinical pathway, where the branches carry DIFFERENT prerequisites; move each pathway-specific gate to only its pathway. Edits criteria.json only.',
  phases: [{ title: 'Split', detail: 'per policy: one order type per gated clinical pathway', model: 'opus' }],
}

const TARGETS = args.targets || []
if (!TARGETS.length) throw new Error('args must supply {targets:[{lcd,run_folder}]}')

const RESULT = {
  type: 'object', additionalProperties: false,
  required: ['lcd', 'json_valid', 'order_types_before', 'order_types_after', 'notes'],
  properties: {
    lcd: { type: 'string' },
    json_valid: { type: 'boolean' },
    order_types_before: { type: 'integer' },
    order_types_after: { type: 'integer' },
    notes: { type: 'string' },
  },
}

function prompt(t) {
  return `Restructure the order types for policy ${t.lcd} so each distinct CLINICAL PATHWAY is its own order type, instead of one order type that bundles several pathways together.

RUN FOLDER: ${t.run_folder}
EDIT: 2 - Working Files/${t.lcd}_criteria.json  (handle EVERY code in the file)
READ FOR CONTEXT: 4 - Human Outputs/${t.lcd}_criteria_by_code.md and the extracted policy text (${t.lcd}_policy.txt).

THE TEST FOR SPLITTING (apply per code): a bundled order type should become SEPARATE order
types only where the branches carry DIFFERENT PREREQUISITES — a required prior test, a
required prior therapy, a "need determined beforehand", or a distinct frequency rule. If every
alternative shares the same gate (e.g. a long list of ischemia signs, or a large covered-
diagnosis set), that is ONE pathway — keep it as a single order type with the OR inside one
indication criterion. Do NOT over-fragment homogeneous lists.

Pathways likely present in THIS policy's codes (split only the ones actually there):
- Venous 93970/93971: "Deep Vein Thrombosis (DVT) Evaluation" (carries the outpatient
  Wells-score/D-dimer prior-workup), "Chronic Venous Insufficiency", "Preoperative Vein
  Mapping" ("need for the procedure determined beforehand"; 93971 is the indicated
  unilateral/limited study, on 93970 keep a "document why a bilateral study is needed" note).
- Visceral 93975/93976: a general "Abdominal/Visceral Vascular" order type for the shared-gate
  indications, PLUS a separate order type for each branch with its OWN prerequisite —
  "Scrotal Duplex" (prior non-definitive conventional test), "Acute Mesenteric Ischemia" (the
  compound pain + minimal-exam-findings + leukocytosis gate), "Renovascular Hypertension"
  (failed first-line antihypertensive therapy). Aneurysm/graft surveillance that only differs
  by a frequency rule can stay in the general order type.
- Hemodialysis access 93990: "Hemodialysis Access Evaluation" (existing access WITH signs of
  compromise) vs "Preoperative Vessel Mapping" (before access creation) — the tangled
  "(C2 OR C6) AND (C3 OR C6)" logic is exactly this bundle; separate them.
- Arterial 93925 / carotid 93880: usually ONE pathway (shared gate) — leave as one order type
  unless a branch genuinely has its own distinct prerequisite.

FOR EACH new order type: SHARED criteria (covered diagnosis with its list_not_inlined call-out
intact, exclusion/screening gates, impact/management, frequency, documentation) + ONLY that
pathway's indication + ONLY that pathway's prerequisite, with pathway-specific gates CONVERTED
from conditional pass-throughs into clean direct requirements (drop the "applies only when…;
otherwise considered met" wording, since the order type now IS that pathway). Give each order
type a clean AND logic_expression. Keep every criterion's "n" UNIQUE WITHIN A CODE across its
order types (continue numbering across order types) so downstream keying by code+n cannot
collide. Everything stays reviewer PENDING, Tennr left-side format, every criterion source-
cited. Do NOT invent clinical content — only re-partition and de-conditionalize what is already
authored. Use the pathway name as the order_type label (becomes the JSON "variation").

Edit ONLY ${t.lcd}_criteria.json. Re-parse it with a JSON parser; set json_valid. Write
3 - Checks/${t.lcd}_split_order_types.md summarizing the new order types per code.
Return RESULT (order_types_before/after = total order-type count across all codes).`
}

phase('Split')
const rows = await parallel(TARGETS.map(t => () =>
  agent(prompt(t), { label: `split:${t.lcd}`, phase: 'Split', model: 'opus', effort: 'high', agentType: 'general-purpose', schema: RESULT })))
const ok = rows.filter(Boolean)
log(`split order types for ${ok.length}/${TARGETS.length} policies`)
return { split: ok }
