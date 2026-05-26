# Severity rubric — cách phân loại finding

> Load file này **khi đang phân loại finding biên giới giữa 2 severity** — không load mặc định.

## Nguyên tắc

Severity = (Impact nếu bị khai thác) × (Probability bị khai thác trong public repo)

## 🔴 Critical — chặn push, fix ngay

Finding thuộc nhóm này nếu thoả MỘT trong:

1. **Lộ credential dùng được luôn:** API key/secret/token cho production system, ngay cả khi chỉ xuất hiện 1 lần trong git history
2. **Lộ private key/certificate:** `.pem`, `.key`, service account JSON đã commit
3. **`.env` file đã tracked by git:** cho dù value hiện tại là placeholder, lịch sử commit có thể chứa secret thật
4. **Lộ database connection string:** `mongodb+srv://user:pass@cluster.../db`, `postgres://...`

**Ví dụ thực tế:**
- ❌ `LARK_APP_SECRET = "cli_abc123real_secret_here"` trong code committed
- ❌ `firebase-adminsdk-xxxxx.json` push lên public repo
- ❌ `.env` chứa `OPENAI_API_KEY=sk-proj-...` đã commit

## 🟡 Medium — nên fix < 30 ngày, không chặn push

1. **Demo/staging key lộ:** key được scope hẹp, rate-limited, không touch production data
2. **PII trong output public:** tên + email ứng viên thật, kể cả non-critical
3. **Bearer token pattern weakness:** dùng template đúng nhưng có log thừa
4. **Permission scope quá rộng:** app có scope mà use case không cần

**Ví dụ thực tế:**
- ⚠️ `X-API-Key: ${HRM_API_KEY}` plaintext trong SKILL.md (demo key, rate-limited)
- ⚠️ Output file có tên ứng viên thật + Link CV
- ⚠️ Lark Bot có scope `mail:user_mailbox.message:send` trong khi chỉ cần gửi từ 1 mailgroup

## 🟢 Low — backlog, fix khi tiện

1. **Hardcoded URL/identifier không phải secret:** lock-in risk, không phải security
2. **`.gitignore` thiếu entry chuẩn:** chưa lộ gì nhưng phòng ngừa
3. **Best practice không tối ưu:** ví dụ thiếu audit log, thiếu alert expire token

## Khi không chắc — quy tắc thận trọng

> Khi finding nằm biên giới 2 mức (vd: demo key có CRITICAL nếu attacker dùng để probe rate-limit) → **chọn mức CAO HƠN**.

Lý do: false positive Critical (tốn 5 phút review) rẻ hơn false negative Critical (lộ key thật).

## Tham chiếu

- OWASP Top 10 (2023) — A07: Identification and Authentication Failures
- Nghị định 13/2023/NĐ-CP — bảo vệ dữ liệu cá nhân (PII)
- GitHub secret scanning patterns: https://docs.github.com/en/code-security/secret-scanning
