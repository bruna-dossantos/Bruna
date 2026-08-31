export const meta = {
  name: 'imaging-criteria-author-extraction',
  description: 'For each criterion in a policy, author the extraction fields as the DECISION VARIABLES a reviewer must pull from the chart to evaluate it (not just ontology concepts). Writes a code::n -> [fields] map per policy; the Tennr JSON is rebuilt from it afterward.',
  phases: [{ title: 'Author fields', detail: 'per policy: derive extraction fields from each criterion', model: 'opus' }],
}

const TARGETS = args.targets || []
if (!TARGETS.length) throw new Error('args must supply {targets:[{lcd,run_folder}]}')

const RESULT = {
  type: 'object', additionalProperties: false,
  required: ['lcd', 'wrote', 'criteria_covered', 'fields_total', 'notes'],
  properties: {
    lcd: { type: 'string' },
    wrote: { type: 'boolean' },
    criteria_covered: { type: 'integer' },
    fields_total: { type: 'integer' },
    notes: { type: 'string' },
  },
}

const TAGS = 'Medical Record, Diagnostic Test Result, Physician Written Order, Labs, EMR Info, Authorization, Letter of Medical Necessity, Insurance Verification, Proof of Delivery, Certification Statement, Reference Document'

function prompt(t) {
  return `Author the EXTRACTION FIELDS for every clinical criterion in policy ${t.lcd}. An extraction field is a specific piece of information a reviewer must pull from the chart to decide whether the criterion is met. The current fields are weak — they only captured ontology nouns (e.g. "Cardiac CT") and missed the decision variables. Fix that.

RUN FOLDER: ${t.run_folder}
READ:
- 3 - Checks/${t.lcd}_criteria.resolved.json  (authoritative: each code, each criterion's n / type / title / definition)
- 4 - Human Outputs/${t.lcd}_criteria_by_code.md  (readable version)

AN EXTRACTION FIELD IS PURE RETRIEVAL — a "go get and find" instruction. It locates a raw data element in the chart and returns it. It contains NO decision, NO reasoning, NO threshold, NO judgment. The criterion (already written) holds ALL the logic; the field only fetches the inputs the criterion needs.

HARD RULE — a field's label or description may NEVER contain:
- any threshold or rule value: no ">=5", "<0.9", ">200 mm Hg", "at least 64-slice", "12 months or less", "within 6 months".
- any evaluative / judgment word: no qualifies, meets, satisfies, abnormal, normal, significant, adequate, sufficient, severe, high, low, elevated, positive/negative-as-judgment, suspicion, appropriate.
- any conditional / decision word: no if, when, whether, unless, provided that.
It ONLY names the data point and where/how it is written. If you catch yourself describing what makes the value pass, delete that clause.

CORRECT PATTERN (from the platform): criterion "The sleep study reports an AHI of 5 or greater" -> field { label: "Apnea-Hypopnea Index (AHI)", description: "Find the apnea-hypopnea index value reported on the sleep study. May be recorded as AHI, apnea hypopnea index, RDI." }. The number 5 stays in the CRITERION, never in the field.

FOR EACH criterion that is NOT a pure DOCUMENTATION criterion, list the raw inputs the criterion needs, each fetched literally:
- Measurement / methodology criterion (e.g. scanner >=64-slice / collimation <=0.625mm / rotation <=375msec): one field per raw value — "CT Scanner Type or Model", "Number of Slices or Detectors", "Collimation Value", "Rotational Speed / Gantry Rotation Time". Description = "Find/Locate the <value> documented for the study" (units like 'mm' are fine as a formatting cue; the threshold is NOT).
- Covered-diagnosis / indication criterion: a field per condition, finding, or value to FIND — "Find documentation of claudication…", "Find the ankle-brachial index (ABI) value…", "Find the interarm systolic blood pressure…". Retrieve the finding or number; never say it "qualifies", is "abnormal", or crosses a threshold.
- Exclusion criterion: a field to FIND the presence/text of each named thing — "Find documentation that the study was ordered for screening", "Find documentation of a planned angiography". Locate presence only; the criterion decides exclusion.
- Frequency / prior-study criterion: "Find the date of the prior study", "Find the number of prior studies", "Find the date of the procedure" — dates and counts only, no interval math.
Be thorough: if a criterion lists 6 alternative indications, that is several fetch-fields, not one.

EACH field = { "label": neutral Title Case name of the data point (no judgment words), "description": imperative "Find/Locate the … . May be recorded as … / look in …" — RETRIEVAL ONLY, with synonym cues and where it appears, and NONE of the banned content above, "tag": one of [${TAGS}] — where the data is documented (clinical facts = Medical Record; imaging/scanner/contrast values = Diagnostic Test Result; the order = Physician Written Order; lab values = Labs) }.

WRITE the result to "${t.run_folder}/3 - Checks/${t.lcd}_extraction_authored.json" as:
{ "fields": { "<code>::<n>": [ {label, description, tag}, … ], … } }
Key EVERY covered clinical criterion by its code and criterion number n (e.g. "75574::7"). One code may repeat criteria across order types — key each (code, n) pair that appears. Use real newlines. Validate the file parses as JSON.

Return RESULT (criteria_covered = number of code::n keys written; fields_total = total fields across all keys).`
}

phase('Author fields')
const rows = await parallel(TARGETS.map(t => () =>
  agent(prompt(t), { label: `xfields:${t.lcd}`, phase: 'Author fields', model: 'opus', effort: 'high', agentType: 'general-purpose', schema: RESULT })))
const ok = rows.filter(Boolean)
log(`authored extraction fields for ${ok.length}/${TARGETS.length} policies`)
return { authored: ok }
