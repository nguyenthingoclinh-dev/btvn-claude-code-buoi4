# Architecture - Dual Agent Pipeline (Invite + Rejection)

## Bird's-eye view

```
+--------------------------------------------------------------------+
| ngoclinhhrm.com/tuyen-dung/ (Cloudflare Pages)                     |
|   +--------------------------------------------------+             |
|   | Dashboard 90 ung vien - 13 cot                   |             |
|   | Cot "Da gui Email" hien smart display:           |             |
|   |   - Sent invite + timestamp + [Gui lai]          |             |
|   |   - Sent rejection + timestamp + [Gui lai]       |             |
|   |   - Nut [Gui moi PV] khi du 3 DK                 |             |
|   |   - Nut [Gui tu choi] khi Tinh trang Khong       |             |
|   |     phu hop                                      |             |
|   |   - Action moi nhat theo timestamp uu tien hien  |             |
|   +-------------------+------------------------------+             |
+-----------------------|--------------------------------------------+
                        | HTTPS + X-API-Key
                        v
+--------------------------------------------------------------------+
| hrm-api-521103150103.asia-southeast1.run.app (Cloud Run)           |
|  Flask backend (Python)                                            |
|  +--------------------------------------------------------------+  |
|  | GET    /api/candidates                                       |  |
|  | PATCH  /api/candidates/{id}     <- auto-trigger 2 agent      |  |
|  | DELETE /api/candidates/{id}                                  |  |
|  | POST   /api/candidates/{id}/send-invite-email     (manual)   |  |
|  | POST   /api/candidates/{id}/send-rejection-email  (manual)   |  |
|  +--------------------------------------------------------------+  |
|                                                                    |
|  Modules:                                                          |
|    db.py            <- Firestore + 6 NEW fields                    |
|                       (email_invite_*, rejection_email_*)          |
|    lark_mail.py     <- Lark Mail OpenAPI sender +                  |
|                       send_invite_email + send_rejection_email +   |
|                       send_lark_im (NEW)                           |
|    email_reader.py  <- Da co (doc CV tu mail)                      |
|    lark_chat.py     <- Da co (gui IM card)                         |
|                                                                    |
|  Triggers trong PATCH endpoint (chay background thread):           |
|    Snapshot BEFORE update + AFTER update                           |
|    Detect transition: old_tinh_trang != new_tinh_trang             |
|    If transition into "Khong phu hop" -> force send rejection      |
|    If transition into "ready" (Du 3 DK)  -> force send invite      |
+----------------------+---------------------------------------------+
                       |
        +--------------+--------------+
        v                             v
+------------------+   +-------------------------------+
| Firestore        |   | Lark Open Platform (cli_...)  |
| - candidates     |   | - /mail/v1/.../messages/send  |
| - jobs           |   | - /im/v1/messages             |
| - lark_tokens    |   | - /calendar/v4/.../events     |
+------------------+   +-------------------------------+
        ^
        | PATCH status (sent/failed)
        |
+--------------------------------------------------------------------+
| LOCAL CRON LAYER (du phong khi backend trigger miss)               |
|                                                                    |
| dual_agent_scheduler.py - chay moi 30 phut:                        |
|   1. interview_invite_agent.run_once()                             |
|      - Filter: Tinh trang=Phu hop + 3 DK + chua sent               |
|      - Send mail + Lark IM + Calendar                              |
|   2. rejection_mail_agent.run_once()                               |
|      - Filter: Tinh trang=Khong phu hop + chua sent                |
|      - Send mail + Lark IM                                         |
+--------------------------------------------------------------------+
```

## Phan bo sub-agent (Claude Code orchestration)

Khi user giao task lon, Claude Code chinh phan tich va route:

| Buoc | Sub-agent | Skill su dung |
|------|-----------|---------------|
| Doc HRM API tim ung vien du DK | `recruitment-agent` | `hrm-loc-ung-vien` |
| Gui email moi PV | `communication-agent` | `auto-send-email` |
| Gui email tu choi | `communication-agent` | `auto-send-email` |
| Bao Lark cho HRM | `communication-agent` | `lark-setup-bot` |
| Tao Lark Calendar event | `communication-agent` | `lark-calendar-pv` |
| PATCH HRM `email_invite_status=sent` | `recruitment-agent` | `hrm-cap-nhat-ung-vien` |
| PATCH HRM `rejection_email_status=sent` | `recruitment-agent` | `hrm-cap-nhat-ung-vien` |

## Token flow

```
+------------------------------------------------------------------+
| Lark App: HR SEONGON Bot (cli_a97b4c1583f8ded1)                  |
|   Scopes user_token (v1.3.5):                                    |
|     - mail:user_mailbox.message:send                             |
|     - mail:user_mailbox.message:readonly                         |
|     - mail:user_mailbox.message.body:read                        |
|     - calendar:calendar                                          |
+------+-----------------------------------------------------------+
       |
       v OAuth (HRM nguyenthingoclinh@seongon.com authorize)
       |
       v access_token + refresh_token
       |
   +---+----------------------------------------------+
   | Local:  .env CV_LARK_USER_REFRESH_TOKEN          |
   | Cloud:  Firestore lark_tokens/tuyendung          |
   +---+----------------------------------------------+
       |
       | Moi lan dung -> Lark rotate refresh_token moi
       | -> save lai env / Firestore (CRITICAL - single-use!)
       |
       v user_access_token (2h TTL)
   +-----------------------------------------------+
   | POST /open-apis/mail/v1/.../messages/send     |
   |   Bearer <user_token>                         |
   |   payload.body_html = plain HTML              |
   |   payload.head_from = tuyendung@seongon.com   |
   +-----------------------------------------------+
```

## Real-time trigger logic (detect transition)

```python
# Trong PATCH /api/candidates/{id}:

c_before = db.get_candidate(id) or {}
old_tinh_trang = c_before.get("Tinh trang", "")
old_trang_thai = c_before.get("Trang thai", "")
old_lich_pv    = (c_before.get("Lich PV") or "").strip()

updated = db.update_candidate_fields(id, data)

c_after = db.get_candidate(id) or {}
new_tinh_trang = c_after.get("Tinh trang", "")

# TRIGGER REJECTION
if new_tinh_trang == "Khong phu hop":
    transitioned = (old_tinh_trang != new_tinh_trang)
    not_yet_sent = (c_after.get("Email tu choi - Trang thai") != "sent")
    if transitioned or not_yet_sent:
        Thread(target=_trigger_send_rejection,
               args=(id, transitioned)).start()

# TRIGGER INVITE (du 3 DK)
if (new_trang_thai == "Quan ly da duyet"
    and new_tinh_trang == "Phu hop"
    and new_lich_pv and has_email):
    was_ready = (old_trang_thai == "Quan ly da duyet"
                 and old_tinh_trang == "Phu hop"
                 and old_lich_pv)
    transitioned_into_ready = not was_ready
    not_yet_sent = (c_after.get("Email moi PV - Trang thai") != "sent")
    if transitioned_into_ready or not_yet_sent:
        Thread(target=_trigger_send_invite,
               args=(id, transitioned_into_ready)).start()
```

Force=True khi transitioned -> bo qua check da sent, force re-send.

## 4 van de thuc te da xu ly trong session

1. **Refresh token expired (code 20038)** - Lark rotate refresh_token moi
   lan dung nhung code cu khong save lai. Fix: auto-save vao .env ngay
   sau khi refresh.

2. **Tenant token khong gui duoc mail (code 99991663)** - Lark Mail Send
   REQUIRE user_token (OAuth). Fix: chuyen sang user_token + ensure scope
   `mail:user_mailbox.message:send`.

3. **Email body hien thi base64** - Lark Mail API expect plain HTML,
   khong decode base64 (khac Gmail API). Fix: bo `base64.b64encode()`
   tren body_html.

4. **Backend va local dung token khac nhau (code 99991679)** - Backend
   load Firestore (cu), local dung .env (moi). Fix: tao
   `sync_lark_token.py` dong bo local -> Firestore.

## Smart UI display logic (frontend)

Cot "Da gui Email" hien 1 trong 6 trang thai theo uu tien timestamp:

```javascript
const inviteTs = parseTs(emailSentAt);  // "DD/MM/YYYY HH:MM" -> ms
const rejTs    = parseTs(rejSentAt);
const inviteIsLatest = inviteTs >= rejTs;

if (emailStatus && rejStatus) {
  return inviteIsLatest ? renderInvite() : renderRejection();
}
if (emailStatus) return renderInvite();
if (rejStatus)   return renderRejection();

// Chua gui gi -> nut action tuy tinh huong
if (tinh_trang == "Khong phu hop") -> [Gui tu choi]
if (du 3 DK)                       -> [Gui moi PV]
else                               -> "-"
```
