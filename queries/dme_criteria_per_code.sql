-- DME vertical criteria-generation jobs (global / team-less):
--   1. how many criteria per code
--   2. job duration from "ready to review" -> "published" (when available)
--
-- Target: Tennr app Postgres (Metabase read replica). Postgres dialect.
--
-- Scope filters (confirmed):
--   * vertical = DME   -> criteria_generation_job.pipeline_type = 'DME'
--   * global jobs      -> criteria_generation_job.team_id is null
--   (to also include the testing service line, OR-in a service_line filter -- see note.)
--
-- Endpoint mapping (NOT literal states on criteria_generation_job.status,
-- whose enum stops at COMPLETED -- these are reconstructed):
--   ready_to_review = criteria_generation_job.data -> 'progress' ->> 'updatedAt'
--   published       = first order_rule_version.created_at for the order rule(s)
--                     linked to the job via order_rule.criteria_generation_job_id
--   "when available" -> publish_times is left-joined, so unpublished jobs return null.
--
-- ============================================================================
-- OPEN ITEM -- criteria_count source. For team=NULL global jobs the criteria are
-- NOT on a team-scoped qualification_rule, so counting qualification_criteria the
-- normal way returns nothing. The count below reads the job's own data blob
-- (data -> 'variants'), which is what the published-jobs query used. This needs
-- ONE confirmation: the shape of data -> 'variants'.
--   * if it's a flat array of criteria      -> jsonb_array_length(data -> 'variants')   (as written)
--   * if it's {clinical:[...], docs:[...]}  -> sum the sub-array lengths instead
-- Paste one data row (or the key names) and I'll lock this down.
-- ============================================================================

with target_jobs as (
    select
        j.id                                                  as job_id,
        j.j_code,
        j.pipeline_type,
        (j.data -> 'progress' ->> 'updatedAt')::timestamptz   as ready_to_review_at,
        -- OPEN ITEM: confirm data -> 'variants' shape (see header)
        jsonb_array_length(j.data -> 'variants')              as criteria_count
    from criteria_generation_job j
    where j.archived = false
      and j.pipeline_type = 'DME'
      and j.team_id is null
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
)
select
    tj.j_code                                                                        as code,
    tj.criteria_count,
    (tj.ready_to_review_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/New_York'        as ready_to_review_et,
    (pt.published_at       AT TIME ZONE 'UTC') AT TIME ZONE 'America/New_York'        as published_et,
    round(extract(epoch from (pt.published_at - tj.ready_to_review_at)) / 3600.0, 2)  as review_to_publish_hours
from target_jobs tj
left join publish_times pt
    on pt.job_id = tj.job_id
order by
    tj.j_code;

-- To also include the testing service line, add a service_line join in target_jobs and
-- change the where to:  and (j.pipeline_type = 'DME' and j.team_id is null) or <testing filter>
