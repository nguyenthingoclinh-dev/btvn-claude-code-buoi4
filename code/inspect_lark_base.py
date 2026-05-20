"""
Diagnostic: in toàn bộ field schema của bảng CV trên Lark Base + 1 record mẫu.
Dùng để debug khi agent không tìm thấy ứng viên (sai tên field, sai value).

Chạy: python inspect_lark_base.py
"""

import json

import requests

from config import (
    CV_LARK_APP_TOKEN,
    CV_LARK_TABLE_ID,
    CV_LARK_TOKEN_TYPE,
    LARK_DOMAIN,
)
from lark_client import lark


def dump_schema() -> dict:
    app_token = lark.resolve_app_token(CV_LARK_APP_TOKEN, CV_LARK_TOKEN_TYPE)
    url = f"{LARK_DOMAIN}/open-apis/bitable/v1/apps/{app_token}/tables/{CV_LARK_TABLE_ID}/fields"
    resp = requests.get(url, headers=lark._headers(), params={"page_size": 100}, timeout=15).json()
    if resp.get("code") != 0:
        print("❌ Lỗi lấy schema:", resp)
        return {}

    fields = resp.get("data", {}).get("items", [])
    type_map = {
        1: "Text", 2: "Number", 3: "SingleSelect", 4: "MultiSelect",
        5: "DateTime", 7: "Checkbox", 11: "User", 13: "Phone",
        15: "Hyperlink", 17: "Attachment", 18: "OneWayLink", 19: "Lookup",
        20: "Formula", 21: "TwoWayLink", 22: "Location", 23: "GroupChat",
        1001: "CreatedTime", 1002: "ModifiedTime", 1003: "CreatedUser",
        1004: "ModifiedUser", 1005: "AutoNumber",
    }
    print(f"\n=== {len(fields)} FIELDS trong bảng CV ===")
    name_to_type = {}
    for f in fields:
        fname = f["field_name"]
        ftype = type_map.get(f["type"], f"?{f['type']}")
        name_to_type[fname] = ftype
        extra = ""
        if f["type"] == 3:  # SingleSelect → in options
            opts = f.get("property", {}).get("options", [])
            extra = f"  options={[o['name'] for o in opts]}"
        print(f"  • {fname:<30} type={ftype}{extra}")
    return name_to_type


def dump_sample_records(limit: int = 3) -> None:
    app_token = lark.resolve_app_token(CV_LARK_APP_TOKEN, CV_LARK_TOKEN_TYPE)
    url = f"{LARK_DOMAIN}/open-apis/bitable/v1/apps/{app_token}/tables/{CV_LARK_TABLE_ID}/records/search"
    resp = requests.post(url, headers=lark._headers(), json={"page_size": limit}, timeout=15).json()
    items = resp.get("data", {}).get("items", [])
    print(f"\n=== {len(items)} RECORDS MẪU (giới hạn {limit}) ===")
    for r in items:
        print("─" * 60)
        print(f"record_id: {r.get('record_id')}")
        for k, v in (r.get("fields") or {}).items():
            v_str = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
            if len(v_str) > 200:
                v_str = v_str[:200] + "..."
            print(f"  {k}: {v_str}")


def check_filter() -> None:
    """Thử chạy filter giống agent. In ra có bao nhiêu record match."""
    from interview_invite_agent import (
        FIELD_FIT,
        FIELD_INTERVIEW,
        FIELD_STATUS,
        FIT_YES,
        STATUS_READY,
    )

    app_token = lark.resolve_app_token(CV_LARK_APP_TOKEN, CV_LARK_TOKEN_TYPE)
    url = f"{LARK_DOMAIN}/open-apis/bitable/v1/apps/{app_token}/tables/{CV_LARK_TABLE_ID}/records/search"
    body = {
        "page_size": 50,
        "filter": {
            "conjunction": "and",
            "conditions": [
                {"field_name": FIELD_STATUS, "operator": "is", "value": [STATUS_READY]},
                {"field_name": FIELD_FIT, "operator": "is", "value": [FIT_YES]},
                {"field_name": FIELD_INTERVIEW, "operator": "isNotEmpty", "value": []},
            ],
        },
    }
    print(f"\n=== FILTER TEST ===")
    print(f"  {FIELD_STATUS} = {STATUS_READY!r}")
    print(f"  AND {FIELD_FIT} = {FIT_YES!r}")
    print(f"  AND {FIELD_INTERVIEW} != rỗng")
    resp = requests.post(url, headers=lark._headers(), json=body, timeout=15).json()
    if resp.get("code") != 0:
        print(f"❌ Filter lỗi: {resp}")
        return
    items = resp.get("data", {}).get("items", [])
    print(f"✅ Tìm thấy {len(items)} record match.")
    for r in items[:5]:
        fields = r.get("fields", {})
        print(f"  → record_id={r.get('record_id')} | fields keys={list(fields.keys())}")


if __name__ == "__main__":
    dump_schema()
    dump_sample_records(limit=3)
    check_filter()
