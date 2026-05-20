"""List tất cả tables trong Lark Base app — tìm table HRM thật."""

import requests

from config import CV_LARK_APP_TOKEN, CV_LARK_TOKEN_TYPE, LARK_DOMAIN
from lark_client import lark


def main() -> None:
    app_token = lark.resolve_app_token(CV_LARK_APP_TOKEN, CV_LARK_TOKEN_TYPE)
    url = f"{LARK_DOMAIN}/open-apis/bitable/v1/apps/{app_token}/tables"
    resp = requests.get(
        url, headers=lark._headers(), params={"page_size": 100}, timeout=15,
    ).json()
    tables = resp.get("data", {}).get("items", [])
    print(f"\n=== {len(tables)} TABLES trong Lark Base app ===\n")
    for t in tables:
        print(f"  table_id={t['table_id']}  name={t['name']!r}  revision={t.get('revision')}")

    # Với mỗi table, list fields để tìm table có "Trạng thái"
    print("\n=== FIELDS của mỗi table ===\n")
    for t in tables:
        tid = t["table_id"]
        fields_url = f"{LARK_DOMAIN}/open-apis/bitable/v1/apps/{app_token}/tables/{tid}/fields"
        r = requests.get(fields_url, headers=lark._headers(), params={"page_size": 100}, timeout=15).json()
        fields = r.get("data", {}).get("items", [])
        names = [f["field_name"] for f in fields]
        print(f"  📋 {t['name']!r} ({tid}): {len(fields)} fields")
        for n in names:
            mark = ""
            if n in ("Trạng thái", "Tình trạng", "Lịch PV", "Lịch phỏng vấn"):
                mark = "  ← MATCH HRM!"
            print(f"      • {n}{mark}")
        print()


if __name__ == "__main__":
    main()
