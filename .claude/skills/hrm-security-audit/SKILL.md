---
name: hrm-security-audit
description: This skill should be used when the user asks to "audit bảo mật HRM", "scan code tìm credential lộ", "check API key lộ trong repo", "kiểm tra security HRM SEONGON", "security scan", or any code security review on the HRM workspace. Scans Python source + skill markdown for hardcoded secrets, exposed API keys, missing .gitignore entries, weak token storage. Use proactively before mỗi lần push code lên public repo.
---

# Skill: Audit bảo mật HRM workspace

Skill này kiểm tra workspace HRM SEONGON cho các lỗ hổng bảo mật phổ biến trước khi push code public. Mục tiêu: tránh lộ credential/PII ứng viên.

## Khi nào dùng skill này

Trigger khi user:
- "Audit bảo mật code"
- "Check repo có lộ API key không"
- "Quét credential trong code"
- "Security review trước khi public repo"
- "Có file nào chứa token không?"

## 🔍 Các loại lỗ hổng skill này phát hiện

| # | Pattern | Severity | Cách phát hiện |
|---|---|---|---|
| 1 | Hardcoded API key/secret/token | 🔴 Critical | regex `(api[_-]?key\|secret\|password\|token)\s*=\s*['"][A-Za-z0-9_-]{8,}` |
| 2 | `.env` bị commit | 🔴 Critical | check `git ls-files \| grep '\.env$'` |
| 3 | Private key/cert leak | 🔴 Critical | tìm `*.pem`, `*.key`, `service_account*.json` đã track |
| 4 | API key trong markdown public | 🟡 Medium | grep `X-API-Key:` trong .md |
| 5 | Bearer token hardcoded | 🟡 Medium | regex `Bearer [A-Za-z0-9._-]{20,}` |
| 6 | PII ứng viên trong output (email, SĐT, CV link) | 🟡 Medium | scan output files |
| 7 | `.gitignore` thiếu entry quan trọng | 🟢 Low | check `.env`, `*.pem`, `*.key`, `__pycache__/` |
| 8 | Hardcoded production URL (rủi ro lock-in) | 🟢 Low | đếm số lần xuất hiện base URL |

## 📋 Quy trình 5 bước

### Bước 1 — Xác định scope

Hỏi user (mặc định cả repo nếu không nói):
- Folder cần scan (`.claude/`, `code/`, hay toàn bộ)
- Ignore folder nào (vd: `outputs/` thường có data thật)

### Bước 2 — Chạy 8 grep pattern

```bash
# Pattern 1 — hardcoded secrets
grep -rn -E "(api[_-]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9_-]{8,}" code/ --include="*.py"

# Pattern 2 — .env tracked
git ls-files | grep -E "\.env$"

# Pattern 3 — private keys
find . -name "*.pem" -o -name "*.key" -o -name "service_account*.json" | xargs git ls-files

# Pattern 4 — API key in docs
grep -rln "X-API-Key:" .claude code --include="*.md"

# Pattern 5 — Bearer hardcoded
grep -rn -E "Bearer [A-Za-z0-9._-]{20,}" code/

# Pattern 6 — PII in outputs
grep -rln -E "@gmail\.com|@yahoo\.com|\b09[0-9]{8}\b|\b03[0-9]{8}\b" outputs/ .claude/skills/*/output/

# Pattern 7 — .gitignore audit
diff <(cat .gitignore) <(echo -e ".env\n*.pem\n*.key\n__pycache__/")

# Pattern 8 — count hardcoded prod URL
grep -rln "hrm-api-521103150103" .claude code --include="*.md" --include="*.py" | wc -l
```

### Bước 3 — Phân loại findings

Mỗi finding gắn severity Critical/Medium/Low + recommendation.

### Bước 4 — Xuất báo cáo Markdown

Lưu vào `output/security-audit-{YYYY-MM-DD}.md` với 4 section:
- Executive summary (pass/fail score)
- Critical findings (must fix trước push)
- Medium findings (nên fix)
- Low findings + ghi chú

### Bước 5 — Đề xuất hành động cụ thể

Mỗi finding có 1 dòng command/edit để fix.

## ⚠️ Vết xe đổ thường gặp

| Lỗi | Cách tránh |
|---|---|
| Báo false positive cho API key trong SKILL.md (vì là demo key) | Tag riêng "demo/staging key" — không Critical |
| Bỏ sót file `.env` đã commit lỡ | Luôn check `git ls-files`, không chỉ filesystem |
| Scan quá nhiều folder → slow | Default scope: `.claude/` + `code/`, skip `outputs/` (data thật) |
| Bỏ qua PII trong output | Skill có category riêng cho PII — không trộn với credential |

## ✅ Tiêu chí self-check trước khi finish

- [ ] Đã chạy đủ 8 pattern
- [ ] Mỗi finding có file path + line number cụ thể
- [ ] Có severity rõ ràng
- [ ] Có recommendation actionable cho mỗi finding
- [ ] Có executive summary (số finding/severity)
- [ ] File output đúng path `output/security-audit-{date}.md`
