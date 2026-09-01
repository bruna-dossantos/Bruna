export const meta = {
  name: 'imaging-criteria-fill-field-gaps',
  description: 'Author retrieval-only extraction fields for a specific list of gap criteria (code::n keys missing from the authored map after an order-type split) and RETURN them as structured data; the caller merges them into the authored map.',
  phases: [{ title: 'Fill gaps', detail: 'per policy: author fields for the listed gap criteria', model: 'opus' }],
}

const TARGETS = args.targets || []
if (!TARGETS.length) throw new Error('args must supply {targets:[{lcd,run_folder}]}')

const RESULT = {
  type: 'object', additionalProperties: false,
  required: ['lcd', 'fields'],
  properties: {
    lcd: { type: 'string' },
    fields: {
      type: 'array',
      description: 'one entry per authored extraction field; key = the exact "code::n" from the gap list',
      items: {
        type: 'object', additionalProperties: false,
        required: ['key', 'label', 'description', 'tag'],
        properties: {
          key: { type: 'string' },
          label: { type: 'string' },
          description: { type: 'string' },
          tag: { type: 'string', enum: ['Medical Record', 'Diagnostic Test Result', 'Physician Written Order', 'Labs', 'EMR Info', 'Authorization', 'Letter of Medical Necessity', 'Insurance Verification', 'Proof of Delivery', 'Certification Statement', 'Reference Document'] },
        },
      },
    },
  },
}

function prompt(t) {
  return `Author the extraction fields for a specific list of gap criteria in policy ${t.lcd}. Return them as structured data — do NOT edit any file.

RUN FOLDER: ${t.run_folder}
GAP LIST: read 3 - Checks/${t.lcd}_field_gaps.json — { "gaps": [ {key, code, n, order_type, type, title, definition} ] }. These keys are MISSING their fields and you must author for EVERY gap in the list.

For each gap criterion, author the extraction fields = the raw data a reviewer must FIND to
evaluate it, then emit one RESULT.fields entry per field with "key" set to that gap's exact
"code::n". Author several fields where the criterion lists several findings (decompose a
multi-alternative indication into one fetch-field per finding).

PURE RETRIEVAL ONLY — "go get and find". label/description may contain NO threshold or rule
value (no ">=", "<", "or more", "at least", numbers-as-rules, interval math), NO judgment word
(qualifies, meets, abnormal, adequate, sufficient, significant, severe, elevated, suspicion,
appropriate), and NO conditional (if, when, whether, unless). All logic stays in the criterion.
description = imperative "Find/Locate the … . May be recorded as …". Pick tag by where the data
lives (clinical facts=Medical Record; imaging/ABI/study values=Diagnostic Test Result; the
order=Physician Written Order; labs=Labs).

Return RESULT: lcd, and fields = the full array covering EVERY gap key in the list (at least one
field per gap key). Do not include keys that are not in the gap list.`
}

phase('Fill gaps')
const rows = await parallel(TARGETS.map(t => () =>
  agent(prompt(t), { label: `fill:${t.lcd}`, phase: 'Fill gaps', model: 'opus', effort: 'high', agentType: 'general-purpose', schema: RESULT })))
return { filled: rows.filter(Boolean) }
