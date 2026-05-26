# Chat history với Claude Code

## 3 loại file để Thầy chấm

| File | Loại | Mô tả |
|------|------|-------|
| [`chat-export.txt`](./chat-export.txt) | XÂY agent | **REAL `/export` output từ Claude Code CLI** (117 KB). Ghi lại quá trình xây 2 agent + 6 skill (21/05/2026). |
| [`chat-history-clean.txt`](./chat-history-clean.txt) | XÂY agent (đã clean) | Bản clean của session xây, dễ đọc tổng quan flow 11 giai đoạn. |
| [`chat-export-chay-agent-2026-05-26.txt`](./chat-export-chay-agent-2026-05-26.txt) | **CHẠY agent** (TODO) | Cần thêm — `/export` session chạy 5 skill thật ngày 26/05 (scan email +27 CV, lọc top 20, PATCH Linh Test 6, etc.) |

## 📌 Theo feedback của thầy

> *"Có 1 file lịch sử được /export đúng và chứa thông tin quá trình **xây** agent, chưa có lịch sử cho phần **chạy** agent"*

→ Cần `/export` thêm session CHẠY (ngày 26/05) để cover:
- POST `/api/scan-emails?hours=24` → +27 CV
- GET `/api/candidates` + filter top 20 điểm AI
- PATCH `/api/candidates/8a0d0844` → ok:true
- hrm-security-agent chạy `hrm-security-audit` skill

## Cách tạo file chat-export.txt

```bash
cd "/Users/Ngoclinh/Desktop/Lark Bot"
claude --resume <session-id>
```

Trong session resume, gõ `/export` → chọn path lưu file.

Session ID xây agent: `e337a42b-c26d-4e00-a576-c93d040f9647`
Session ID chạy agent ngày 26/05: (Sếp lấy từ terminal hiện tại — Cmd+Shift+P hoặc `claude --list-sessions`)
