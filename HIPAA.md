# HIPAA Compliance Documentation

SOAPFlow is designed with HIPAA awareness for use in healthcare AI research and development.
This document outlines the technical safeguards and compliance considerations.

> **Disclaimer:** This is a portfolio/research project. Before deploying in a real clinical
> environment, a full HIPAA risk assessment and BAA with all vendors is required.

---

## Protected Health Information (PHI) Handling

### What is PHI?
HIPAA defines 18 identifiers as PHI when combined with health information:
names, dates, geographic data, phone numbers, SSNs, medical record numbers, and more.

### De-identification Pipeline
SOAPFlow implements **Safe Harbor de-identification** (45 CFR §164.514(b)):

```
Raw Transcript → Presidio Analyzer → PHI Detection → Anonymizer → Clean Transcript
                                         ↓
                                   AuditLog (counts only — no PHI content)
```

**Entities detected and redacted:** PERSON, DATE_TIME, PHONE_NUMBER,
EMAIL_ADDRESS, LOCATION, US_SSN, MEDICAL_LICENSE, CREDIT_CARD

**Implementation:** `backend/app/services/deidentify.py`

---

## Technical Safeguards

| Safeguard | Implementation |
|---|---|
| Encryption in transit | TLS 1.2+ (enforced by reverse proxy) |
| Encryption at rest | SQLite WAL encryption (configure in production) |
| Access control | JWT + RBAC (admin/doctor/nurse roles) |
| Audit trail | `AuditLog` table — who accessed what, when (no PHI) |
| PHI-safe logging | structlog JSON — request metadata only, never body content |
| Minimum necessary | Role-scoped history queries (user sees only their notes) |
| Session management | JWT access token (60min) + refresh token (7 days) |

---

## AI Provider Compliance

| Provider | HIPAA BAA Available | Status |
|---|---|---|
| OpenAI API | No (standard API) | **Requires de-ID before sending** |
| Azure OpenAI | Yes (with enterprise agreement) | Compliant path |
| Anthropic Claude | No (standard API) | **Requires de-ID before sending** |
| Amazon Bedrock (Claude) | Yes | Compliant path |

**SOAPFlow's approach:** Presidio de-identification runs *before* any transcript
is sent to OpenAI or Anthropic APIs, making the standard API paths safer.

---

## Audit Log Schema

```sql
CREATE TABLE audit_logs (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER,           -- who
    action      VARCHAR(100),      -- what (e.g. "post.api.v1.generate")
    resource_id INTEGER,           -- which note (ID only, not content)
    ip_address  VARCHAR(45),       -- where
    created_at  DATETIME,          -- when
    duration_ms FLOAT              -- how long
    -- NO PHI CONTENT IS EVER STORED IN THIS TABLE
);
```

---

## Dataset Compliance

| Dataset | PHI Status | License |
|---|---|---|
| Synthetic (built-in) | No real PHI | MIT |
| MedDialog (HuggingFace) | De-identified research dataset | CC BY 4.0 |
| MTSamples (Kaggle) | De-identified clinical notes | Public domain |

---

## Regulatory References

- **HIPAA Security Rule:** 45 CFR Part 164, Subpart C
- **HIPAA Safe Harbor:** 45 CFR §164.514(b)
- **ONC HTI-1 Rule (2025):** Algorithm transparency for EHR-integrated AI
- **21st Century Cures Act:** Interoperability and information blocking provisions

---

## Production Checklist

Before deploying in a real clinical environment:

- [ ] Sign BAA with all cloud vendors (Azure OpenAI or Amazon Bedrock)
- [ ] Enable AES-256 encryption at rest for database
- [ ] Configure TLS termination at load balancer
- [ ] Implement database backup and retention policies
- [ ] Conduct formal HIPAA risk assessment (45 CFR §164.308(a)(1))
- [ ] Train all staff on HIPAA policies
- [ ] Establish incident response plan (Breach Notification Rule)
- [ ] Review FDA SaMD classification if AI influences clinical decisions
