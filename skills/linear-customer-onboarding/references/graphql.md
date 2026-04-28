# Linear GraphQL reference

Quick reference for the mutations and queries this skill uses. Endpoint is `https://api.linear.app/graphql`. Auth header: `Authorization: <token from ~/.linear_token>` (no `Bearer` prefix — Linear personal API tokens are bare).

## Mutations

### IssueCreate

```graphql
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue { id identifier url }
  }
}
```

`IssueCreateInput` fields used by this skill:

| Field      | Type     | Notes                                              |
| ---------- | -------- | -------------------------------------------------- |
| title      | String   | "Cxxxx - description"                              |
| teamId     | String   | DME Criteria or Infusion Criteria team UUID        |
| projectId  | String   | Insurance project (parent) or Qual Criteria (cust) |
| parentId   | String   | Customer ticket only — points at parent ticket     |
| labelIds   | [String] | All UUIDs MUST be scoped to `teamId`'s team        |
| stateId    | String   | "Not Started" UUID for the team                    |
| priority   | Int      | 1 (Urgent), 2 (High), 3 (Normal), 4 (Low)          |
| estimate   | Int      | 1 (XS), 2 (S), 3 (M)                               |

### IssueLabelCreate (team-scoped)

```graphql
mutation IssueLabelCreate($input: IssueLabelCreateInput!) {
  issueLabelCreate(input: $input) {
    success
    issueLabel { id name }
  }
}
```

`teamId` MUST be supplied. A label without `teamId` is workspace-scoped and CANNOT be attached to issues whose team has a same-named team-scoped label (you'll get "duplicate label name"). Always create team-scoped duplicates instead of workspace labels.

### customerNeedCreate

```graphql
mutation CustomerNeedCreate($input: CustomerNeedCreateInput!) {
  customerNeedCreate(input: $input) {
    success
    need { id }
  }
}
```

Input: `{ customerId: <Linear Customer UUID>, issueId: <issue UUID> }`. Linear does NOT enforce uniqueness on (customerId, issueId) — repeated calls create duplicate needs.

## Queries used by refresh_linear_data.py

```graphql
query Teams { teams(first: 250) { nodes { id name key } } }

query Labels($teamId: String!, $cursor: String) {
  team(id: $teamId) {
    labels(first: 250, after: $cursor) {
      nodes { id name }
      pageInfo { hasNextPage endCursor }
    }
  }
}

query Projects($cursor: String) {
  projects(first: 250, after: $cursor) {
    nodes { id name }
    pageInfo { hasNextPage endCursor }
  }
}

query States($teamId: String!) {
  team(id: $teamId) {
    states(first: 100) { nodes { id name type } }
  }
}
```

Pagination: `after: $cursor` with `endCursor` from previous response.

## Rate limits (real ones, not docs ones)

Personal API tokens are limited to **2,500 requests / hour rolling window**. Linear returns rate-limit errors as **HTTP 400** with body containing `"code":"RATELIMITED"`. NOT 429. The retry path in `_lib.gql_with_retry` detects this and sleeps 60 minutes.

GraphQL-level `extensions.code = RATELIMITED` errors (e.g. complexity-based) come back as HTTP 200 with non-empty `errors` field. Those are sleep-30s-and-retry.

Sustainable sleep between requests: **1.5 seconds** (= 40/min = 2,400/hr, leaves headroom).

## Gotchas

- **Label cross-team rejection**: `IssueCreate` rejects with "Argument Validation Error: labelIds for incorrect team" when any label UUID is scoped to a different team than the issue's team. The skill resolves all label UUIDs from the team's labels CSV by name (case-insensitive) to avoid this.
- **Estimate values**: integers, not strings. Linear treats `1=XS, 2=S, 3=M, 5=L, 8=XL` by default but the values map to "label slots" in your team's settings — only verify by checking Linear UI if estimates look weird.
- **State UUIDs are per-team**: "Not Started" on DME Criteria has a different UUID than "Not Started" on Infusion Criteria.
