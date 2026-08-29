# HealthLink Ethiopia — Architecture Realism Audit

**Date:** August 29, 2026
**Auditor:** ContextForge Architecture Review
**Status:** AUDIT COMPLETE

---

## Executive Summary

The HealthLink architecture is **substantially correct** for a healthcare platform. The technology choices are appropriate, the data model covers the key entities, and the security design is sound. However, there are **3 critical issues**, **5 high-severity issues**, and **4 medium-severity issues** that must be resolved before the context is handed to a coding agent.

**Verdict: NOT READY — FIX REQUIRED (3 critical issues)**

---

## 1. Architecture Contradictions

### 1.1 CRITICAL — Monolith vs. Services Inconsistency

**Problem:** The architecture prompt now says "be consistent: either use a monolith OR define services, not both." But HealthLink genuinely needs:
- A main web/API backend
- A background worker for appointment reminders
- An AI guidance service (optional — could be a module)

**Why it matters:** If the architecture says "modular monolith" but defines a "background worker" as a separate service, a coding agent will be confused about deployment topology.

**Recommended fix:** Use "small service-based architecture" with 2-3 deployable units:
1. **Web/API service** — Express + Prisma (handles all HTTP requests)
2. **Worker service** — Same codebase, different entrypoint (handles cron jobs, reminders)
3. Both share the same Docker image, started with different commands.

**Affects user-selected technologies:** No.

### 1.2 CRITICAL — node-cron vs. Horizontal Fargate Scaling

**Problem:** If the architecture uses `node-cron` inside a Fargate container, and Fargate runs 2+ replicas for availability, **every replica fires the cron job independently**. This produces duplicate SMS reminders for every patient.

**Why it matters:** A patient receives 2, 3, or N identical reminders. This is a production bug that destroys user trust.

**Severity:** CRITICAL — this is not a theoretical concern. It happens on the first scaling event.

**Recommended fix — smallest change:**
Use a **database-based job claiming** pattern:
```sql
-- ReminderJob table
CREATE TABLE reminder_jobs (
  id UUID PRIMARY KEY,
  appointment_id UUID NOT NULL,
  type VARCHAR(20) NOT NULL,  -- '24h' or '1h'
  scheduled_at TIMESTAMP NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',  -- pending/claimed/sent/failed
  claimed_by VARCHAR(100),  -- container hostname
  claimed_at TIMESTAMP,
  sent_at TIMESTAMP
);
```

The worker does:
```sql
BEGIN;
SELECT * FROM reminder_jobs
WHERE status = 'pending' AND scheduled_at <= NOW()
FOR UPDATE SKIP LOCKED
LIMIT 1;
-- If found, mark as 'claimed', send SMS, mark as 'sent'
COMMIT;
```

`FOR UPDATE SKIP LOCKED` ensures only one replica claims each job.

**Alternative (simpler, for MVP):** Run exactly 1 Fargate task. Accept that it doesn't scale. Document this as a known limitation. Scale later by adding the job-claiming pattern.

**Affects user-selected technologies:** No.

### 1.3 HIGH — Single Backend for Web + Mobile

**Problem:** Not actually a problem. React web and React Native mobile both consume the same Express REST API. This is correct architecture.

**Status:** No fix needed.

### 1.4 HIGH — Deployment Description Ambiguity

**Problem:** The architecture may say "Docker on AWS" without specifying:
- Fargate vs. ECS vs. EC2
- Single task vs. multiple tasks
- How the worker runs

**Recommended fix:** The architecture deployment section must explicitly state:
- "2 Fargate services sharing the same Docker image: api (port 3000) and worker (no port)"
- Or: "1 Fargate task with supervisor process managing both API and worker"

---

## 2. Scalability & Concurrency Issues

### 2.1 CRITICAL — Double-Booking Race Condition

**Problem:** Two patients booking the same time slot simultaneously:
```
Time T1: Patient A queries slot → available
Time T1: Patient B queries slot → available
Time T2: Patient A books → success
Time T2: Patient B books → success (BUG: slot double-booked)
```

**Why it matters:** A doctor sees two patients for the same slot. This is a clinical safety issue.

**Recommended fix:** The TimeSlot entity must have a **database-level unique constraint**:
```sql
ALTER TABLE time_slots
ADD CONSTRAINT uq_doctor_slot
UNIQUE (doctor_clinic_id, date, start_time);
```

And the booking logic must use a **transaction with row-level locking**:
```sql
BEGIN;
SELECT * FROM time_slots
WHERE id = $slot_id AND is_booked = false
FOR UPDATE;
-- If found, update is_booked = true
-- If not found, rollback (slot was taken)
COMMIT;
```

**Affects user-selected technologies:** No.

### 2.2 HIGH — Payment Webhook Idempotency

**Problem:** Telebirr may deliver the same webhook multiple times (network retry, load balancer retry). If the payment handler is not idempotent, a single payment creates duplicate payment records.

**Recommended fix:**
```sql
-- Payment table must have a unique constraint on provider reference
ALTER TABLE payments
ADD CONSTRAINT uq_payment_provider_ref
UNIQUE (provider, provider_reference);
```

And the handler must:
```sql
INSERT INTO payments (..., provider_reference, status)
VALUES (..., $ref, 'completed')
ON CONFLICT (provider, provider_reference) DO NOTHING;
```

**Affects user-selected technologies:** No.

### 2.3 HIGH — Payment Timeout Handling

**Problem:** What if the patient initiates payment, the Telebirr app opens, but the patient closes it without paying? The time slot remains "held" indefinitely.

**Recommended fix:** Add a TTL to held slots:
- When payment is initiated, record `payment_started_at`
- A background job releases slots where `payment_started_at` is older than 15 minutes and status is still 'pending_payment'
- The patient is notified that the booking expired

**Affects user-selected technologies:** No.

### 2.4 MEDIUM — SMS Delivery Failure Handling

**Problem:** Africa's Talking may fail to deliver an SMS (invalid number, network issue, rate limit). The reminder system must:
1. Track delivery status
2. Retry with backoff (max 3 retries)
3. Log failures for manual follow-up
4. Not mark the reminder as "sent" until confirmed

**Recommended fix:** Add `delivery_status` and `retry_count` to ReminderLog.

---

## 3. Data Model Correctness

### 3.1 CRITICAL — TimeSlot Uniqueness

Already covered in 2.1. The data model MUST include:
```sql
UNIQUE (doctor_clinic_id, date, start_time)
```

Without this, the application layer cannot reliably prevent double-booking.

### 3.2 HIGH — Appointment Status State Machine

The Appointment entity needs explicit status transitions:
```
PENDING_PAYMENT → CONFIRMED (on payment success)
PENDING_PAYMENT → CANCELLED (on payment timeout/failure)
CONFIRMED → CANCELLED (patient cancels, with policy)
CONFIRMED → COMPLETED (after appointment time)
CONFIRMED → NO_SHOW (after appointment time, patient didn't show)
```

Each transition must be validated. You cannot go from COMPLETED back to PENDING_PAYMENT.

### 3.3 HIGH — OTP Security

The OtpRecord must include:
- `code_hash` (bcrypt or SHA-256, NOT plaintext)
- `expires_at` (5-10 minute TTL)
- `attempts` (max 3-5)
- `used` (boolean, prevent reuse)
- `created_at` (for audit)

The application must:
- Reject OTP after expiry
- Reject OTP after max attempts
- Mark OTP as used after successful verification
- Rate-limit OTP generation (max 3 per phone per 10 minutes)

### 3.4 MEDIUM — Audit Log Completeness

AuditLog should capture:
- Authentication events (login, logout, failed login)
- Appointment events (booked, cancelled, completed)
- Payment events (initiated, succeeded, failed)
- Data access (patient records viewed by doctor)
- Admin actions (user management, configuration changes)

---

## 4. Authentication & Security

### 4.1 HIGH — Refresh Token Design

The context must specify:
- Access token TTL: 15-30 minutes
- Refresh token TTL: 7 days
- Refresh token rotation: each use issues a new refresh token
- Refresh token revocation: logout invalidates all refresh tokens for that user
- Storage: refresh tokens stored as hashed values in the database

### 4.2 HIGH — Resource Ownership

Every data access query must verify ownership:
- Patients can only view their own appointments
- Doctors can only view appointments at their clinics
- Admins can view all data but actions are audit-logged

This should be enforced at the API layer, not just the database layer.

### 4.3 MEDIUM — Rate Limiting

Critical endpoints must have rate limits:
- OTP generation: 3 per phone per 10 minutes
- Login: 5 per phone per 15 minutes
- Payment initiation: 10 per user per hour
- AI health guidance: 20 per user per day

### 4.4 MEDIUM — Secrets Management

The architecture must specify that ALL secrets go to AWS Secrets Manager:
- Database connection string
- Telebirr API credentials
- Africa's Talking API key
- Amazon Bedrock API key/role
- JWT signing key
- OTP signing key

**Never** hardcode secrets in environment variables or code.

---

## 5. Appointment/Payment Lifecycle

### 5.1 Complete Lifecycle (must be in the context)

```
1. Patient selects: Doctor + Clinic + Date + Time Slot
2. System checks slot availability (SELECT ... FOR UPDATE)
3. System marks slot as 'held' (soft lock, 15-min TTL)
4. System creates Appointment with status PENDING_PAYMENT
5. System creates Payment record with status INITIATED
6. System calls Telebirr API to initiate payment
7. Patient completes payment in Telebirr app
8. Telebirr sends webhook to our endpoint
9. System verifies webhook signature
10. System checks idempotency (provider_reference)
11. System updates Payment status to COMPLETED
12. System updates Appointment status to CONFIRMED
13. System schedules reminders (24h + 1h before)
14. System sends confirmation SMS via Africa's Talking
```

### 5.2 Failure Paths (must be in the context)

```
Payment timeout (15 min):
  → Release time slot
  → Update Appointment to CANCELLED
  → Notify patient via SMS

Payment webhook failure:
  → Log error
  → Retry webhook processing (idempotent)
  → Alert admin if retries exhausted

Duplicate webhook:
  → Idempotent handler rejects duplicate
  → No duplicate payment record
```

---

## 6. External Integration Assumptions

### 6.1 Telebirr (MUST VERIFY)

| Assumption | Status | Risk |
|-----------|--------|------|
| Payment initiation API exists | Likely correct | Low — Telebirr is a real payment provider |
| Callback/webhook URL supported | Must verify | HIGH — some providers only support polling |
| Signature verification available | Must verify | HIGH — without this, webhook is insecure |
| Transaction reference format | Must verify | MEDIUM |
| Test/sandbox environment available | Must verify | HIGH — cannot test without sandbox |
| Currency is ETB | Likely correct | Low |
| Payment timeout behavior | Must verify | MEDIUM |

**The context must NOT invent undocumented Telebirr APIs.** It should say:
> "Telebirr integration details must be verified against official Telebirr developer documentation before implementation."

### 6.2 Africa's Talking (MUST VERIFY)

| Assumption | Status | Risk |
|-----------|--------|------|
| OTP SMS API exists | Correct — AT has SMS API | Low |
| Ethiopia supported | Must verify | HIGH |
| Test mode available | Correct — AT has sandbox | Low |
| Delivery status callback | Must verify | MEDIUM |
| Rate limits | Must verify | MEDIUM |
| Per-message cost | Must verify | LOW |

### 6.3 Amazon Bedrock (MUST VERIFY)

| Assumption | Status | Risk |
|-----------|--------|------|
| Bedrock API available in AWS | Correct | Low |
| Which model? (Claude? Titan?) | Must specify | HIGH — different models have different capabilities |
| IAM role auth | Correct for Fargate | Low |
| Prompt structure | Must design | HIGH — health guidance prompts need careful design |
| Medical disclaimer required | CRITICAL | Must include "not medical advice" |
| Patient data privacy | CRITICAL | Must not store health queries in plaintext |
| Cost per token | Must estimate | MEDIUM |

**The context must include:**
> "The AI health guidance feature MUST include a prominent disclaimer that this is general health information and NOT a substitute for professional medical advice. Emergency situations must always direct users to call emergency services."

---

## 7. AWS Deployment Realism

### 7.1 Components (all needed)

| Component | Purpose | Complexity |
|-----------|---------|------------|
| VPC | Network isolation | Required |
| Public subnets | ALB | Required |
| Private subnets | Fargate, RDS | Required |
| ALB | Load balancing, SSL | Required |
| Fargate | Container hosting | Required |
| RDS PostgreSQL | Database | Required |
| ECR | Docker image registry | Required |
| Secrets Manager | API keys, DB credentials | Required |
| CloudWatch | Logs, metrics | Required |
| S3 | File storage (clinic images, documents) | Required |
| Route 53 | DNS management | Optional for MVP |
| ACM | SSL certificate | Required (free with ALB) |
| SNS | Email/SMS notifications | Optional — can use AT |
| KMS | Encryption at rest | Optional — RDS has built-in encryption |

### 7.2 Potential Issues

1. **Fargate autoscaling**: Need to define min/max task count. For MVP: min=1, max=3.
2. **RDS backups**: Automated backup retention should be 7+ days.
3. **ALB health checks**: Must hit a `/health` endpoint, not just port 3000.
4. **Security groups**: Fargate → RDS must be restricted to port 5432 only.
5. **Cost estimation**: Fargate + RDS + ALB ≈ $50-100/month for MVP traffic.

---

## 8. CI/CD Realism

### 8.1 Pipeline

```
GitHub push → GitHub Actions → Build Docker → Push to ECR
→ Run Prisma migration → Deploy to Fargate
```

### 8.2 Issues

1. **Prisma migration safety**: `prisma migrate deploy` is safe (applies pending migrations only). But must NOT run `prisma db push` in production.
2. **Rollback**: If new deployment fails, roll back Fargate to previous task definition.
3. **Staging vs production**: Must NOT share database, secrets, or Fargate cluster.
4. **Database migration timing**: Migrations must be backward-compatible if zero-downtime deployment is required.

---

## 9. MVP Complexity Assessment

| Component | Classification | Reason |
|-----------|---------------|--------|
| React web app | REQUIRED | User-selected |
| React Native mobile | REQUIRED | User-selected |
| Node.js + Express | REQUIRED | User-selected |
| PostgreSQL + Prisma | REQUIRED | User-selected |
| Telebirr | REQUIRED | User-selected |
| Africa's Talking | REQUIRED | User-selected |
| Amazon Bedrock | REQUIRED | User-selected |
| Docker | REQUIRED | User-selected |
| AWS Fargate | REQUIRED | User-selected |
| ALB | REQUIRED | Needed for SSL + load balancing |
| RDS | REQUIRED | Managed PostgreSQL |
| ECR | REQUIRED | Docker image storage |
| Secrets Manager | REQUIRED | Security best practice |
| CloudWatch | REQUIRED | Basic observability |
| S3 | REQUIRED | File storage |
| Route 53 | OPTIONAL | Can use ALB DNS for MVP |
| ACM | REQUIRED | SSL certificates (free) |
| SNS | OPTIONAL | Can use Africa's Talking for notifications |
| KMS | OPTIONAL | RDS encryption is built-in |
| CI/CD pipeline | REQUIRED | Basic GitHub Actions |
| Redis caching | OPTIONAL | Not needed for MVP |
| Rate limiting | REQUIRED | Security |
| Audit logging | REQUIRED | Healthcare compliance |

**Verdict:** The architecture is appropriately complex for the requirements. No overengineering detected.

---

## 10. Final Verdict

### CRITICAL Issues (must fix before coding)

1. **node-cron + Fargate = duplicate reminders** — Use database job claiming or single-replica constraint
2. **Double-booking race condition** — Add UNIQUE constraint + SELECT FOR UPDATE
3. **TimeSlot must have transaction-level locking** — Without this, concurrent bookings corrupt data

### HIGH Issues (should fix before coding)

4. **Payment webhook idempotency** — Unique constraint on provider_reference
5. **Payment timeout handling** — TTL-based slot release
6. **Refresh token design** — Rotation + revocation
7. **Resource ownership enforcement** — Per-query ownership check
8. **Appointment status state machine** — Explicit transitions

### MEDIUM Issues (fix during implementation)

9. **SMS delivery failure handling** — Retry with backoff
10. **Rate limiting** — OTP, login, payment endpoints
11. **Audit log completeness** — All sensitive operations
12. **Secrets management** — All secrets in Secrets Manager

### Integration Assumptions (must verify)

13. Telebirr webhook support and signature verification
14. Africa's Talking Ethiopia support and sandbox
15. Amazon Bedrock model selection
16. AI health guidance disclaimer requirement

---

## Recommended Context Changes

The generated context should include these explicit sections:

### A. Concurrency Safety Rules (agent_rules)
```
- Appointment booking MUST use database-level locking (SELECT FOR UPDATE)
- TimeSlot MUST have UNIQUE constraint on (doctor_clinic_id, date, start_time)
- Payment webhooks MUST be idempotent (unique provider_reference)
- Reminder jobs MUST use database-based claiming (FOR UPDATE SKIP LOCKED)
```

### B. Reminder Architecture (architecture section)
```
Background worker runs as a separate Fargate task (same Docker image).
Uses database-based job claiming to prevent duplicate processing.
NOT node-cron in-process (incompatible with multiple replicas).
```

### C. Payment State Machine (architecture section)
```
Appointment statuses: PENDING_PAYMENT → CONFIRMED → COMPLETED/CANCELLED/NO_SHOW
Payment statuses: INITIATED → PENDING → COMPLETED/FAILED/REFUNDED
Time slot soft-lock TTL: 15 minutes
```

### D. Security Essentials (security section)
```
OTP: SHA-256 hash, 5-min expiry, max 3 attempts, rate-limited
JWT: 15-min access, 7-day refresh with rotation
RBAC: patient, doctor, admin roles
All health data encrypted at rest and in transit
AI disclaimer: "Not medical advice. Call emergency services for emergencies."
```

---

*This audit ensures the generated HealthLink context is realistic, implementable, and safe for a coding agent to use as an engineering specification.*
