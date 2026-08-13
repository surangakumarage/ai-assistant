import os
from fpdf import FPDF

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")

DOCS = []

def add(category, filename, doc_id, title, document_type, department,
        access_level, created_date, body, **extra):
    DOCS.append(dict(
        category=category, filename=filename, doc_id=doc_id, title=title,
        document_type=document_type, department=department,
        access_level=access_level, created_date=created_date, body=body,
        extra=extra,
    ))

BANK = "Meridian Commercial Bank"

# ---------------------------------------------------------------- INCIDENTS

add("incident_reports", "INC-2025-08-14-payment-gateway-timeout.pdf",
    "INC-2025-08-14-001", "Payment Gateway Timeout Outage - Card Present Transactions",
    "incident", "payments", "internal", "2025-08-14",
    severity="high", status="resolved",
    body="""Summary
Between 09:12 and 10:47 UTC on 2025-08-14, card-present transaction
authorizations routed through the Payments Gateway (PGW) experienced
elevated latency and timeouts. Approximately 18% of authorization requests
during the window failed with a gateway timeout (HTTP 504) rather than a
normal approve/decline response.

Timeline
09:12 - PGW p99 latency alert fires (>4500ms, threshold 1200ms).
09:18 - On-call payments engineer acknowledges; begins triage using the
Payment Gateway Failover runbook.
09:26 - Root cause suspected: connection pool exhaustion to the downstream
card network adapter (CNA) service after a CNA deployment at 09:05.
09:40 - Decision made to fail over PGW traffic to the secondary region.
10:05 - Failover completed; latency begins recovering.
10:47 - Latency fully recovered; incident downgraded to monitoring.
11:30 - Incident closed.

Root Cause
The Card Network Adapter (CNA) service was redeployed at 09:05 UTC with a
reduced connection pool size (default value was accidentally left at the
framework default of 10 instead of the tuned production value of 200).
Under normal peak load, PGW instances exhausted the available CNA
connections, causing requests to queue and eventually time out at the PGW's
5-second upstream timeout.

Impact
- Approximately 18% of card-present authorization attempts failed for 95
  minutes.
- Estimated 4,200 declined-in-error transactions.
- No funds were moved incorrectly; failures were pre-authorization.
- Merchant support received approximately 60 escalations.

Resolution
- Failed PGW traffic to secondary region (unaffected by the bad CNA
  config).
- CNA connection pool size restored to the tuned value of 200 and
  redeployed.
- Added a pre-deploy config diff check to the CNA deployment pipeline.

Action Items
1. Add automated regression test asserting CNA connection pool size before
   deploy (Owner: Payments Platform, Due: 2025-08-28).
2. Add PGW-to-CNA circuit breaker to fail fast instead of queuing under
   connection exhaustion (Owner: Payments Platform, Due: 2025-09-15).
3. Update the Payment Gateway Failover runbook with the CNA connection pool
   check as a first-line triage step (Owner: SRE, Due: 2025-08-21).""")

add("incident_reports", "INC-2025-10-02-card-authorization-outage.pdf",
    "INC-2025-10-02-002", "Card Authorization Service Outage - Database Failover Delay",
    "incident", "payments", "internal", "2025-10-02",
    severity="critical", status="resolved",
    body="""Summary
On 2025-10-02, the primary database for the Card Authorization Service
(CAS) experienced an unplanned failure. Automated failover to the replica
took longer than expected, resulting in a full outage of card
authorizations (both card-present and card-not-present) for 22 minutes.

Timeline
14:03 - Primary CAS database host becomes unreachable (underlying cloud
provider host failure).
14:04 - CAS health checks begin failing; all authorization requests return
HTTP 503.
14:05 - PagerDuty escalation to Payments on-call and Database on-call.
14:11 - Automated failover initiated but stalls due to replication lag
(replica was 40 seconds behind at time of failure, exceeding the automated
failover tool's 15-second safety threshold).
14:18 - Database on-call manually verifies replica data integrity and
forces failover.
14:25 - CAS reconnects to new primary; authorizations begin succeeding.
14:26 - Full recovery confirmed via synthetic transaction monitoring.

Root Cause
Replication lag between the CAS primary and its standby replica exceeded
the automated failover tool's safety threshold at the moment of failure,
forcing a manual decision point. The lag itself was caused by a large batch
reconciliation job that had been scheduled to run against the primary
during business hours, generating an unusually high write volume.

Impact
- 100% of card authorizations failed for 22 minutes (14:03-14:25 UTC).
- Estimated 31,000 transactions declined-in-error.
- SLA breach: CAS availability SLA is 99.95%; this incident alone consumed
  the monthly error budget.

Resolution
- Manual failover executed by Database on-call.
- Batch reconciliation job rescheduled to a maintenance window (02:00 UTC).
- Replication lag alerting threshold lowered from 60s to 20s warning.

Action Items
1. Move all batch/reconciliation jobs affecting CAS primary to the nightly
   maintenance window (Owner: Data Platform, Due: 2025-10-09) - COMPLETED.
2. Reduce automated failover safety threshold evaluation window, or add a
   force-failover-with-data-loss-acknowledgement fast path for on-call
   (Owner: Database Platform, Due: 2025-10-30).
3. Add synthetic authorization transaction probe at 10s interval (currently
   60s) to reduce detection time (Owner: SRE, Due: 2025-10-16).

Related Incidents
See INC-2025-08-14-001 (Payment Gateway Timeout) - different root cause
(connection pool exhaustion) but same downstream symptom class: card
authorization failures.""")

add("incident_reports", "INC-2025-12-19-ach-batch-failure.pdf",
    "INC-2025-12-19-003", "ACH Batch Payment Processing Failure - Year-End Volume Spike",
    "incident", "payments", "internal", "2025-12-19",
    severity="high", status="resolved",
    body="""Summary
The nightly ACH batch processing job on 2025-12-19 failed partway through
execution, leaving approximately 6,300 outbound ACH payments (payroll and
vendor disbursements) unprocessed and delayed by one business day.

Timeline
02:00 - Nightly ACH batch job starts (volume: 118,000 transactions, about
2.4x normal due to year-end payroll runs).
02:41 - Batch worker pool begins reporting OutOfMemoryError on 3 of 12
worker nodes.
02:44 - Job orchestrator marks batch as FAILED and halts remaining shards
to avoid partial/duplicate submission to the Fed ACH network.
03:15 - Payments on-call paged via automated batch-failure alert.
07:30 - Engineering team (business hours start) confirms 6,300 of the
118,000 transactions in the failed shards were not submitted.
09:00 - Manual re-run of the 3 failed shards after increasing worker memory
limits.
10:12 - Remaining transactions submitted successfully to the Fed ACH
network same-day, but after the 09:00 same-day submission cutoff, so they
settled one business day late.

Root Cause
ACH batch workers were provisioned with a fixed memory limit sized for
average daily volume (about 50,000 transactions). The year-end payroll
spike (118,000 transactions) was not accounted for in capacity planning,
causing in-memory batch buffers on 3 worker nodes to exceed the container
memory limit.

Impact
- 6,300 payroll/vendor ACH payments delayed by one business day.
- No payments were lost or duplicated; the halt-on-failure design worked as
  intended to prevent double submission.
- Customer support fielded approximately 140 inquiries from affected
  payees.

Resolution
- Re-ran failed shards with increased memory limits.
- Notified affected business customers of the one-day delay.

Action Items
1. Add seasonal/calendar-aware capacity planning for ACH batch workers,
   particularly around month-end and year-end payroll cycles (Owner:
   Payments Platform, Due: 2026-01-31).
2. Implement dynamic worker autoscaling based on queued transaction count
   rather than a fixed worker pool (Owner: Payments Platform, Due:
   2026-02-28).
3. Add a pre-flight volume estimate check that pages on-call proactively
   when a batch run is more than 1.5x the trailing 30-day average (Owner:
   SRE, Due: 2026-01-15).

Related Incidents
This is the third payments-related incident in Q3-Q4 2025 involving
resource exhaustion under load (see INC-2025-08-14-001 connection pool
exhaustion, INC-2025-10-02-002 database write load). Recurring theme:
capacity limits not scaled to real-world peak/seasonal load.""")

add("incident_reports", "INC-2026-02-27-wire-transfer-duplicate.pdf",
    "INC-2026-02-27-004", "Duplicate Wire Transfer Submissions Due to Client Retry Storm",
    "incident", "payments", "internal", "2026-02-27",
    severity="critical", status="resolved",
    body="""Summary
A retry storm from the Business Banking web client caused 214 wire transfer
requests to be submitted more than once to the Wire Transfer Service (WTS)
between 11:02 and 11:19 UTC on 2026-02-27. 37 of these resulted in
duplicate wires being sent before the issue was caught.

Timeline
11:02 - WTS API latency increases due to an unrelated downstream compliance
screening service slowdown (average response time 800ms to 6200ms).
11:04 - Business Banking web client's request layer, which has a 5-second
timeout and automatic retry (up to 3 attempts) with no idempotency key,
begins retrying slow-but-in-flight wire submissions.
11:06 - WTS request volume spikes 3.5x normal.
11:14 - Duplicate-transaction detection job (runs every 10 minutes) flags
37 potential duplicate wires already submitted to the correspondent bank
network.
11:19 - Client-side retry logic identified as root cause; feature-flagged
off for the Business Banking web client.
11:45 - Payments Operations begins manual recall/reversal process for the
37 duplicate wires with the correspondent bank.
16:30 - 34 of 37 duplicate wires successfully recalled; 3 required direct
customer contact and manual reversal, completed by 2026-02-28.

Root Cause
Two contributing factors: (1) the compliance screening service slowdown
increased WTS end-to-end latency past the client's 5-second timeout, and
(2) the Business Banking web client's retry logic did not attach an
idempotency key to wire submission requests, so WTS could not distinguish a
retried request from a genuinely new wire.

Impact
- 37 duplicate wire transfers sent, total duplicate value approximately
  $1.86M.
- 34 recalled same-day; 3 required manual customer-facing resolution.
- No permanent customer funds loss; full recovery within 30 hours.
- Reputational risk flagged given direct customer/counterparty impact.

Resolution
- Disabled client-side auto-retry for wire submission pending idempotency
  key support.
- Manual recall process executed by Payments Operations.
- Emergency scaling applied to the compliance screening service.

Action Items
1. Require idempotency keys on all wire submission endpoints; reject
   duplicate submissions server-side (Owner: Payments Platform, Due:
   2026-03-20) - HIGH PRIORITY.
2. Audit all client applications (web, mobile, partner API) for retry logic
   on payment-initiating endpoints without idempotency keys (Owner:
   Engineering, Due: 2026-03-31).
3. Reduce duplicate-detection job interval from 10 minutes to 1 minute for
   wire transfers specifically (Owner: Payments Platform, Due: 2026-03-06).
4. Add compliance screening service to the payments platform's critical
   dependency SLO dashboard (Owner: SRE, Due: 2026-03-13).

Related Incidents
Root cause category (missing idempotency protection) is new to this
incident cluster; prior 2025 incidents were capacity/connection related.
Recommend a cross-cutting review of idempotency coverage across all payment
initiation paths.""")

add("incident_reports", "INC-2026-05-11-payment-gateway-timeout-recurrence.pdf",
    "INC-2026-05-11-005", "Payment Gateway Timeout Recurrence - CNA Connection Pool",
    "incident", "payments", "internal", "2026-05-11",
    severity="high", status="resolved",
    body="""Summary
On 2026-05-11, the Payments Gateway (PGW) experienced a second connection
pool exhaustion incident against the Card Network Adapter (CNA) service,
closely resembling INC-2025-08-14-001 from nine months earlier. Approximately
11% of card-present authorizations timed out over a 40-minute window.

Timeline
15:20 - PGW p99 latency alert fires.
15:24 - On-call recognizes the pattern from INC-2025-08-14-001 and checks
CNA connection pool configuration first, per the updated runbook.
15:27 - Confirms CNA connection pool size was reduced to 10 again, this
time due to a configuration management tool reverting to a stale template
during an unrelated infrastructure-as-code refactor.
15:35 - Connection pool size corrected and CNA redeployed.
16:00 - Latency fully recovered.

Root Cause
The CNA connection pool size (200) had been set as a manual override outside
the standard infrastructure-as-code (IaC) templates after INC-2025-08-14-001.
An unrelated IaC refactor in April 2026 consolidated service configs into a
shared template, which did not carry forward the manual override, silently
resetting the pool size to the framework default of 10 on the next deploy.

Impact
- Approximately 11% of card-present authorizations failed for 40 minutes.
- Estimated 1,900 declined-in-error transactions.
- Detected and resolved faster than the original incident (40 min vs 95
  min) due to the runbook update from the 2025-08-14 action items.

Resolution
- Corrected CNA connection pool size and redeployed.
- Added the connection pool size as a required, tested field in the CNA IaC
  module rather than a manual override.

Action Items
1. Convert all "manual override" post-incident fixes into first-class,
   tested IaC configuration rather than out-of-band changes (Owner:
   Platform Engineering, Due: 2026-05-25).
2. Add a config-drift detection job that diffs live service configuration
   against the last known-good incident-remediation baseline (Owner: SRE,
   Due: 2026-06-15).

Related Incidents
Direct recurrence of INC-2025-08-14-001. Root cause category: configuration
drift undoing a prior incident remediation. This is a distinct systemic
issue from the capacity-planning theme in INC-2025-10-02-002 and
INC-2025-12-19-003, and warrants its own action-item tracking separate from
capacity/scaling fixes.""")

add("incident_reports", "INC-2026-07-08-mobile-app-login-outage.pdf",
    "INC-2026-07-08-006", "Mobile Banking App Login Outage - Identity Provider Certificate Expiry",
    "incident", "retail_banking", "internal", "2026-07-08",
    severity="high", status="resolved",
    body="""Summary
On 2026-07-08, customers were unable to log in to the Meridian mobile
banking app for 53 minutes due to an expired TLS certificate on the
internal Identity Provider (IdP) token-signing endpoint. This incident is
unrelated to the payments platform and is included here as a contrasting
non-payments example.

Timeline
06:00 - IdP token-signing certificate expires (renewal automation job had
failed silently three weeks prior).
06:00 - Mobile app login requests begin failing with certificate validation
errors on the client side.
06:12 - Elevated login-failure-rate alert fires.
06:20 - On-call identifies the expired certificate via IdP service logs.
06:35 - Emergency certificate reissued and deployed.
06:53 - Login success rate returns to baseline.

Root Cause
The automated certificate renewal job silently failed three weeks before
expiry due to an unrelated IAM permissions change that revoked the
renewal service account's access to the certificate authority. No alert
existed for renewal job failures, only for certificate expiry itself, which
did not fire until the day of expiry.

Impact
- Mobile app login failures for 53 minutes affecting an estimated 22,000
  customer sessions.
- Web banking and card transactions were unaffected (separate IdP
  integration).

Resolution
- Emergency certificate reissued.
- Added a dedicated alert for certificate renewal job failures (not just
  expiry).

Action Items
1. Add renewal-job-failure alerting for all automated certificate rotation
   jobs (Owner: Identity Platform, Due: 2026-07-22).
2. Audit IAM permission changes for downstream effects on automation
   service accounts before rollout (Owner: Security, Due: 2026-08-05).
3. Reduce certificate validity period and increase renewal lead time to
   catch failures earlier (Owner: Identity Platform, Due: 2026-08-15).""")

# ----------------------------------------------------------------- RUNBOOKS

add("runbooks", "RB-payment-gateway-failover.pdf",
    "RB-PGW-001", "Runbook: Payment Gateway Regional Failover",
    "runbook", "payments", "internal", "2025-08-21",
    body="""Purpose
This runbook describes how to fail over Payments Gateway (PGW) traffic from
the primary region to the secondary region during a latency or availability
incident, and the first-line triage steps to run before deciding to fail
over.

When To Use This Runbook
- PGW p99 latency exceeds 1200ms for more than 5 minutes.
- PGW error rate (5xx) exceeds 2% for more than 3 minutes.
- Any PGW-related page during a card authorization incident.

First-Line Triage (check before failing over)
1. Check CNA (Card Network Adapter) connection pool metrics in the
   payments-platform Grafana dashboard, panel "CNA Pool Utilization." If
   utilization is pinned at 100%, this is very likely a repeat of the
   connection-pool-exhaustion failure mode (see INC-2025-08-14-001 and
   INC-2026-05-11-005). Fixing the CNA config directly may resolve the
   issue without a full failover.
2. Check the deployments feed for any CNA or PGW deployment in the last 30
   minutes. A recent deploy is the most common trigger.
3. Check downstream dependency health (compliance screening, fraud
   scoring) in the dependency status page. A downstream slowdown may be the
   true root cause rather than PGW itself.

Failover Procedure
1. Confirm with the Payments on-call lead that failover is warranted (not
   required for a single-service config fix identified in triage).
2. Run: pgw-cli failover --to-region secondary --reason "<incident-id>"
3. Monitor the PGW dashboard for traffic shift completion (typically 2-4
   minutes).
4. Verify synthetic transaction success rate returns to baseline (>99.5%)
   in the secondary region.
5. Post an update in #incident-payments with current status.

Fail-Back Procedure
1. Once the root cause in the primary region is fixed and verified in a
   staging deploy, run: pgw-cli failback --to-region primary
2. Monitor for 30 minutes before closing the incident.

Escalation
- Payments Platform on-call (PagerDuty schedule: payments-platform-primary)
- If unresolved after 30 minutes, escalate to Payments Engineering Manager.
- For customer-facing communication decisions, loop in Customer Support
  Lead.

Related Documents
- ARCH-payments-platform-overview
- INC-2025-08-14-001, INC-2026-05-11-005 (connection pool exhaustion
  incidents this runbook was updated in response to)""")

add("runbooks", "RB-database-restore.pdf",
    "RB-DB-002", "Runbook: Production Database Point-in-Time Restore",
    "runbook", "core_banking", "internal", "2025-06-10",
    body="""Purpose
Describes the process for restoring a production database to a specific
point in time, used for both disaster recovery and data-correction
scenarios (for example, recovering from a bad batch job or data corruption
event).

Preconditions
- Confirm the target restore time with the requesting engineer and, for any
  restore affecting customer-facing data, with the Database Platform Lead.
- Confirm whether a fresh restore (new instance) or in-place restore is
  required. In-place restores cause downtime and require a maintenance
  window; fresh restores can run alongside production.

Procedure (Fresh Restore, Preferred)
1. Identify the nearest snapshot before the target restore time in the
   backup catalog: db-cli backups list --db <db-name>
2. Provision a new instance from that snapshot: db-cli restore
   --snapshot <snapshot-id> --target-instance <new-instance-name>
3. Apply write-ahead log (WAL) replay to reach the exact target timestamp:
   db-cli wal-replay --instance <new-instance-name> --until <timestamp>
4. Validate data integrity against expected row counts / checksums provided
   by the requesting team.
5. If this is a disaster-recovery failover (not a data-correction restore),
   promote the new instance to primary following the "Primary Promotion"
   section of this runbook and update connection strings in the service
   configuration.

Procedure (In-Place Restore, Requires Downtime)
1. Schedule and announce a maintenance window; this always requires sign-off
   from the Database Platform Lead and the affected service owner.
2. Stop write traffic to the affected database (drain connections, put
   dependent services into maintenance mode).
3. Follow steps 1-4 above but restore into the existing instance.
4. Resume write traffic and monitor error rates for 30 minutes.

Rollback
If validation fails after a fresh restore, simply discard the new instance;
production is unaffected. If validation fails after an in-place restore,
restore again from an earlier snapshot and extend the maintenance window.

Escalation
- Database Platform on-call (PagerDuty schedule: db-platform-primary)
- For restores affecting the Card Authorization Service or Wire Transfer
  Service specifically, also page Payments Platform on-call for
  coordination, referencing INC-2025-10-02-002 as a precedent where
  replication/restore timing directly affected payments availability.""")

add("runbooks", "RB-incident-response-process.pdf",
    "RB-IR-003", "Runbook: Incident Response Process and Severity Definitions",
    "runbook", "engineering", "internal", "2025-05-01",
    body="""Purpose
Defines the standard incident response process at Meridian Commercial Bank,
including severity levels, roles, and communication expectations. This
process applies to all production incidents regardless of department.

Severity Definitions
- Critical: Full outage of a customer-facing or payment-critical service,
  or any incident involving incorrect movement of customer funds. Page
  immediately, all-hands response, executive notification within 30
  minutes.
- High: Significant degradation (partial outage, elevated error rate above
  5%) of a customer-facing or payment-critical service. Page on-call
  immediately.
- Medium: Degradation of a non-critical service or a critical service with
  a known workaround. Notify on-call, response during business hours if
  outside working hours.
- Low: Minor issue with no material customer impact. Track as a ticket, no
  paging required.

Roles
- Incident Commander (IC): Owns the incident timeline, coordinates
  responders, makes the call on major decisions (e.g., failover,
  rollback). For Critical incidents, the IC is a designated Staff+
  engineer or engineering manager.
- Technical Lead: The subject-matter expert actively diagnosing and fixing
  the issue (often the paged on-call engineer).
- Communications Lead: Owns customer/stakeholder communication, status
  page updates, and internal updates in #incident-<name>.

Process
1. Detect: Alert fires or issue is reported.
2. Triage: On-call assesses severity using the definitions above.
3. Declare: For High/Critical, formally declare an incident (creates an
   incident channel, assigns IC).
4. Mitigate: Focus on restoring service first; root cause analysis can wait.
5. Resolve: Confirm service restored via monitoring/synthetic checks.
6. Document: Write the incident report within 2 business days using the
   standard incident report template (see any file under
   docs/incident_reports for the expected format: Summary, Timeline, Root
   Cause, Impact, Resolution, Action Items).
7. Review: Blameless postmortem review within 1 week for High/Critical
   incidents; action items tracked to completion.

Communication Cadence
- Critical: updates every 15 minutes until mitigated.
- High: updates every 30 minutes until mitigated.
- Medium/Low: update on state changes only.

Related Documents
- RB-payment-gateway-failover, RB-database-restore (service-specific
  runbooks referenced during triage/mitigate steps)""")

add("runbooks", "RB-card-fraud-alert-triage.pdf",
    "RB-FRAUD-004", "Runbook: Card Fraud Alert Triage",
    "runbook", "security", "internal", "2025-11-05",
    body="""Purpose
Describes how the Fraud Operations team triages real-time card fraud alerts
generated by the fraud scoring engine, and when to escalate to card
blocking or law enforcement referral.

Alert Categories
- Velocity Alert: Unusual transaction frequency on a single card in a short
  window.
- Geo-Anomaly Alert: Transaction location inconsistent with recent card
  usage pattern.
- Score Alert: Fraud model score exceeds the configured threshold (default
  0.85) for a single transaction.

Triage Steps
1. Review the alert detail in the Fraud Console, including the fraud score
   contributing factors.
2. Cross-reference recent customer contact history (has the customer
   reported travel, a lost card, etc.) in the CRM.
3. For Score Alerts above 0.95, or any alert combined with a customer-
   reported lost/stolen card, block the card immediately and issue a
   temporary hold; notify the customer via the configured contact method.
4. For Score Alerts between 0.85 and 0.95 without corroborating signals,
   place a soft hold (next transaction requires step-up verification) and
   queue for manual review within 4 hours.
5. Document disposition (confirmed fraud, false positive, inconclusive) in
   the Fraud Console; this feeds back into fraud model retraining.

Escalation
- Confirmed fraud above $10,000: escalate to Fraud Operations Lead and open
  a case with the card network's fraud liaison.
- Suspected organized/ring fraud (multiple related alerts): escalate to
  Security Investigations team and Fraud Operations Lead simultaneously.

Related Documents
- ARCH-identity-access-management (for authentication step-up mechanics)
- SPEC-card-controls (customer-facing card lock/unlock feature that Fraud
  Operations can also trigger on the customer's behalf)""")

# ------------------------------------------------------------ ARCHITECTURE

add("architecture_docs", "ARCH-payments-platform-overview.pdf",
    "ARCH-PAY-001", "Architecture: Payments Platform Overview",
    "architecture", "payments", "internal", "2025-07-01",
    body="""Overview
The Payments Platform handles card authorizations, ACH batch transfers, and
wire transfers for Meridian Commercial Bank. It is composed of four primary
services: the Payments Gateway (PGW), the Card Authorization Service (CAS),
the ACH Batch Processor, and the Wire Transfer Service (WTS).

Components
- Payments Gateway (PGW): Entry point for all card-present and
  card-not-present authorization requests from merchants and internal
  channels. Routes to the Card Network Adapter (CNA), which integrates with
  external card network APIs (Visa/Mastercard equivalents in this fictional
  environment).
- Card Authorization Service (CAS): Maintains card status, limits, and
  authorization holds. Backed by a primary/replica relational database
  with automated failover.
- ACH Batch Processor: Runs nightly batch jobs to submit outbound ACH
  payments (payroll, vendor disbursements, customer transfers) to the Fed
  ACH network, and ingest inbound ACH files.
- Wire Transfer Service (WTS): Handles real-time, high-value wire transfers
  with mandatory compliance screening (sanctions/AML checks) before
  submission to the correspondent banking network.

Data Flow (Card Authorization)
Merchant terminal -> PGW -> CAS (limit/status check) -> CNA -> external
card network -> response propagated back through CNA -> PGW -> merchant
terminal. Target end-to-end latency: under 800ms p99.

Data Flow (Wire Transfer)
Customer request (web/mobile/branch) -> WTS -> Compliance Screening Service
(sanctions/AML) -> WTS -> correspondent bank network -> confirmation back to
WTS -> customer notification.

Reliability Posture
- PGW and CAS run active-active across two regions; CAS uses a
  primary/replica database with automated failover (see
  RB-database-restore).
- WTS and the ACH Batch Processor run active-passive; WTS has no automated
  regional failover as of this writing (tracked as a platform gap).
- Availability SLA: CAS and PGW 99.95%; WTS 99.9%; ACH Batch Processor
  99.5% (batch, not real-time).

Known Gaps / Active Work
- Idempotency key support is being added to WTS following
  INC-2026-02-27-004 (duplicate wire transfers).
- Capacity planning for the ACH Batch Processor is being revised to be
  calendar-aware following INC-2025-12-19-003 (year-end volume spike).
- CNA connection pool configuration has caused two incidents
  (INC-2025-08-14-001, INC-2026-05-11-005) and is being migrated to
  enforced IaC configuration.

Related Documents
- RB-payment-gateway-failover
- INC-2025-08-14-001, INC-2025-10-02-002, INC-2025-12-19-003,
  INC-2026-02-27-004, INC-2026-05-11-005""")

add("architecture_docs", "ARCH-core-banking-integration.pdf",
    "ARCH-CORE-002", "Architecture: Core Banking Integration Layer",
    "architecture", "core_banking", "internal", "2025-04-15",
    body="""Overview
The Core Banking Integration Layer (CBIL) sits between customer-facing
channels (web, mobile, branch systems) and the core ledger system of
record. It exists to decouple channel teams from the core ledger's legacy
batch-oriented interface, exposing a modern async API surface instead.

Components
- Ledger Adapter: Translates async API calls into the core ledger's native
  batch file format, queues them, and polls for completion.
- Balance Cache: A near-real-time read replica of account balances,
  refreshed via change-data-capture from the core ledger, used to serve
  low-latency balance inquiries without hitting the ledger directly.
- Event Publisher: Publishes account and transaction events (deposit,
  withdrawal, hold placed/released) to an internal event bus consumed by
  downstream systems such as fraud scoring and customer notifications.

Design Rationale
The core ledger system processes updates in batch windows every 15
minutes, which is incompatible with customer expectations of near-instant
balance updates. The Balance Cache exists specifically to bridge this gap:
writes go through the Ledger Adapter (eventually consistent, batch-backed),
while reads are served from the cache (near-real-time, seconds of lag via
CDC) for a responsive user experience.

Consistency Model
CBIL is eventually consistent by design. The Balance Cache may lag the
authoritative ledger by up to 15 seconds under normal operation. Any
feature requiring strong consistency (e.g., final balance check
immediately before a large wire transfer) must read directly from the
Ledger Adapter's synchronous confirmation path, not the Balance Cache.

Failure Modes
- If CDC lag exceeds 60 seconds, the Balance Cache is marked stale and
  read requests are transparently routed to the synchronous Ledger Adapter
  path (higher latency but always fresh).
- If the Ledger Adapter's batch queue backs up, writes are still accepted
  and queued; customers see a "pending" transaction state rather than a
  failure.

Related Documents
- ARCH-payments-platform-overview (Payments Platform is a consumer of
  CBIL's Ledger Adapter for settlement)
- ARCH-data-platform (Event Publisher feeds the Data Platform's event
  ingestion pipeline)""")

add("architecture_docs", "ARCH-data-platform.pdf",
    "ARCH-DATA-003", "Architecture: Enterprise Data Platform",
    "architecture", "data_platform", "internal", "2025-03-20",
    body="""Overview
The Enterprise Data Platform (EDP) ingests, stores, and serves data from
across Meridian Commercial Bank's operational systems for analytics,
reporting, regulatory compliance, and (as of 2026) the internal AI
Assistant's knowledge retrieval layer.

Components
- Ingestion Layer: Consumes events from the Core Banking Integration
  Layer's Event Publisher, plus scheduled extracts from operational
  databases and uploaded document repositories (policies, runbooks,
  incident reports, etc.).
- Object Storage: Raw and processed data lake, partitioned by domain
  (payments, retail_banking, core_banking, security) and date.
- Document Index: A hybrid dense/sparse vector index (embeddings +
  keyword/BM25) over unstructured documents, with metadata filtering by
  department, document_type, access_level, and created_date. This is the
  retrieval backend for the internal AI Assistant.
- Warehouse: Structured analytics tables for BI dashboards and regulatory
  reporting, refreshed nightly.

Data Governance
- All documents ingested into the Document Index carry an access_level tag
  (public, internal, confidential, restricted). The AI Assistant's
  retrieval layer enforces role-based filtering on this field so that, for
  example, a Viewer-role user cannot retrieve confidential documents even
  if the document is topically relevant to their query.
- Data lineage is tracked per ingestion job; every record in the Warehouse
  can be traced back to its source system and ingestion timestamp.

Access Model
Access to raw Object Storage is restricted to Data Platform engineers.
Access to the Warehouse and Document Index is mediated entirely through
service APIs (including the AI Assistant backend), which enforce
authentication and role-based authorization before any query executes.

Related Documents
- ARCH-identity-access-management (authentication/authorization enforced at
  the API layer described above)
- ARCH-core-banking-integration (primary event source for the Ingestion
  Layer)""")

add("architecture_docs", "ARCH-identity-access-management.pdf",
    "ARCH-IAM-004", "Architecture: Identity and Access Management",
    "architecture", "security", "internal", "2025-02-10",
    body="""Overview
Describes the Identity and Access Management (IAM) architecture used across
Meridian Commercial Bank's internal and customer-facing systems, including
the role model used by the internal AI Assistant.

Components
- Identity Provider (IdP): Issues signed tokens (short-lived access tokens
  plus refresh tokens) for both customer-facing apps and internal tools.
  Token signing keys rotate on a scheduled basis via automated certificate
  renewal (see INC-2026-07-08-006 for a case where this automation failed).
- Role Service: Maintains role assignments for internal users. For the
  internal AI Assistant POC, three roles are defined: Viewer, Analyst, and
  Administrator.
- Policy Enforcement Point (PEP): A shared authorization library used by
  internal services (including the AI Assistant backend) to check whether
  a given role may perform a given action before executing it.

Role Definitions (Internal AI Assistant)
- Viewer: May use chat and knowledge search. May not invoke administrative
  or analytical tools.
- Analyst: May use search, analytics tools (Python Analysis Tool), and MCP
  tools (employee directory, service catalog, incident records).
- Administrator: May use all tools, including reindexing the knowledge base
  and viewing system-wide usage/feedback data.

Enforcement Principle
Authorization checks must be enforced at the point of tool execution on the
backend, never solely in the UI or solely via prompt instructions to the
LLM. This ensures that neither a modified client request nor a crafted
prompt-injection attempt can cause the agent to bypass role restrictions
enforced by the PEP.

Related Documents
- ARCH-data-platform (Document Index access filtering uses the same role
  model)
- RB-card-fraud-alert-triage (Fraud Operations step-up verification uses
  the IdP's step-up authentication flow)""")

# ------------------------------------------------------------ PRODUCT SPECS

add("product_specs", "SPEC-mobile-instant-transfer.pdf",
    "SPEC-MOBILE-001", "Product Spec: Mobile Instant Transfer",
    "product_spec", "product", "internal", "2025-09-10",
    body="""Overview
Instant Transfer lets customers send money to another Meridian customer
using just a phone number or email address, with funds available to the
recipient within seconds rather than the 1-3 business days typical of
standard transfers.

Goals
- Enable peer-to-peer transfers that settle in under 10 seconds for
  Meridian-to-Meridian transfers.
- Support transfer limits configurable per customer risk tier.
- Provide clear, real-time status (sent, received, failed) in the mobile
  app.

Non-Goals
- Cross-bank instant transfers (out of scope for this version; routed
  through standard ACH rails instead).
- Business-to-business transfers (covered separately by
  SPEC-business-loan-portal's disbursement flow for loan-related
  payments only).

Requirements
1. Sender selects a recipient by phone/email; the app resolves this to a
   Meridian account via the Recipient Lookup service (opt-in only;
   customers must have registered a phone/email for lookup).
2. Sender enters an amount, subject to the customer's daily instant-
   transfer limit (default $2,500/day, configurable per risk tier by Fraud
   Operations).
3. Transfer request is screened by the fraud scoring engine in real time
   (target: under 500ms) before funds move.
4. On approval, funds are moved via the Core Banking Integration Layer's
   synchronous Ledger Adapter path (not the Balance Cache) to guarantee
   consistency for both sender and recipient balances.
5. Both parties receive a push notification on completion.
6. Failed transfers (fraud hold, insufficient funds, recipient not found)
   return a specific, customer-readable error reason.

Dependencies
- Core Banking Integration Layer (synchronous ledger path) - see
  ARCH-core-banking-integration.
- Fraud scoring engine - see RB-card-fraud-alert-triage for the underlying
  fraud alert triage process this feature's scoring feeds into.

Open Questions
- Should recipients without the Meridian app be able to claim a transfer
  via a web link? Deferred to v2.
- Should instant transfer limits stack with existing ACH transfer limits or
  be tracked independently? Currently independent; revisit after 90 days
  of production data.""")

add("product_specs", "SPEC-savings-goals-feature.pdf",
    "SPEC-SAVE-002", "Product Spec: Savings Goals",
    "product_spec", "product", "internal", "2025-06-18",
    body="""Overview
Savings Goals lets customers create named sub-accounts within their savings
account (e.g., "Vacation," "Emergency Fund") with individual progress
tracking, without opening separate formal accounts.

Goals
- Increase savings account engagement and average balance retention.
- Provide visual progress tracking toward customer-defined goals.
- Support optional automated recurring transfers into a goal.

Requirements
1. Customers can create up to 10 goals per savings account, each with a
   name, target amount, and optional target date.
2. Goals are implemented as sub-ledger tracking within the existing savings
   account (not separate core ledger accounts), maintained by the Core
   Banking Integration Layer's Balance Cache with a "goal_allocations"
   extension.
3. Customers can manually move funds between goals and the unallocated
   balance at any time, subject to standard savings account transaction
   limits (Regulation D style, 6 transfers/month in this fictional
   context).
4. Optional recurring auto-transfer into a goal (daily/weekly/monthly),
   configured by the customer, executed via a scheduled job.
5. Progress is shown as a percentage and dollar amount toward the target in
   the mobile and web apps.

Dependencies
- ARCH-core-banking-integration (sub-ledger allocation is an extension of
  the existing Balance Cache design; does not require new ledger accounts).

Non-Goals
- Goals do not earn a different interest rate than the parent savings
  account in this version.
- No goal-sharing between multiple customers (e.g., joint savings goals) in
  this version.

Open Questions
- Should goal funds be excluded from the available balance shown at ATMs /
  card-linked transactions to prevent accidental spending? Current
  decision: no, goals are a soft allocation only, not a hold. Revisit based
  on early customer feedback.""")

add("product_specs", "SPEC-card-controls.pdf",
    "SPEC-CARD-003", "Product Spec: Self-Service Card Controls",
    "product_spec", "product", "internal", "2025-10-25",
    body="""Overview
Self-Service Card Controls let customers lock/unlock their debit or credit
card instantly from the mobile app, and set merchant-category or geographic
spending restrictions, without contacting support.

Goals
- Reduce fraud-related support call volume by letting customers self-serve
  common actions (lost card, suspected fraud, travel).
- Give customers proactive control to prevent unwanted spending categories
  (e.g., gambling, online purchases) for themselves or authorized users on
  the account.

Requirements
1. Instant lock/unlock: toggling the lock in the app applies within 2
   seconds by writing directly to the Card Authorization Service's card
   status field; CAS checks this status on every authorization request.
2. Merchant-category blocking: customers can toggle categories (e.g.,
   gambling, online purchases, international transactions) on or off;
   blocked categories are declined at authorization time with a
   customer-facing reason code.
3. Geographic restriction: customers can restrict card usage to their home
   country; travel notifications temporarily lift this restriction for a
   customer-specified date range.
4. All control changes are logged and available in an audit view within the
   app for the customer's own reference.
5. Fraud Operations can also apply a lock on the customer's behalf (see
   RB-card-fraud-alert-triage); customer-initiated unlock does not override
   a fraud-initiated lock without a step-up verification flow.

Dependencies
- Card Authorization Service (ARCH-payments-platform-overview) for the
  real-time status/category check on every authorization.
- ARCH-identity-access-management for the step-up verification flow used
  when unlocking a fraud-initiated hold.

Non-Goals
- Per-transaction manual approval (customer approves each transaction
  individually) is out of scope; considered for a future "Card Controls
  Pro" tier.""")

add("product_specs", "SPEC-business-loan-portal.pdf",
    "SPEC-LOAN-004", "Product Spec: Business Loan Application Portal",
    "product_spec", "product", "internal", "2026-01-14",
    body="""Overview
The Business Loan Application Portal allows small-business customers to
apply for, track, and (upon approval) receive disbursement of a business
loan entirely online, replacing the current branch-only application
process.

Goals
- Reduce average time-to-decision from 10 business days (branch process) to
  2 business days for loans under $250,000.
- Provide applicants with real-time status visibility instead of requiring
  phone follow-up.

Requirements
1. Application intake: business financials, ownership information, and
   requested loan amount/purpose, with document upload for supporting
   materials (tax returns, financial statements).
2. Automated pre-screening: a rules-based check (credit score threshold,
   debt-to-income ratio, business age) runs immediately on submission;
   applications failing pre-screening are routed to manual review rather
   than auto-declined, to avoid false negatives on edge cases.
3. Underwriting queue: applications passing pre-screening enter a
   underwriter review queue with SLA tracking (target: 2 business days for
   loans under $250,000; 5 business days above that threshold).
4. Disbursement: upon approval, funds are disbursed via the ACH Batch
   Processor (see ARCH-payments-platform-overview) into the business's
   designated Meridian account, or an external account via standard ACH if
   the business does not hold a Meridian deposit account.
5. Status tracking: applicants see one of Submitted, Pre-Screening,
   Under Review, Approved, Declined, Disbursed at each stage.

Dependencies
- ACH Batch Processor for disbursement (subject to the same batch-window
  and capacity-planning considerations noted in INC-2025-12-19-003;
  large disbursement batches around month-end should be flagged to
  Payments Platform in advance).

Open Questions
- Should pre-approved existing customers get an expedited underwriting
  path? Under discussion with Underwriting leadership, not yet decided for
  v1.
- Loan servicing (payments, statements) is handled by a separate existing
  system and is explicitly out of scope for this portal.""")

# ------------------------------------------------------------- MEETING NOTES

add("meeting_notes", "MN-2025-09-payments-reliability-review.pdf",
    "MN-2025-09-001", "Meeting Notes: Payments Reliability Quarterly Review",
    "meeting_notes", "payments", "internal", "2025-09-18",
    body="""Attendees
Payments Platform Engineering, SRE, Payments Product, Engineering
Leadership.

Agenda
1. Review of Q3 payments incidents.
2. CNA connection pool remediation status.
3. Q4 reliability priorities.

Discussion
The team reviewed INC-2025-08-14-001 (payment gateway timeout) and
INC-2025-10-02-002 (card authorization outage) in detail. Both incidents
shared a common theme: capacity/resource limits not scaled to real
production load, and both had clear, completed short-term remediations.

There was concern raised that the CNA connection pool fix was applied as a
manual override rather than being enforced in infrastructure-as-code,
creating risk of future config drift silently reintroducing the issue.
Action assigned to Platform Engineering to convert this into a proper IaC
change, though this was not completed by year-end (see
INC-2026-05-11-005, which confirms this exact drift scenario occurred).

Decisions
- Q4 reliability priority #1: circuit breaker for PGW-to-CNA calls to fail
  fast rather than queue under connection exhaustion.
- Q4 reliability priority #2: synthetic transaction probe interval reduced
  across all payments services, not just CAS.
- Agreed to schedule a follow-up in November to check status of open
  action items from both incidents.

Action Items
1. Platform Engineering: convert CNA connection pool config to enforced
   IaC (carried over, still open as of this meeting).
2. SRE: implement PGW-to-CNA circuit breaker by end of Q3.
3. Payments Product: communicate Q4 reliability roadmap to customer-facing
   teams so support staff understand upcoming changes.""")

add("meeting_notes", "MN-2026-01-quarterly-roadmap.pdf",
    "MN-2026-01-002", "Meeting Notes: Q1 2026 Product Roadmap Planning",
    "meeting_notes", "product", "internal", "2026-01-08",
    body="""Attendees
Product Leadership, Engineering Leadership, Design, representatives from
Retail Banking and Business Banking.

Agenda
1. Review Q4 2025 delivery against plan.
2. Q1 2026 priorities across product lines.
3. Cross-team dependency check.

Discussion
Q4 delivery review: Savings Goals (SPEC-savings-goals-feature) shipped on
schedule in December. Self-Service Card Controls (SPEC-card-controls)
shipped two weeks late due to additional work needed on the step-up
verification integration with Identity Platform.

The ACH batch failure incident from December (INC-2025-12-19-003) was
raised as a dependency risk for the Business Loan Application Portal
(SPEC-business-loan-portal), since loan disbursement relies on the same ACH
Batch Processor. Payments Platform confirmed the seasonal capacity fix is
scheduled for completion by end of January, ahead of the loan portal's
planned Q1 launch.

Q1 2026 priorities agreed: (1) Business Loan Application Portal MVP launch,
(2) Mobile Instant Transfer (SPEC-mobile-instant-transfer) expansion to
include recipient web-claim links, (3) continued hardening of card controls
step-up flow.

Decisions
- Business Loan Application Portal MVP targeted for end of Q1 2026,
  contingent on ACH Batch Processor capacity fix landing first.
- Instant Transfer web-claim link feature moved from "under discussion" to
  committed Q1 scope.

Action Items
1. Payments Platform: confirm ACH capacity fix completion date to unblock
   Loan Portal launch planning.
2. Product: finalize Instant Transfer web-claim link requirements by end of
   January.
3. Design: begin Loan Portal underwriting queue UI review in February.""")

add("meeting_notes", "MN-2026-03-security-review-sync.pdf",
    "MN-2026-03-003", "Meeting Notes: Security Review Sync - Payments Idempotency",
    "meeting_notes", "security", "internal", "2026-03-05",
    body="""Attendees
Security, Payments Platform Engineering, Engineering Leadership.

Agenda
1. Follow-up on INC-2026-02-27-004 (duplicate wire transfers) action items.
2. Broader idempotency audit findings.
3. Sign-off requirements for the idempotency key rollout.

Discussion
Payments Platform presented the design for idempotency key enforcement on
the Wire Transfer Service, targeting completion by 2026-03-20 per the
incident action item. Security reviewed the design and requested that the
idempotency key itself be a client-generated UUID rather than a
server-generated sequence, to avoid predictability.

The broader audit (action item 2 from INC-2026-02-27-004) found that the
ACH Batch Processor already has natural idempotency via its batch-file
submission model, but the mobile app's Instant Transfer feature
(SPEC-mobile-instant-transfer) does not currently enforce idempotency keys
on its transfer initiation endpoint. This was flagged as a new, separate
follow-up item, not blocking the wire transfer fix.

Decisions
- Wire Transfer Service idempotency key rollout approved as designed,
  client-generated UUID.
- Instant Transfer idempotency gap added to Payments Platform's Q2 backlog
  as a medium-priority item (no known incident yet, proactive fix).

Action Items
1. Payments Platform: ship WTS idempotency enforcement by 2026-03-20 as
   committed in INC-2026-02-27-004.
2. Payments Platform: scope Instant Transfer idempotency fix for Q2
   backlog.
3. Security: add idempotency key coverage as a standing check in the
   quarterly payments security review going forward.""")

add("meeting_notes", "MN-2026-06-incident-postmortem-followup.pdf",
    "MN-2026-06-004", "Meeting Notes: H1 2026 Incident Postmortem Follow-Up",
    "meeting_notes", "engineering", "internal", "2026-06-25",
    body="""Attendees
Engineering Leadership, SRE, Payments Platform, Identity Platform, Security.

Agenda
1. Review status of all H1 2026 incident action items.
2. Identify recurring root-cause patterns across the last 12 months.
3. Agree H2 2026 reliability investment areas.

Discussion
The group reviewed all incidents from the last 12 months
(INC-2025-08-14-001 through INC-2026-07-08-006, noting the July incident
was still fresh at time of this meeting and added for completeness). Three
recurring root-cause patterns were identified across the payments-related
incidents specifically:

1. Capacity/resource-limit exhaustion under real-world peak load
   (INC-2025-08-14-001, INC-2025-10-02-002 indirectly via replication load,
   INC-2025-12-19-003).
2. Configuration drift silently undoing prior incident remediations
   (INC-2026-05-11-005 directly repeating INC-2025-08-14-001's root
   cause).
3. Missing idempotency protection on payment-initiating endpoints
   (INC-2026-02-27-004, and the related proactive fix opened for Instant
   Transfer in the March security review).

The non-payments incident (INC-2026-07-08-006, mobile login outage) was
noted as a different pattern entirely: silent automation failure with
insufficient alerting, which the group agreed is also worth tracking as its
own systemic theme across all automated renewal/rotation jobs, not just
certificates.

Decisions
- H2 2026 investment area #1: config-drift detection tooling (already
  underway per May action items) to be expanded platform-wide, not just
  payments.
- H2 2026 investment area #2: standardize idempotency key support as a
  required pattern for all new payment-initiating endpoints, enforced via
  API design review checklist.
- H2 2026 investment area #3: audit all automated renewal/rotation jobs
  (certificates, credentials, keys) for silent-failure alerting gaps,
  prompted by INC-2026-07-08-006.

Action Items
1. SRE: expand config-drift detection beyond payments platform, target Q3.
2. Engineering Leadership: add idempotency requirement to API design review
   checklist.
3. Security: lead the automated renewal/rotation job alerting audit,
   report findings in Q3 postmortem follow-up.""")


def render_pdf(doc):
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(0, 8, doc["title"])
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 5, BANK + " - Internal Document")
    pdf.ln(2)

    # Metadata box
    pdf.set_draw_color(180, 180, 180)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(0, 0, 0)
    meta_lines = [
        ("doc_id", doc["doc_id"]),
        ("document_type", doc["document_type"]),
        ("department", doc["department"]),
        ("access_level", doc["access_level"]),
        ("created_date", doc["created_date"]),
    ]
    for k, v in doc["extra"].items():
        meta_lines.append((k, str(v)))

    y_start = pdf.get_y()
    pdf.set_font("Helvetica", "", 9)
    for k, v in meta_lines:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(40, 5, k + ":")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, str(v), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_draw_color(160, 160, 160)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(20, 20, 20)
    for para in doc["body"].split("\n\n"):
        lines = para.split("\n")
        first = lines[0]
        is_heading = (
            len(first) < 60
            and not first[:1].isdigit()
            and not first.startswith("-")
            and len(lines) > 1
        )
        pdf.set_x(pdf.l_margin)
        if is_heading:
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(pdf.epw, 6, first)
            pdf.set_font("Helvetica", "", 10.5)
            rest = "\n".join(lines[1:])
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5.5, rest)
        else:
            pdf.multi_cell(pdf.epw, 5.5, para)
        pdf.ln(2)

    out_dir = os.path.join(BASE, doc["category"])
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, doc["filename"])
    pdf.output(out_path)
    return out_path


if __name__ == "__main__":
    manifest = []
    for d in DOCS:
        path = render_pdf(d)
        rel = os.path.relpath(path, BASE).replace("\\", "/")
        manifest.append({
            "doc_id": d["doc_id"],
            "title": d["title"],
            "document_type": d["document_type"],
            "department": d["department"],
            "access_level": d["access_level"],
            "created_date": d["created_date"],
            "path": "docs/" + rel,
            **d["extra"],
        })
        print("wrote", rel)

    import json
    with open(os.path.join(BASE, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("wrote manifest.json with", len(manifest), "entries")
