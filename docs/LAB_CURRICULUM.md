# CADS Lab Curriculum

CADS (Cloud Attack-Defense Simulation) delivers structured, hands-on cloud security labs designed around real-world misconfigurations, detection engineering, and remediation workflows.

Every lab adheres to the canonical learning lifecycle:
```
LEARN → DISCOVER → ENUMERATE → IDENTIFY MISCONFIGURATION → SIMULATE ATTACK/INVESTIGATION → DETECT → INVESTIGATE → REMEDIATE → VERIFY → COMPLETE → UPDATE PROGRESS
```

---

## Lab Index

| Lab ID | Lab Title | Cloud Service | Category | Difficulty | Estimated Time |
| --- | --- | --- | --- | --- | --- |
| **LAB-001** | Public S3 Bucket Discovery & Hardening | Amazon S3 | Storage Security | Beginner | 15 mins |
| **LAB-002** | Excessive IAM Permissions & Privilege Escalation | AWS IAM | IAM Security | Intermediate | 20 mins |
| **LAB-003** | Insecure Security Group Remediation | Amazon EC2 / VPC | Network Security | Beginner | 15 mins |
| **LAB-004** | CloudTrail Threat Investigation & Response | AWS CloudTrail | Threat Detection & IR | Intermediate | 25 mins |

---

## Detailed Lab Specifications

### LAB-001: Public S3 Bucket Discovery & Hardening

- **Learning Goal:** Understand S3 bucket access permissions, identify unauthorized public read exposure, detect data exfiltration vectors, and apply `PublicAccessBlock` configurations to remediate vulnerabilities.
- **Cloud Service:** Amazon S3 (Simulated)
- **Misconfiguration / Threat:** An S3 bucket (`cads-confidential-assets-prod`) is configured with `public_access=True`, exposing confidential company documents (`customer_pii_export.csv`, `system_credentials.env`, `architecture_diagram.pdf`) to unauthenticated actors.
- **Lifecycle Flow:**
  1. **Discover & Enumerate:** Run `aws s3 ls` to identify available buckets and explore files in the target bucket.
  2. **Identify Misconfiguration:** Run `aws s3api get-bucket-policy-status --bucket cads-confidential-assets-prod` or `aws s3api get-public-access-block --bucket cads-confidential-assets-prod` to verify public accessibility.
  3. **Simulate Attack / Data Access:** Run `aws s3 cp s3://cads-confidential-assets-prod/customer_pii_export.csv local_data.csv` to demonstrate unauthenticated data retrieval.
  4. **Detect:** Detection engine triggers the `S3-PUBLIC-ACCESS` rule (Severity: `HIGH`), opening a security finding.
  5. **Investigate:** Examine finding details in the Investigation console, verifying the affected ARN and extracted access evidence.
  6. **Remediate:** Apply `aws s3api put-public-access-block --bucket cads-confidential-assets-prod --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true` or use the 1-click remediation action in the UI.
  7. **Verify & Complete:** Run verification to confirm the bucket is private and all objectives are satisfied; progress updates in the dashboard.

---

### LAB-002: Excessive IAM Permissions & Privilege Escalation

- **Learning Goal:** Audit IAM user permissions and attached policies, recognize dangerous wildcard permissions (`iam:AttachUserPolicy`, `iam:PutUserPolicy`), identify privilege escalation paths, and enforce the principle of least privilege.
- **Cloud Service:** AWS Identity & Access Management (IAM)
- **Misconfiguration / Threat:** User `dev-contractor-01` has an attached policy (`ContractorPrivilegeEscalationPolicy`) granting `iam:AttachUserPolicy` with resource `*`. An attacker who compromises this account can attach `AdministratorAccess` to escalate privileges to full root-equivalent access.
- **Lifecycle Flow:**
  1. **Discover & Enumerate:** Run `aws iam list-users` and `aws iam get-user --user-name dev-contractor-01` to identify the contractor identity.
  2. **Enumerate Policies:** Run `aws iam list-attached-user-policies --user-name dev-contractor-01` and `aws iam get-policy --policy-arn arn:aws:iam::123456789012:policy/ContractorPrivilegeEscalationPolicy` to inspect permissions.
  3. **Simulate Privilege Escalation:** Run `aws iam attach-user-policy --user-name dev-contractor-01 --policy-arn arn:aws:iam::aws:policy/AdministratorAccess` to elevate permissions.
  4. **Detect:** Detection engine triggers the `IAM-PRIVILEGE-ESCALATION` rule (Severity: `CRITICAL`), generating a security finding with evidence of excessive privilege attachment.
  5. **Investigate:** Review the finding evidence, identify the over-permissive policy ARN, and analyze the privilege boundary violation.
  6. **Remediate:** Run `aws iam detach-user-policy --user-name dev-contractor-01 --policy-arn arn:aws:iam::aws:policy/AdministratorAccess` and replace over-permissive policies with least-privilege policies, or click Remediate.
  7. **Verify & Complete:** Run verification to confirm administrative policies are detached and the contractor role is constrained to least privilege.

---

### LAB-003: Insecure Security Group Remediation

- **Learning Goal:** Inspect VPC security group ingress rules, identify open administrative ports exposed to the entire internet (`0.0.0.0/0` on TCP port 22), understand unauthorized remote access risks, and enforce restrictive CIDR ingress filtering.
- **Cloud Service:** Amazon EC2 & VPC Security Groups
- **Misconfiguration / Threat:** Security Group `sg-prod-db-mgmt` protecting critical database hosts has an inbound rule permitting `0.0.0.0/0` on TCP Port 22 (SSH), leaving management interfaces open to brute-force attacks from the public Internet.
- **Lifecycle Flow:**
  1. **Discover & Enumerate:** Run `aws ec2 describe-security-groups` to retrieve all configured security groups.
  2. **Inspect Rules:** Run `aws ec2 describe-security-group-rules --group-id sg-prod-db-mgmt` or `aws ec2 describe-security-groups --group-ids sg-prod-db-mgmt` to inspect ingress CIDRs.
  3. **Identify Insecure Ingress:** Confirm the rule allowing `IpProtocol: tcp`, `FromPort: 22`, `ToPort: 22`, `CidrIp: 0.0.0.0/0`.
  4. **Detect:** Detection engine triggers the `EC2-OPEN-SSH` rule (Severity: `HIGH`), flagging the open port vulnerability.
  5. **Investigate:** Inspect the finding details, noting the exposed port, protocol, and broad CIDR range.
  6. **Remediate:** Run `aws ec2 revoke-security-group-ingress --group-id sg-prod-db-mgmt --protocol tcp --port 22 --cidr 0.0.0.0/0` (and optionally authorize a secure bastion CIDR e.g. `10.0.0.0/16`), or execute automated remediation.
  7. **Verify & Complete:** Verification engine checks that no `0.0.0.0/0` SSH ingress rule exists on `sg-prod-db-mgmt`, resolves the finding, and marks lab completed.

---

### LAB-004: CloudTrail Threat Investigation & Response

- **Learning Goal:** Analyze CloudTrail audit logs, filter activity by username and event name, identify anomalous reconnaissance and privilege escalation events, correlate compromised API access keys, and execute incident response remediation.
- **Cloud Service:** AWS CloudTrail & Identity Security
- **Misconfiguration / Threat:** Compromised credentials for identity `temp-intern-dev` were used from an untrusted public IP (`198.51.100.42`) after hours to execute `DescribeInstances`, `GetSecretValue`, and attempt `AttachUserPolicy`.
- **Lifecycle Flow:**
  1. **Discover & Enumerate Trails:** Run `aws cloudtrail describe-trails` to identify active audit trails and logging status.
  2. **Query Event Logs:** Run `aws cloudtrail lookup-events` to inspect recorded API activity.
  3. **Filter Suspicious Activity:** Run `aws cloudtrail lookup-events --username temp-intern-dev` and `aws cloudtrail lookup-events --event-name GetSecretValue` to trace the attacker's actions.
  4. **Detect:** Detection engine triggers `CLOUDTRAIL-SUSPICIOUS-ACTIVITY` (Severity: `HIGH`) correlating unapproved secret access and permission modification attempts.
  5. **Investigate:** Analyze the event trail timeline, source IP address, requested API actions, and compromised access key ID.
  6. **Remediate (Incident Response):** Run `aws iam delete-access-key --user-name temp-intern-dev --access-key-id AKIAIOSFODNN7EXAMPLE` (or deactivate the compromised identity) to immediately revoke attacker access.
  7. **Verify & Complete:** Run verification to confirm the compromised credentials are invalidated and incident response actions are recorded.

---

## Architectural Isolation & Safety Guarantees

All four labs operate within strict sandboxed simulation bounds:
- **No Real AWS Credentials:** No real cloud APIs are contacted; all interactions run in an isolated in-memory Python state machine with SQLite session persistence.
- **Deterministic Safe Command Engine:** Commands are parsed and mapped via whitelisted dispatchers with zero `eval()`, `exec()`, or subshell execution.
- **User & Session Isolation:** Each student lab session maintains distinct cloud resource states, events, findings, and objective progress.
- **Repeatable & Resettable:** Any lab can be reset at any time to its baseline misconfigured state without affecting other users or labs.
