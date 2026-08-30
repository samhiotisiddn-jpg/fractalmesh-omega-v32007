# FractalMesh Omega Security Policy — NSW / Australia Baseline

**Version:** 1.0  
**Jurisdiction:** New South Wales, Australia  
**Applies to:** `safe-mas-core` branch of `fractalmesh-omega-v32007`  
**Owner:** Sam Hiotis | IronVision Nexus  
**Status:** Draft — requires legal review before operational use

> ⚠️ **Disclaimer:** This document is a developer-facing security policy template. It does not constitute legal advice and has no force of law until reviewed and adopted by the entity's responsible officers. Patent, trademark, domain, and licensing decisions require qualified Australian legal practitioners.

---

## 1. Scope

This policy governs the local-first multi-agent swarm architecture implemented in the `safe-mas-core` branch. It covers:

- The `safe_memory` tiered memory subsystem.
- The `safe_orchestrator` Model Context Protocol (MCP) tool registry and policy gateway.
- The `safe_router` model-routing subsystem.
- All local compute nodes, edge devices, and cloud endpoints that interact with the swarm.
- Human operators, agent principals, and automated monitoring processes.

This policy does **not** authorise autonomous financial transactions, surveillance of individuals, credential harvesting, dark-web sourcing, or unilateral agent action outside the explicit approval flows defined below.

---

## 2. Governance Principles

| Principle | Requirement |
|---|---|
| Human-in-the-loop | Any action that spends funds, modifies external systems, or affects personal data requires explicit operator approval. |
| Least privilege | Each agent receives only the tool permissions mapped to its operational scope. |
| Local-first | Sensitive memory, credentials, and signing keys remain on operator-controlled hardware unless encrypted in transit to an approved endpoint. |
| Transparency | Tool decisions, policy denials, and memory writes are logged for audit. |
| Defence in depth | No single component bypass; policy gateway, RBAC, and kill-switches operate independently. |

---

## 3. Legal and Regulatory Baseline

### 3.1 Australian Privacy Principles (APPs)

The system must minimise collection of personal information (APP 3), protect it from misuse and unauthorised access (APP 11), and allow correction or deletion on request (APP 13). Operational data classified as personal information under the *Privacy Act 1988* (Cth) must be:

- Stored with encryption at rest (AES-256 or equivalent).
- Transmitted only over TLS 1.3 or equivalent secure channels.
- Redacted before being sent to external model providers unless the user explicitly opts in.

### 3.2 New South Wales State Records Act 1998

Where the swarm generates records that are "State records" for NSW public-sector deployments, retention and disposal must follow an approved retention and disposal authority issued by State Records NSW.

### 3.3 Essential Eight and ACSC Guidance

Align with the Australian Cyber Security Centre (ACSC) Essential Eight maturity model, at minimum aiming for **Maturity Level Two** for:

- Application control
- Patch applications and operating systems
- Configure Microsoft Office macro settings (where applicable)
- User application hardening
- Restrict administrative privileges
- Patch operating systems
- Multi-factor authentication for operator accounts
- Regular backups

### 3.4 ISO/IEC 27001:2022 Mapping (Informative)

| Policy Section | Relevant ISO 27001 Controls |
|---|---|
| 4. Access Control | A.5.15, A.5.18, A.8.2, A.8.5 |
| 5. Cryptography | A.8.24 |
| 6. Secrets Management | A.5.23, A.8.5 |
| 7. Logging and Monitoring | A.8.15, A.8.16 |
| 8. Incident Response | A.5.24, A.5.25, A.5.26, A.8.15 |
| 9. Third-Party Suppliers | A.5.19, A.5.20, A.5.21 |

---

## 4. Secret Handling

### 4.1 Prohibited Practices

- API keys, passwords, Hive posting keys, wallet seed phrases, and service-account credentials must never be:
  - Written to `safe_memory` logs or memory tiers.
  - Returned in agent-generated outputs.
  - Hard-coded in source code.
  - Stored in plain text on disk.

### 4.2 Approved Storage

| Secret Type | Storage |
|---|---|
| LLM provider API keys | OS keyring (`keyring`), encrypted env var, or approved secret manager |
| Hive posting keys | OS keyring only; loaded into volatile memory for local signing |
| Database credentials | Environment variables or secret manager; rotated every 90 days |
| TLS certificates | Hardware-backed store or encrypted file system |

### 4.3 Memory Redaction

Before any content is written to `safe_memory` or transmitted to an external provider, it must pass `safe_router.scrub` to remove:

- API keys and bearer tokens (regex + entropy heuristics).
- Australian telephone numbers.
- Email addresses.
- Tax file numbers, Medicare numbers, and driver licence patterns.
- Credit card and bank account numbers.

---

## 5. Role-Based Access Control (RBAC)

### 5.1 Roles

| Role | Permissions |
|---|---|
| `operator` | Full read/write, can approve high-risk actions, can rotate secrets. |
| `agent_executor` | Can invoke allow-listed tools within an approved session. |
| `agent_observer` | Can read telemetry and query `safe_memory`; cannot invoke tools. |
| `auditor` | Read-only access to logs, policy decisions, and memory metadata. |

### 5.2 Permission Model

- Every tool is registered with a required capability vector, e.g. `["memory:read", "network:external"]`.
- Every agent identity is issued a capability vector by the GOA-equivalent policy gateway.
- Invocation is permitted only if the agent's capabilities are a superset of the tool's required capabilities.
- High-risk tools additionally require an operator `approval_token`.

---

## 6. MCP Tool Registry Security

### 6.1 Manifest Validation

All tools must supply a signed manifest containing:

```json
{
  "name": "string",
  "version": "semver",
  "authority": "trusted-identity-fingerprint",
  "capabilities": ["capability:scope"],
  "risk_class": "low|medium|high|critical",
  "description": "plain text, max 500 chars"
}
```

The gateway rejects manifests that:

- Originate from unrecognised authorities.
- Contain HTML, JavaScript, or markdown injection attempts.
- Declare overly broad capabilities.
- Shadow an already-registered tool name.

### 6.2 Tool Description Poisoning and Shadowing (MCP-10 / MCP-13 Mitigations)

- Compare new manifest names and descriptions against existing tools; raise `SHADOW_DETECTED` on collision.
- Strip control characters and limit description length before registration.
- Require authority attestation for any tool that can invoke external network calls.

---

## 7. Model Routing and Data Sovereignty

### 7.1 Dual-Path Architecture

| Data Sensitivity | Routing |
|---|---|
| Public / non-personal | Cloud provider with acceptable DPA and region |
| Internal / operational | Australian-region cloud or private VPC |
| Personal / sensitive | Local runtime only (`llama.cpp`, local TEE, or edge device) |
| Secrets / credentials | Blocked from all model providers |

### 7.2 Metadata Scrubbing

Before a request leaves the operator environment:

1. Identify metadata: origin IP, hostnames, usernames, file paths.
2. Redact or generalise metadata (e.g. replace `/home/alice/...` with `<USER_HOME>`).
3. Re-run Presidio-style PII detection with `min_score >= 0.5`.
4. Log scrubbing action in the audit trail.

### 7.3 Fallback Policy

If cloud connectivity fails, compliance confidence is below threshold, or the operator toggles `SOVEREIGN_MODE`, the router must:

- Reject the external request.
- Queue the task for local execution.
- Notify the operator if no local model is available.

---

## 8. Logging, Monitoring, and Kill-Switch

### 8.1 Audit Events

Log every:

- Tool registration and deregistration.
- Policy gateway allow / deny decision.
- Memory write to `long_term_explicit`.
- External model request (provider, model, bytes out / bytes in, not content unless debug-approved).
- Operator approval of high-risk actions.
- Secret rotation.

### 8.2 Kill-Switch

A circuit breaker triggers an automatic 10-minute cooldown when:

- Three tool invocations are denied within 10 minutes, OR
- A critical-risk tool is invoked without approval, OR
- An anomaly detector flags prompt-injection or data-exfiltration patterns.

During cooldown, all agent-initiated external actions are paused. Operator actions remain available.

---

## 9. Incident Response

### 9.1 Severity Levels

| Level | Examples |
|---|---|
| P1 Critical | Credential exfiltration, unauthorised transaction, system takeover attempt |
| P2 High | Repeated policy violations, malformed tool manifest from trusted source |
| P3 Medium | Scrubbing bypass, model provider outage |
| P4 Low | Cosmetic log issues, false-positive policy denials |

### 9.2 Notification

- P1–P2: Notify operator immediately via configured channel.
- P1: Rotate affected secrets and suspend agent identity pending investigation.
- P3–P4: Log and batch for daily review.

---

## 10. Versioning and Review

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-30 | Safe-MAS-Core | Initial NSW baseline |

Review cycle: every 6 months or after any security incident.
