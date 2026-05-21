# Chat history voi Claude Code

## 2 file de Thay cham

| File | Mo ta | Dung de |
|------|-------|---------|
| [`chat-export.txt`](./chat-export.txt) | **REAL `/export` output tu Claude Code CLI** (117 KB). Co box-drawing header chuan, ky tu `❯` cho user prompt, `⏺` cho Claude response. | Dap ung yeu cau BTVN: "File ghi chep lai lich su tro chuyen voi Claude Code /export" |
| [`chat-history-clean.txt`](./chat-history-clean.txt) | Bien ban session da clean (plain text, khong icon, tom tat theo 11 giai doan logic) | Cho Thay doc nhanh hieu flow tong the |

## Cach tao file chat-export.txt

Chay trong terminal:
```bash
cd "/Users/Ngoclinh/Desktop/Lark Bot"
claude --resume e337a42b-c26d-4e00-a576-c93d040f9647
```
Trong session resume, go `/export` -> chon path luu file.
