-- DME vertical + testing service line:
--   1. how many criteria per code
--   2. criteria-generation-job duration from "ready to review" -> "published" (when available)
--
-- Target: Tennr app Postgres (Metabase read replica). Postgres dialect.
--
-- Endpoint mapping (these are NOT literal states on criteria_generation_job.status,
-- whose enum stops at COMPLETED -- they are reconstructed):
--   ready_to_review = criteria_generation_job.data -> 'progress' ->> 'updatedAt'
--   published       = first order_rule_version.created_at for the order rule(s)
--                     linked back to the job via order_rule.criteria_generation_job_id
--
-- Notes / knobs:
--   * DME vertical      = criteria_generation_job.pipeline_type = 'DME'
--   * testing service   = service_line.service_line ilike '%test%'  (confirm exact name;
--                         if testing has its own pipeline_type value, filter on that instead)
--   * criteria_count    = persisted live criteria (qualification_rule -> qualification_criteria).
--                         For the generated-variants blob instead, swap criteria_counts for
--                         jsonb_array_length(j.data -> 'variants').
--   * grain is one row per generation job (code x payer/run). group by code to roll up.
--   * "published (when available)" -> publish_times is left-joined, so unpublished jobs
--                         return null duration rather than dropping out.
--   * heads-up: order_rule.criteria_generation_job_id and the data JSON keys are newer than
--     the checked-in Kysely schema snapshot -- verify counts against a couple known codes.

with target_jobs as (
    select
        j.id                                                  as job_id,
        j.j_code,
        j.pipeline_type,
        j.service_line_id,
        (j.data -> 'progress' ->> 'updatedAt')::timestamptz   as ready_to_review_at
    from criteria_generation_job j
    left join service_line sl
        on sl.id = j.service_line_id
    where j.archived = false
      and (
        j.pipeline_type = 'DME'              -- the DME vertical
        or sl.service_line ilike '%test%'    -- the testing service line (confirm exact name)
      )
),
publish_times as (
    -- "published" = first order-rule version cut from the job
    select
        o.criteria_generation_job_id as job_id,
        min(orv.created_at)          as published_at
    from order_rule o
    join order_rule_version orv
        on orv.order_rule_id = o.id
    where o.criteria_generation_job_id is not null
    group by o.criteria_generation_job_id
),
criteria_counts as (
    -- criteria per code, via the rule the job produced (live version)
    select
        o.criteria_generation_job_id as job_id,
        count(qc.id)                 as criteria_count
    from order_rule o
    join qualification_rule qr
        on qr.order_rule_id = o.id
    join qualification_criteria qc
        on qc.qualification_criteria_version_id = qr.live_criteria_version_id
    where o.criteria_generation_job_id is not null
    group by o.criteria_generation_job_id
)
select
    tj.j_code                                                                        as code,
    tj.pipeline_type,
    sl.service_line,
    cc.criteria_count,
    (tj.ready_to_review_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/New_York'        as ready_to_review_et,
    (pt.published_at       AT TIME ZONE 'UTC') AT TIME ZONE 'America/New_York'        as published_et,
    round(extract(epoch from (pt.published_at - tj.ready_to_review_at)) / 3600.0, 2)  as review_to_publish_hours
from target_jobs tj
left join service_line sl
    on sl.id = tj.service_line_id
left join publish_times pt
    on pt.job_id = tj.job_id
left join criteria_counts cc
    on cc.job_id = tj.job_id
order by
    sl.service_line,
    code;
