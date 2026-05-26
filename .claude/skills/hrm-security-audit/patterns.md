# Patterns — 8 grep regex cho security scan

> File này chỉ load **khi cần verify cụ thể 1 pattern** — không load mặc định.
> SKILL.md chỉ liệt kê tên + severity; chi tiết regex + edge case nằm ở đây.

---

## Pattern 1 — Hardcoded API key / secret / token

```regex
(api[_-]?key|secret|password|token|access[_-]?key)\s*=\s*['"][A-Za-z0-9_\-]{8,}['"]
```

**Severity:** 🔴 Critical
**Scope:** `code/*.py`, `code/**/*.py`
**Edge cases:**
- ❌ False positive: `api_key = os.getenv("API_KEY")` — không phải hardcoded
- ❌ False positive: `password = ""` (empty placeholder)
- ✅ True positive: `api_key = "sk-proj-abc123..."`

**Command:**
```bash
grep -rnE "(api[_-]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9_-]{8,}" code/ --include="*.py"
```

---

## Pattern 2 — `.env` file tracked by git

```bash
git ls-files | grep -E "(^|/)\.env$"
```

**Severity:** 🔴 Critical
**Action nếu hit:** `git rm --cached .env && echo ".env" >> .gitignore`
**Quan trọng:** Nếu file đã từng commit thì cần `git filter-repo` hoặc revoke + rotate toàn bộ key.

---

## Pattern 3 — Private key / service account JSON committed

```bash
find . \( -name "*.pem" -o -name "*.key" -o -name "service_account*.json" -o -name "*-key.json" \) | xargs git ls-files
```

**Severity:** 🔴 Critical
**Edge cases:**
- ❌ False positive: `package.json`, `tsconfig.json` chứa key trong tên
- ✅ True positive: `firebase-adminsdk-key.json`, `gcp-service-account.json`

---

## Pattern 4 — API key plaintext trong markdown public

```bash
grep -rln -E "X-API-Key:\s*[a-zA-Z0-9_-]+|api[_-]key=[a-zA-Z0-9_-]{10,}" .claude code --include="*.md"
```

**Severity:** 🟡 Medium (Critical nếu là production key)
**Note phân biệt:**
- Demo key (`${HRM_API_KEY}` — rate-limited, scope hẹp): Medium
- Production key: Critical

---

## Pattern 5 — Bearer token hardcoded

```regex
Bearer\s+[A-Za-z0-9._-]{20,}
```

**Severity:** 🟡 Medium
**Edge cases:**
- ❌ False positive: `Bearer {token}` (template f-string)
- ❌ False positive: `Bearer ${TOKEN}` (env var)
- ✅ True positive: `Bearer eyJhbGciOi...` (real JWT)

**Command:**
```bash
grep -rnE "Bearer [A-Za-z0-9._-]{20,}" code/ --include="*.py"
```

---

## Pattern 6 — PII trong output files

```regex
@(gmail|yahoo|outlook|hotmail)\.com|\b0(3|5|7|8|9)[0-9]{8}\b
```

**Severity:** 🟡 Medium (PII = vi phạm Nghị định 13/2023 nếu public)
**Scope:** `outputs/`, `.claude/skills/*/output/`
**Edge cases:**
- ❌ False positive: email test (`ngoclinhk47u1@gmail.com` — Linh Test data)
- ✅ True positive: tên + SĐT thật của ứng viên non-test

**Command:**
```bash
grep -rln -E "@(gmail|yahoo|outlook|hotmail)\.com|\b0(3|5|7|8|9)[0-9]{8}\b" \
  outputs/ .claude/skills/*/output/
```

---

## Pattern 7 — `.gitignore` thiếu entry quan trọng

```bash
REQUIRED=(".env" "*.env" "*.pem" "*.key" "service_account*.json" "__pycache__/" ".venv/" "*.log")
for entry in "${REQUIRED[@]}"; do
  grep -qF "$entry" .gitignore || echo "MISSING: $entry"
done
```

**Severity:** 🟢 Low (chưa lộ gì, nhưng phòng ngừa)

---

## Pattern 8 — Hardcoded production URL (lock-in risk)

```bash
grep -rln "hrm-api-521103150103" .claude code --include="*.md" --include="*.py" | wc -l
```

**Severity:** 🟢 Low
**Threshold:** > 5 occurrences → recommend tách config file
**Action gợi ý:** Define `HRM_API_BASE` env var, reference qua placeholder

---

## Mapping severity → action

| Severity | Block push? | Timeline fix |
|---|---|---|
| 🔴 Critical | ✅ YES — không push | Ngay lập tức |
| 🟡 Medium | ❌ Không block | < 30 ngày |
| 🟢 Low | ❌ Không block | Backlog, fix khi tiện |
