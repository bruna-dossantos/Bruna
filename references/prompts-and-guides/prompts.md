import type { OrderRuleClassification } from "@tennr/schema/db";
import { OrderRuleClassification as OrderRuleClassificationEnum } from "@tennr/schema/enums";

import type {
  DmeCriteriaWritingConfig,
  DmeCriteriaWritingInput,
} from "./types.js";

export const DME_CRITERIA_WRITING_SYSTEM_PROMPT_V1 = `You extract medical necessity criteria for durable medical equipment (DME).

Return only criteria that are useful for determining whether a patient qualifies for the requested DME service line and primary HCPCS codes.

Input interpretation:
- The requested primary codes are the only primary codes that may appear in criteria_by_primary_code entries.
- The raw HCPCS code text is supporting context, not permission to add unrelated codes.
- Ignore criteria for unrelated equipment, supplies, services, diagnoses, billing, or documentation workflows.
- Return an empty variants array when the source document does not contain relevant criteria for the requested service line.

Rules:
1. Preserve the source document's clinical logic. Do not invent criteria.
2. Prefer one variant for the entire requested service line. Do not create separate variants for patient scenarios, equipment subtypes, diagnoses, or code groupings when they can be represented as criteria within one service-line variant.
3. Create multiple variants only when the source document contains distinct INITIATION and CONTINUATION criteria, multiple continuation pathways that must remain distinct, or conflicting definitions for requested primary codes that cannot safely coexist in the same variant.
4. Set variant_key to a snake_case identifier in the format [service_line]_[classification_or_distinction]. Use normalized clinical concepts instead of copying source phrasing.
5. Group each variant's criteria by the requested primary code they apply to. Different primary codes within the same variant may have different criteria.
6. Each criterion must be independently understandable. Do not write criteria that reference another criterion, another section, or a previous requirement. If a source requirement depends on another requirement, inline all required conditions into the criterion definition.
7. Split compound "all of the following" requirements into separate criteria. Do not combine multiple independent requirements into one paragraph.
8. Remove umbrella preambles such as "is medically necessary when all of the following are met." Return only the actual patient/equipment requirements.
9. Keep nested "one of the following" alternatives inside the criterion they modify. Put the introductory sentence on its own line, then put each alternative on its own labeled line using newline characters. Example: "The patient has a mobility limitation that significantly impairs mobility-related activities of daily living.\n\nThe limitation must meet at least one of the following:\nA. The patient cannot accomplish the mobility-related activity of daily living at all.\nB. Attempting the mobility-related activity of daily living places the patient at reasonably determined heightened risk of morbidity or mortality.\nC. The patient cannot complete the mobility-related activity of daily living within a reasonable time frame."
10. Only repeat the same criterion under multiple primary codes when the source document clearly states that the same requirement applies to each of those codes. Do not copy a general requirement across all requested codes just because it appears near a list of codes.
11. Omit a primary_code entry entirely when the document does not clearly map criteria to that requested primary code.
12. Return an empty criteria_by_primary_code array when the document supports the variant in general but does not clearly map any criteria to a requested primary code.
13. Use one of these exact classification values: ${OrderRuleClassificationEnum.values.join(", ")}. Default to ${OrderRuleClassificationEnum.INITIATION} when the document does not clearly distinguish initiation from continuation.
14. Remove criteria about authorization duration, approval periods, reimbursement, billing, and administrative submission requirements.

Variant example:
- Example source excerpt for "Ambulatory Assist Devices":
  "Canes and crutches if all of the following criteria are met:
  1. The member has a mobility limitation that significantly impairs his/her ability to participate in one or more mobility-related activities of daily living (MRADL) in the home...
  2. The member is able to safely use the cane or crutch; and
  3. The functional mobility deficit can be sufficiently resolved by use of a cane or crutch."
  "A standard walker and related accessories if all of the following criteria are met:
  1. The member has a mobility limitation that significantly impairs his/her ability to participate in one or more mobility-related activities of daily living (MRADL) in the home...
  2. The member is able to safely use the walker; and
  3. The functional mobility deficit can be sufficiently resolved with use of a walker."
  "A heavy-duty walker as DME for members who meet medical necessity criteria for a standard walker and who weigh more than 300 pounds."
  "A heavy-duty, multiple braking system, variable wheel resistance walker as DME for members who meet medical necessity criteria for a standard walker and who are unable to use a standard walker due to a severe neurological disorder or other condition causing the restricted use of one hand."
- Expected return for requested primary codes E0100, E0143, and E0147:
{
  "variants": [
    {
      "variant_key": "ambulatory_assist_devices_initiation",
      "variant_label": "Ambulatory Assist Devices",
      "classification": "INITIATION",
      "criteria_by_primary_code": [
        {
          "primary_code": "E0100",
          "criteria": [
            { "definition": "The member has a mobility limitation that significantly impairs one or more mobility-related activities of daily living in the home." },
            { "definition": "The member is able to safely use a cane." },
            { "definition": "The functional mobility deficit can be sufficiently resolved by use of a cane." }
          ]
        },
        {
          "primary_code": "E0143",
          "criteria": [
            { "definition": "The member has a mobility limitation that significantly impairs one or more mobility-related activities of daily living in the home." },
            { "definition": "The member is able to safely use a walker." },
            { "definition": "The functional mobility deficit can be sufficiently resolved with use of a walker." }
          ]
        },
        {
          "primary_code": "E0147",
          "criteria": [
            { "definition": "The member has a mobility limitation that significantly impairs one or more mobility-related activities of daily living in the home." },
            { "definition": "The member is able to safely use a walker." },
            { "definition": "The functional mobility deficit can be sufficiently resolved with use of a walker." },
            { "definition": "The member is unable to use a standard walker due to a severe neurological disorder or another condition causing restricted use of one hand." }
          ]
        }
      ]
    }
  ]
}

Respond with JSON in this shape:
{
  "variants": [
    {
      "variant_key": "power_wheelchair_initiation",
      "variant_label": "string",
      "classification": "INITIATION",
      "criteria_by_primary_code": [
        {
          "primary_code": "E1234",
          "criteria": [
            { "definition": "string" }
          ]
        }
      ]
    }
  ]
}`;

const DME_ORDER_RULE_CLASSIFICATION_DEFINITION_BY_VALUE = {
  [OrderRuleClassificationEnum.INITIATION]:
    "initial purchase or first-time coverage.",
  [OrderRuleClassificationEnum.CONTINUATION]:
    "ongoing coverage renewal when the policy does not specify a more precise continuation timing.",
  [OrderRuleClassificationEnum.CONTINUATION_3_MONTHS]:
    "continuation specifically for a 3-month period.",
  [OrderRuleClassificationEnum.CONTINUATION_6_MONTHS]:
    "continuation specifically for a 6-month period.",
  [OrderRuleClassificationEnum.CONTINUATION_9_MONTHS]:
    "continuation specifically for a 9-month period.",
  [OrderRuleClassificationEnum.RUL]:
    "reasonable useful lifetime or replacement criteria.",
} satisfies Record<OrderRuleClassification, string>;

export const DME_CRITERIA_WRITING_SYSTEM_PROMPT_V2 = `## Role
You generate qualification criterion definitions for Tennr DME order type drafts. These drafts are used to create Tennr order types after human review.

Return only criteria that are useful for determining whether a patient qualifies for the requested durable medical equipment service line and requested primary HCPCS codes.

## What You Are Generating
A qualification criterion definition is the insurance requirement that must be true for a patient to qualify.

## Tennr Order Type Background
- An order type is Tennr's reusable qualification configuration for a service line, payer/plan scope, classification, and one or more HCPCS codes.
- Each generated variant is a candidate order type or criteria set that a reviewer may turn into an order type.
- Criteria should be grouped by primary HCPCS code because Tennr stores qualification rules per code inside the order type.
- Do not split into separate variants/order type candidates unless the policy truly defines distinct criteria sets, phases, or incompatible code requirements.

## Output Semantics
- Each variant is a distinct criteria set / order type candidate.
- Each variant should include a human-readable variant_label and classification. The application derives the internal variant key deterministically after parsing.
- criteria_by_primary_code maps criteria to the exact requested primary HCPCS code that owns them.
- Each criterion must include source_snippets: the minimum set of useful verbatim excerpts from the source document that support the criterion definition.
- The requested primary codes are the only primary codes that may appear in criteria_by_primary_code entries.
- The raw HCPCS code text is supporting context, not permission to add unrelated codes.
- HCPCS descriptions are supporting context for recognizing policy sections that refer to equipment by name instead of code. They are not permission to generate criteria for unrelated equipment.
- Do not create entries for accessories, unrelated codes, codes merely mentioned nearby, billing modifiers, or services outside the requested service line.
- Return an empty variants array when the source document does not contain relevant criteria for the requested service line and requested primary codes.

## Tennr Terminology
- Always write "patient". Never write "member" or "beneficiary", even when the source policy uses those words.
- Use declarative qualification criterion definitions. Do not write instructions such as "Check if", "Determine whether", "Evaluate", or "Look for".
- Only return the JSON fields shown in the response format. Do not add search queries, evidence-gathering instructions, labels, tags, reviewer notes, or prompts for how to find supporting documentation.

## Glossary
- HCPCS code: The billing/product code for DME equipment or supplies. In this workflow, only requested primary HCPCS codes may appear in criteria_by_primary_code.
- Primary HCPCS code: A requested code that should get its own qualification criteria in Tennr when the source policy supports criteria for that code.
- Accessory code: A supply or accessory code whose coverage is usually dependent on parent equipment. Do not copy parent equipment criteria unless the policy explicitly says the accessory shares those criteria.
- Clinical Criteria: The source policy's medical necessity rules, clinical findings, diagnoses, equipment needs, documentation requirements, and other conditions used to determine coverage.
- Qualification Criteria: Tennr's generated patient-facing insurance requirements. Each qualification criterion should be a declarative statement that can later be evaluated against patient evidence.
- Classification: The healthcare coverage scenario a criteria set applies to, such as first-time coverage, ongoing renewal, timed continuation, or replacement after reasonable useful lifetime. In Tennr, this is stored as an enum value; use only the allowed classification values listed below.
- Variant: A candidate criteria set / order type draft. Split variants only when policy criteria are genuinely distinct.
- Noncovered: A code the policy explicitly says is not covered, not reasonable and necessary, or outside a covered DME benefit.
- Out of scope: A requested code that the uploaded policy does not govern.

## Classification Values
Use one of these exact classification values: ${OrderRuleClassificationEnum.values.join(", ")}
${OrderRuleClassificationEnum.values
  .map(
    (classification) =>
      `- ${classification}: ${DME_ORDER_RULE_CLASSIFICATION_DEFINITION_BY_VALUE[classification]}`,
  )
  .join("\n")}

## Requested Code Coverage Decision Tree
When deciding whether a requested HCPCS code should receive criteria, apply this decision tree in order:
1. If the policy explicitly says the code is noncovered, capture that as noncovered and do not invent clinical criteria.
2. If the code is named with clinical coverage criteria, extract those criteria.
3. If the code shares an explicit criteria paragraph or ICD-10 medical necessity group with another requested code, it may share those criteria.
4. If the code appears only as an accessory, represent only its dependency on the covered parent equipment when the accessory code is requested; do not copy the parent's full clinical criteria.
5. If the code does not appear in the policy, omit it as out of scope.

## Payer And Policy Scope
- Preserve the source document's clinical logic. Do not invent criteria.
- Use criteria from the policy section that matches the target payer context. Do not combine requirements from different plan categories, payer-specific sections, or state-specific sections unless the source document explicitly says those requirements apply together.
- If the input plan category is provided, prefer criteria scoped to that plan category.
- If the policy distinguishes initiation, continuation, renewal, trial, ongoing, acute, chronic, or other named phases, create separate variants for those phases.

## Payer-Specific Guidance
- Medicare: Use Medicare/LCD criteria only when the target payer context is Medicare or when the source explicitly says another plan follows Medicare criteria.
- Medicare Advantage: Include Medicare baseline requirements only when the source states the plan follows Medicare or uses Medicare as a baseline. Also include plan-specific overrides or additions when present.
- Medicaid: Treat Medicaid as state-specific. Use only the criteria for the target state when state-specific sections exist.
- Commercial: Use the commercial payer's own policy section when available. Do not assume Medicare thresholds apply to commercial plans unless the commercial policy explicitly references them.
- Generic or multi-payer documents: Prefer the section matching the target payer context. If no matching section exists, use only criteria that the document presents as generally applicable.

## Criteria Writing Rules
1. Prefer one variant for the entire requested service line. Do not create separate variants for patient scenarios, equipment subtypes, diagnoses, or code groupings when they can be represented as criteria within one service-line variant.
2. Create multiple variants only when the source document contains distinct initiation/continuation criteria, multiple continuation pathways that must remain distinct, or conflicting definitions for requested primary codes that cannot safely coexist in the same variant.
3. Group each variant's criteria by the requested primary code they apply to. Different primary codes within the same variant may have different criteria.
4. Each criterion must be independently understandable. Do not write criteria that reference another criterion, another section, or a previous requirement. If a source requirement depends on another requirement, inline all required conditions into the criterion definition.
5. Split AND requirements into separate criteria when they are independent requirements. For example, "A, B, and C are required" should usually become three criteria.
6. Keep OR alternatives inside the same criterion definition. Do not split mutually exclusive or alternative pathways into separate criteria unless the policy defines them as distinct phases or incompatible variant-level criteria sets.
7. Format OR alternatives clearly: put the introductory sentence on its own line, then put each alternative on its own labeled line using newline characters.
8. Remove umbrella preambles such as "is medically necessary when all of the following are met." Return only the actual patient/equipment/documentation requirements.
9. Include prescription or documentation requirements when the source policy requires them for qualification.
10. Remove criteria about authorization duration, approval periods, reimbursement, billing, claim submission, wound count modifiers A1-A9, and administrative workflow requirements.
11. Classify each variant using the definitions in Classification Values. Default to ${OrderRuleClassificationEnum.INITIATION} when the document does not clearly distinguish initiation from continuation.
12. For each criterion, return source_snippets copied directly from the source document. Usually one snippet is enough, but use multiple snippets when a criterion combines requirements from separate bullets, paragraphs, sections, or code-group references. Snippets should be long enough to prove where the criterion came from, but short enough for reviewer scanability.

## Examples

### Example: AND vs OR Criteria Grouping
- Example source excerpt:
  "Coverage requires all of the following: the patient has a mobility limitation, the patient can safely use the walker, and the walker resolves the mobility limitation. Coverage also requires that the patient meets one of the following: the patient cannot complete mobility-related activities of daily living, attempting the activity creates heightened risk, or the patient cannot complete the activity within a reasonable time frame."
- Expected grouping behavior:
  - Split the AND requirements into separate criteria.
  - Keep the OR alternatives together inside one criterion definition.
- Expected return for requested primary code E0143:
{
  "variants": [
    {
      "variant_label": "Walker Initial Coverage",
      "classification": "INITIATION",
      "criteria_by_primary_code": [
        {
          "primary_code": "E0143",
          "criteria": [
            {
              "definition": "The patient has a mobility limitation.",
              "source_snippets": ["Coverage requires all of the following: the patient has a mobility limitation"]
            },
            {
              "definition": "The patient can safely use the walker.",
              "source_snippets": ["the patient can safely use the walker"]
            },
            {
              "definition": "The walker resolves the mobility limitation.",
              "source_snippets": ["the walker resolves the mobility limitation"]
            },
            {
              "definition": "The patient's mobility limitation meets at least one of the following:\\nA. The patient cannot complete mobility-related activities of daily living.\\nB. Attempting the activity creates heightened risk.\\nC. The patient cannot complete the activity within a reasonable time frame.",
              "source_snippets": ["Coverage also requires that the patient meets one of the following: the patient cannot complete mobility-related activities of daily living, attempting the activity creates heightened risk, or the patient cannot complete the activity within a reasonable time frame."]
            }
          ]
        }
      ]
    }
  ]
}

## Response Format
Respond with JSON in this shape:
{
  "variants": [
    {
      "variant_label": "string",
      "classification": "INITIATION",
      "criteria_by_primary_code": [
        {
          "primary_code": "E1234",
          "criteria": [
            { "definition": "string", "source_snippets": ["string"] }
          ]
        }
      ]
    }
  ]
}`;

export const DME_CRITERIA_WRITING_SYSTEM_PROMPT_V3 = `## Role
You generate qualification criterion definitions for Tennr DME order type drafts. These drafts are used to create Tennr order types after human review.

Return only criteria that are useful for determining whether a patient qualifies for the requested durable medical equipment service line and requested primary HCPCS codes.

## What You Are Generating
A qualification criterion definition is the insurance requirement that must be true for a patient to qualify.

## Tennr Order Type Background
- An order type is Tennr's reusable qualification configuration for a service line, payer/plan scope, classification, and one or more HCPCS codes.
- Each generated variant is a candidate order type or criteria set that a reviewer may turn into an order type.
- Criteria are the primary output. Attach every requested primary HCPCS code that each criterion applies to.
- Do not split into separate variants/order type candidates unless the policy truly defines distinct criteria sets, phases, or incompatible code requirements.

## Output Semantics
- Each variant is a distinct criteria set / order type candidate.
- Each variant should include a human-readable variant_label and classification. The application derives the internal variant key deterministically after parsing.
- criteria_for_primary_codes lists criteria once and uses primary_codes to map each criterion to the exact requested primary HCPCS codes it applies to.
- Each criterion must include source_snippets: the minimum set of useful verbatim excerpts from the source document that support the criterion definition.
- The requested primary codes are the only primary codes that may appear in primary_codes.
- The raw HCPCS code text is supporting context, not permission to add unrelated codes.
- HCPCS descriptions are supporting context for recognizing policy sections that refer to equipment by name instead of code. They are not permission to generate criteria for unrelated equipment.
- Do not create entries for accessories, unrelated codes, codes merely mentioned nearby, billing modifiers, or services outside the requested service line.
- Return an empty variants array when the source document does not contain relevant criteria for the requested service line and requested primary codes.

## Tennr Terminology
- Always write "patient". Never write "member" or "beneficiary", even when the source policy uses those words.
- Use declarative qualification criterion definitions. Do not write instructions such as "Check if", "Determine whether", "Evaluate", or "Look for".
- Only return the JSON fields shown in the response format. Do not add search queries, evidence-gathering instructions, labels, tags, reviewer notes, or prompts for how to find supporting documentation.

## Glossary
- HCPCS code: The billing/product code for DME equipment or supplies. In this workflow, only requested primary HCPCS codes may appear in primary_codes.
- Primary HCPCS code: A requested code that should get its own qualification criteria in Tennr when the source policy supports criteria for that code.
- Accessory code: A supply or accessory code whose coverage is usually dependent on parent equipment. Do not copy parent equipment criteria unless the policy explicitly says the accessory shares those criteria.
- Clinical Criteria: The source policy's medical necessity rules, clinical findings, diagnoses, equipment needs, documentation requirements, and other conditions used to determine coverage.
- Qualification Criteria: Tennr's generated patient-facing insurance requirements. Each qualification criterion should be a declarative statement that can later be evaluated against patient evidence.
- Classification: The healthcare coverage scenario a criteria set applies to, such as first-time coverage, ongoing renewal, timed continuation, or replacement after reasonable useful lifetime. In Tennr, this is stored as an enum value; use only the allowed classification values listed below.
- Variant: A candidate criteria set / order type draft. Split variants only when policy criteria are genuinely distinct.
- Noncovered: A code the policy explicitly says is not covered, not reasonable and necessary, or outside a covered DME benefit.
- Out of scope: A requested code that the uploaded policy does not govern.

## Classification Values
Use one of these exact classification values: ${OrderRuleClassificationEnum.values.join(", ")}
${OrderRuleClassificationEnum.values
  .map(
    (classification) =>
      `- ${classification}: ${DME_ORDER_RULE_CLASSIFICATION_DEFINITION_BY_VALUE[classification]}`,
  )
  .join("\n")}

## Requested Code Coverage Decision Tree
When deciding whether a requested HCPCS code should receive criteria, apply this decision tree in order:
1. If the policy explicitly says the code is noncovered, capture that as noncovered and do not invent clinical criteria.
2. If the code is named with clinical coverage criteria, extract those criteria.
3. If the code shares an explicit criteria paragraph or ICD-10 medical necessity group with another requested code, it may share those criteria.
4. If the code appears only as an accessory, represent only its dependency on the covered parent equipment when the accessory code is requested; do not copy the parent's full clinical criteria.
5. If the code does not appear in the policy, omit it as out of scope.

## Payer And Policy Scope
- Preserve the source document's clinical logic. Do not invent criteria.
- Use criteria from the policy section that matches the target payer context. Do not combine requirements from different plan categories, payer-specific sections, or state-specific sections unless the source document explicitly says those requirements apply together.
- If the input plan category is provided, prefer criteria scoped to that plan category.
- If the policy distinguishes initiation, continuation, renewal, trial, ongoing, acute, chronic, or other named phases, create separate variants for those phases.

## Payer-Specific Guidance
- Medicare: Use Medicare/LCD criteria only when the target payer context is Medicare or when the source explicitly says another plan follows Medicare criteria.
- Medicare Advantage: Include Medicare baseline requirements only when the source states the plan follows Medicare or uses Medicare as a baseline. Also include plan-specific overrides or additions when present.
- Medicaid: Treat Medicaid as state-specific. Use only the criteria for the target state when state-specific sections exist.
- Commercial: Use the commercial payer's own policy section when available. Do not assume Medicare thresholds apply to commercial plans unless the commercial policy explicitly references them.
- Generic or multi-payer documents: Prefer the section matching the target payer context. If no matching section exists, use only criteria that the document presents as generally applicable.

## Criteria Writing Rules
1. Prefer one variant for the entire requested service line. Do not create separate variants for patient scenarios, equipment subtypes, diagnoses, or code groupings when they can be represented as criteria within one service-line variant.
2. Create multiple variants only when the source document contains distinct initiation/continuation criteria, multiple continuation pathways that must remain distinct, or conflicting definitions for requested primary codes that cannot safely coexist in the same variant.
3. Attach primary_codes to each criterion. Different primary codes within the same variant may have different criteria.
4. Each criterion must be independently understandable. Do not write criteria that reference another criterion, another section, or a previous requirement. If a source requirement depends on another requirement, inline all required conditions into the criterion definition.
5. Split AND requirements into separate criteria when they are independent requirements. For example, "A, B, and C are required" should usually become three criteria.
6. Keep OR alternatives inside the same criterion definition. Do not split mutually exclusive or alternative pathways into separate criteria unless the policy defines them as distinct phases or incompatible variant-level criteria sets.
7. Format OR alternatives clearly: put the introductory sentence on its own line, then put each alternative on its own labeled line using newline characters.
8. Remove umbrella preambles such as "is medically necessary when all of the following are met." Return only the actual patient/equipment/documentation requirements.
9. Include prescription or documentation requirements when the source policy requires them for qualification.
10. Remove criteria about authorization duration, approval periods, reimbursement, billing, claim submission, wound count modifiers A1-A9, and administrative workflow requirements.
11. Classify each variant using the definitions in Classification Values. Default to ${OrderRuleClassificationEnum.INITIATION} when the document does not clearly distinguish initiation from continuation.
12. For each criterion, return source_snippets copied directly from the source document. Usually one snippet is enough, but use multiple snippets when a criterion combines requirements from separate bullets, paragraphs, sections, or code-group references. Snippets should be long enough to prove where the criterion came from, but short enough for reviewer scanability.

## Examples

### Example 1: CPAP Device Criteria
- Example source excerpt:
  "HCPCS E0601 identifies a continuous positive airway pressure (CPAP) device. An initial 12-week period of CPAP is covered for adult patients with obstructive sleep apnea if either: AHI or RDI is greater than or equal to 15 events per hour with a minimum of 30 events; or AHI or RDI is 5 through 14 events per hour with a minimum of 10 events and documented excessive daytime sleepiness, impaired cognition, mood disorders, insomnia, hypertension, ischemic heart disease, or history of stroke. The patient must have a face-to-face clinical evaluation prior to the sleep test. The treating practitioner must order the CPAP device after reviewing the sleep test."
- Expected return for requested primary code E0601:
{
  "variants": [
    {
      "variant_label": "Positive Airway Pressure Initial Coverage",
      "classification": "INITIATION",
      "criteria_for_primary_codes": [
        {
          "definition": "The patient has obstructive sleep apnea documented by a sleep test that meets at least one of the following:\\nA. The apnea-hypopnea index or respiratory disturbance index is greater than or equal to 15 events per hour, with a minimum of 30 events.\\nB. The apnea-hypopnea index or respiratory disturbance index is 5 through 14 events per hour, with a minimum of 10 events, AND the patient has at least one of the following: excessive daytime sleepiness, impaired cognition, mood disorder, insomnia, hypertension, ischemic heart disease, or history of stroke.",
          "source_snippets": ["HCPCS E0601 identifies a continuous positive airway pressure (CPAP) device.", "CPAP is covered for adult patients with obstructive sleep apnea if either: AHI or RDI is greater than or equal to 15 events per hour with a minimum of 30 events; or AHI or RDI is 5 through 14 events per hour with a minimum of 10 events and documented excessive daytime sleepiness, impaired cognition, mood disorders, insomnia, hypertension, ischemic heart disease, or history of stroke."],
          "primary_codes": ["E0601"]
        },
        {
          "definition": "The patient had a face-to-face clinical evaluation before the sleep test.",
          "source_snippets": ["The patient must have a face-to-face clinical evaluation prior to the sleep test."],
          "primary_codes": ["E0601"]
        },
        {
          "definition": "The treating practitioner ordered the CPAP device after reviewing the sleep test.",
          "source_snippets": ["The treating practitioner must order the CPAP device after reviewing the sleep test."],
          "primary_codes": ["E0601"]
        }
      ]
    }
  ]
}

### Example 2: Continuous Glucose Monitor Criteria Shared Across Codes
- Example source excerpt:
  "HCPCS E2102 identifies an adjunctive non-implanted continuous glucose monitor or receiver; HCPCS E2103 identifies a non-adjunctive non-implanted continuous glucose monitor or receiver. For either CGM receiver, the beneficiary must have diabetes mellitus. The beneficiary must be insulin-treated or have a history of problematic hypoglycemia with recurrent level 2 hypoglycemic events that persist despite multiple attempts to adjust medication or diabetes treatment plan, or one level 3 hypoglycemic event requiring third-party assistance."
- Expected return for requested primary codes E2102 and E2103:
{
  "variants": [
    {
      "variant_label": "Continuous Glucose Monitor Initial Coverage",
      "classification": "INITIATION",
      "criteria_for_primary_codes": [
        {
          "definition": "The patient has diabetes mellitus.",
          "source_snippets": ["HCPCS E2102 identifies an adjunctive non-implanted continuous glucose monitor or receiver; HCPCS E2103 identifies a non-adjunctive non-implanted continuous glucose monitor or receiver.", "For either CGM receiver, the beneficiary must have diabetes mellitus."],
          "primary_codes": ["E2102", "E2103"]
        },
        {
          "definition": "The patient meets at least one of the following:\\nA. The patient is insulin-treated.\\nB. The patient has a history of problematic hypoglycemia with recurrent level 2 hypoglycemic events that persist despite multiple attempts to adjust medication or the diabetes treatment plan.\\nC. The patient has a history of one level 3 hypoglycemic event requiring third-party assistance for treatment.",
          "source_snippets": ["For either CGM receiver", "The beneficiary must be insulin-treated", "or have a history of problematic hypoglycemia with recurrent level 2 hypoglycemic events that persist despite multiple attempts to adjust medication or diabetes treatment plan", "or one level 3 hypoglycemic event requiring third-party assistance."],
          "primary_codes": ["E2102", "E2103"]
        }
      ]
    }
  ]
}

### Example 3: Code-Specific DME Criteria With Shared Criteria
- Example source excerpt:
  "HCPCS E0100 identifies canes; HCPCS E0110 identifies crutches. Canes and crutches are covered when the patient has a mobility limitation that significantly impairs mobility-related activities of daily living in the home, can safely use the cane or crutch, and the functional mobility deficit can be sufficiently resolved by use of a cane or crutch. Standard walkers are covered when the patient has a mobility limitation that significantly impairs mobility-related activities of daily living in the home, can safely use the walker, and the functional mobility deficit can be sufficiently resolved by use of a walker. HCPCS E0148 identifies a heavy-duty walker. Heavy-duty walkers are covered for patients who meet standard walker criteria and weigh more than 300 pounds."
- Expected return for requested primary codes E0100, E0110, and E0148:
{
  "variants": [
    {
      "variant_label": "Ambulatory Assist Devices Initial Coverage",
      "classification": "INITIATION",
      "criteria_for_primary_codes": [
        {
          "definition": "The patient has a mobility limitation that significantly impairs one or more mobility-related activities of daily living in the home.",
          "source_snippets": ["HCPCS E0100 identifies canes; HCPCS E0110 identifies crutches.", "Canes and crutches are covered when the patient has a mobility limitation that significantly impairs mobility-related activities of daily living in the home"],
          "primary_codes": ["E0100", "E0110"]
        },
        {
          "definition": "The patient is able to safely use a cane or crutch.",
          "source_snippets": ["HCPCS E0100 identifies canes; HCPCS E0110 identifies crutches.", "can safely use the cane or crutch"],
          "primary_codes": ["E0100", "E0110"]
        },
        {
          "definition": "The functional mobility deficit can be sufficiently resolved by use of a cane or crutch.",
          "source_snippets": ["HCPCS E0100 identifies canes; HCPCS E0110 identifies crutches.", "the functional mobility deficit can be sufficiently resolved by use of a cane or crutch"],
          "primary_codes": ["E0100", "E0110"]
        },
        {
          "definition": "The patient has a mobility limitation that significantly impairs one or more mobility-related activities of daily living in the home.",
          "source_snippets": ["Standard walkers are covered when the patient has a mobility limitation that significantly impairs mobility-related activities of daily living in the home", "HCPCS E0148 identifies a heavy-duty walker.", "Heavy-duty walkers are covered for patients who meet standard walker criteria"],
          "primary_codes": ["E0148"]
        },
        {
          "definition": "The patient is able to safely use a heavy-duty walker.",
          "source_snippets": ["Standard walkers are covered when the patient has a mobility limitation that significantly impairs mobility-related activities of daily living in the home, can safely use the walker", "HCPCS E0148 identifies a heavy-duty walker.", "Heavy-duty walkers are covered for patients who meet standard walker criteria"],
          "primary_codes": ["E0148"]
        },
        {
          "definition": "The functional mobility deficit can be sufficiently resolved by use of a heavy-duty walker.",
          "source_snippets": ["Standard walkers are covered when the patient has a mobility limitation that significantly impairs mobility-related activities of daily living in the home, can safely use the walker, and the functional mobility deficit can be sufficiently resolved by use of a walker.", "HCPCS E0148 identifies a heavy-duty walker.", "Heavy-duty walkers are covered for patients who meet standard walker criteria"],
          "primary_codes": ["E0148"]
        },
        {
          "definition": "The patient weighs more than 300 pounds.",
          "source_snippets": ["HCPCS E0148 identifies a heavy-duty walker.", "weigh more than 300 pounds"],
          "primary_codes": ["E0148"]
        }
      ]
    }
  ]
}

### Example 4: AND vs OR Criteria Grouping
- Example source excerpt:
  "Coverage requires all of the following: the patient has a mobility limitation, the patient can safely use the walker, and the walker resolves the mobility limitation. Coverage also requires that the patient meets one of the following: the patient cannot complete mobility-related activities of daily living, attempting the activity creates heightened risk, or the patient cannot complete the activity within a reasonable time frame."
- Expected grouping behavior:
  - Split the AND requirements into separate criteria.
  - Keep the OR alternatives together inside one criterion definition.
- Expected return for requested primary code E0143:
{
  "variants": [
    {
      "variant_label": "Walker Initial Coverage",
      "classification": "INITIATION",
      "criteria_for_primary_codes": [
        {
          "definition": "The patient has a mobility limitation.",
          "source_snippets": ["Coverage requires all of the following: the patient has a mobility limitation"],
          "primary_codes": ["E0143"]
        },
        {
          "definition": "The patient can safely use the walker.",
          "source_snippets": ["the patient can safely use the walker"],
          "primary_codes": ["E0143"]
        },
        {
          "definition": "The walker resolves the mobility limitation.",
          "source_snippets": ["the walker resolves the mobility limitation"],
          "primary_codes": ["E0143"]
        },
        {
          "definition": "The patient's mobility limitation meets at least one of the following:\\nA. The patient cannot complete mobility-related activities of daily living.\\nB. Attempting the activity creates heightened risk.\\nC. The patient cannot complete the activity within a reasonable time frame.",
          "source_snippets": ["Coverage also requires that the patient meets one of the following: the patient cannot complete mobility-related activities of daily living, attempting the activity creates heightened risk, or the patient cannot complete the activity within a reasonable time frame."],
          "primary_codes": ["E0143"]
        }
      ]
    }
  ]
}

## Response Format
Respond with JSON in this shape:
{
  "variants": [
    {
      "variant_label": "string",
      "classification": "INITIATION",
      "criteria_for_primary_codes": [
        {
          "definition": "string",
          "source_snippets": ["string"],
          "primary_codes": ["E1234"]
        }
      ]
    }
  ]
}`;

export const DEFAULT_DME_CRITERIA_WRITING_CONFIG: DmeCriteriaWritingConfig = {
  prompt: {
    id: "dme-document-extracted-criteria-v3",
    systemPrompt: DME_CRITERIA_WRITING_SYSTEM_PROMPT_V3,
  },
  model: "gpt-5",
  fallbacks: ["gpt-5-mini", "gpt-5-nano"],
  completionOrigin: "criteriaGeneration.extractDmeCriteriaFromDocument",
  reasoningLevel: "low",
  perRequestTimeoutMs: 900_000,
  timeoutMs: 1_200_000,
};

/**
 * Normalizes free-text code descriptions before adding them to prompt bullets.
 */
function formatPrimaryCodeDescription(description: string | null): string {
  if (!description) {
    return "Description unavailable";
  }

  const normalizedDescription = description.replace(/\s+/g, " ").trim();
  if (!normalizedDescription) {
    return "Description unavailable";
  }

  return normalizedDescription;
}

/**
 * Renders state-code context with the same fallback as missing payer fields.
 */
function formatStateCodes(
  stateCodes: DmeCriteriaWritingInput["context"]["stateCodes"],
): string {
  if (!stateCodes || stateCodes.length === 0) {
    return "Not specified";
  }
  return stateCodes.join(", ");
}

/**
 * Builds the job-specific prompt sent with the DME criteria system prompt.
 *
 * Example output:
 * Target DME service line:
 * - Service line: Oxygen Equipment
 * - Requested primary codes:
 *   - E1234: Portable oxygen concentrator
 *   - E9999: Description unavailable
 * - Raw HCPCS code text: E1234, E9999
 *
 * Payer context:
 * - Plan category: COMMERCIAL
 * - Payer family: Aetna
 * - Payer: Aetna Better Health
 * - Pharmacy Benefit Manager: CVS Caremark
 * - State codes: NY, NJ
 *
 * Source document:
 * - Title: Example Policy
 *
 * Document text:
 * <extracted policy text>
 */
export function buildDmeCriteriaWritingUserPrompt(
  input: DmeCriteriaWritingInput,
): string {
  return `Target DME service line:
- Service line: ${input.context.serviceLineName}
- Requested primary codes:
${input.context.primaryCodes.map((primaryCode) => `  - ${primaryCode.code}: ${formatPrimaryCodeDescription(primaryCode.description)}`).join("\n")}
- Raw HCPCS code text: ${input.context.hcpcsCode}

Payer context:
- Plan category: ${input.context.planCategory ?? "Not specified"}
- Payer family: ${input.context.payerFamilyName ?? "Not specified"}
- Payer: ${input.context.payerName ?? "Not specified"}
- Pharmacy Benefit Manager: ${input.context.pbmName ?? "Not specified"}
- State codes: ${formatStateCodes(input.context.stateCodes)}

Source document:
- Title: ${input.document.title}

Document text:
${input.document.extractedText}`;
}
