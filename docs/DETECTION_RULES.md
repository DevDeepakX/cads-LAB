# Detection Rules

Rules are `DetectionRule` data objects evaluated by `DetectionEngine`; service code does not contain a growing event conditional chain.

| Rule | Trigger | Severity |
| --- | --- | --- |
| `S3-PUBLIC-ACCESS` | S3 bucket has `public_access=true` during a related event | HIGH |
| `S3-SENSITIVE-OBJECT` | A classified sensitive object is retrieved from a public bucket | HIGH |
| `IAM-PRIVILEGE-ESCALATION` | Unauthorized attachment of AdministratorAccess or excessive wildcard policies | CRITICAL |
| `IAM-EXCESSIVE-PERMISSIONS` | IAM role inspection exposes broad wildcard permissions | HIGH |
| `EC2-OPEN-SSH` | Security group permits TCP/22 ingress from `0.0.0.0/0` | HIGH |
| `CLOUDTRAIL-SUSPICIOUS-ACTIVITY` | Detection of suspicious API events from untrusted sources or compromised keys | HIGH |

Each detection creates or updates a session-scoped finding with affected resource, evidence, explanation, and recommendation. Findings begin as `OPEN`, can become `INVESTIGATING`, and become `RESOLVED` only after the simulator state is remediated and re-evaluated.

- **LAB-001 (S3):** uses `S3-PUBLIC-ACCESS`. Remediated via `PutPublicAccessBlock` or defense engine.
- **LAB-002 (IAM):** uses `IAM-PRIVILEGE-ESCALATION`. Remediated via `DetachUserPolicy` or least-privilege policy attachment.
- **LAB-003 (EC2/SG):** uses `EC2-OPEN-SSH`. Remediated via `RevokeSecurityGroupIngress` removing `0.0.0.0/0:22`.
- **LAB-004 (CloudTrail):** uses `CLOUDTRAIL-SUSPICIOUS-ACTIVITY`. Remediated via `DeleteAccessKey` or compromised identity revocation.