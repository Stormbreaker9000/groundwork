<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/gdpr/requirements/functional/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Functional requirements

The 3 functional requirements from the `gdpr` worked example, exactly as the pipeline wrote them.

## FR-001 — Export personal data as machine-readable archive [#fr-001]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| EARS pattern | event |
| Verification | test |

### Description
When an authenticated user submits a request to export their personal data,
the system shall generate a machine-readable archive containing all personal
data held for their account within 30 days of the request.

### Rationale
GDPR Article 20 grants a data subject the right to receive their personal
data in a portable format; self-service export discharges this legal
obligation directly and reduces the volume of manual
data-subject-access-request handling.

### Acceptance Criteria
#### AC-1 — Successful export request
```gherkin
Given an authenticated user with personal data held across the system's
  catalogued data stores
When the user submits a request to export their personal data
Then the system generates a machine-readable archive containing all of
  that personal data
And the archive is made available to the user within 30 days of the request
```

#### AC-2 — Archive completeness across all data stores
```gherkin
Given an authenticated user whose personal data spans multiple catalogued
  data stores
When the export archive is generated for that user's request
Then a field-level audit of the archive against the catalogued data map
  finds 0 omitted fields
```

### Fit Criterion
100% of export requests produce a downloadable archive within 30 days of
submission; a field-level audit of each generated archive against the
catalogued data map confirms 0 omitted fields, checked across a sample of
test accounts spanning every data store in scope.

## FR-002 — Erase account and personal data on confirmed deletion request [#fr-002]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | low |
| EARS pattern | event |
| Verification | test |
| Traces from | [BR-001](/guide/examples/gdpr/requirements/business-rules/#br-001), [BR-002](/guide/examples/gdpr/requirements/business-rules/#br-002), [CON-001](/guide/examples/gdpr/requirements/constraints/#con-001) |

### Description
When a data subject's deletion request has been confirmed, the system shall
permanently erase all personal data associated with the account within 30 days
of confirmation, excluding records subject to a statutory retention obligation.

### Rationale
Discharges the GDPR Article 17 right to erasure directly through self-service,
without requiring administrative or support intervention. Success is measured
by a post-deletion audit finding zero personal-data records outside the
documented statutory-retention set, and by the account becoming fully
inaccessible.

### Acceptance Criteria
#### AC-1 — Successful erasure excludes statutory-retention records
```gherkin
Given an authenticated data subject has confirmed a deletion request for their account
And the account has financial/tax records within their statutory retention period
When 30 days have elapsed since the deletion request was confirmed
Then all personal data associated with the account is erased from active personal-data stores
And the financial/tax records remain preserved in pseudonymised form, isolated from active personal-data stores
And a data audit of the account finds 0 personal-data records outside the documented statutory-retention set
```

#### AC-2 — Authentication fails against a deleted account
```gherkin
Given an authenticated data subject's deletion request has completed erasure
When any party attempts to authenticate using the deleted account's credentials
Then the authentication attempt fails
And no administrative or automated path restores access to the erased account
```

### Fit Criterion
For 100% of confirmed deletion requests sampled in acceptance testing, a data
audit conducted on or before day 30 after confirmation finds 0 personal-data
records for the account outside the documented statutory-retention set, and
100% of authentication attempts against the deleted account fail.

## FR-003 — Cancel unconfirmed account deletion request within 24-hour window [#fr-003]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| EARS pattern | unwanted |
| Verification | test |

### Description
If an account deletion request is not confirmed via re-authentication
within 24 hours of submission, then the system shall cancel the deletion
request and leave the account and its personal data unchanged.

### Rationale
Erasure is irreversible, so the deletion request must be confirmed by the
data subject themselves before it proceeds; bounding confirmation to a
24-hour window using the existing identity provider's step-up
re-authentication flow prevents an unconfirmed, unauthorized, or abandoned
request from leaving the account in an indefinitely pending or
accidentally-deleted state.

### Acceptance Criteria
#### AC-1 — Confirmation within the window proceeds
```gherkin
Given a data subject has submitted an account deletion request
When the data subject completes re-authentication via the identity
  provider within 24 hours of submission
Then the deletion request is confirmed and proceeds to erasure processing
```

#### AC-2 — Timeout cancels the request with no changes
```gherkin
Given a data subject has submitted an account deletion request
When 24 hours elapse from submission without the data subject completing
  re-authentication
Then the system cancels the deletion request
And the account and its personal data remain unchanged
```

### Fit Criterion
100% of deletion requests left unconfirmed for 24 hours are automatically
cancelled with 0 mutations to account state or personal data; 0 accounts
are deleted without a corresponding recorded re-authentication event
within the 24-hour window.
