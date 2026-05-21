"""Tạo 5 ứng viên 'Linh Test' để demo agent gửi mời PV."""
import sys
from datetime import datetime
sys.path.insert(0, ".")
import db

# Lịch PV: ngày mai → mốt
def lich_pv_offset(days_ahead: int, hour: int, minute: int) -> str:
    from datetime import timedelta
    d = datetime.now() + timedelta(days=days_ahead)
    return f"{hour:02d}:{minute:02d} {d.strftime('%d/%m/%Y')}"


TEST_EMAIL = "ngoclinhk47u1@gmail.com"
COMMON_NGAY_NHAN = datetime.now().strftime("%d/%m/%Y %H:%M")

# 5 ứng viên — mỗi người 1 vị trí khác để cảm giác đa dạng
candidates = [
    {
        "ho_ten": "Linh Test 2 - SEO Manager",
        "vi_tri_ung_tuyen": "SEO Manager",
        "lich_pv": lich_pv_offset(1, 9, 0),
        "diem_ai": "82",
        "ghi_chu_ai": "Ứng viên có 5 năm SEO B2B, đề nghị mời PV chuyên môn.",
        "ky_nang": "SEO, Technical SEO, Content Strategy, Google Analytics",
        "kinh_nghiem_nam": "5",
        "truong_dai_hoc": "Đại học Kinh tế Quốc dân",
        "tom_tat": "Ứng viên test 2 — SEO Manager 5 năm KN.",
    },
    {
        "ho_ten": "Linh Test 3 - Google Ads Lead",
        "vi_tri_ung_tuyen": "Google Ads Lead",
        "lich_pv": lich_pv_offset(1, 14, 30),
        "diem_ai": "75",
        "ghi_chu_ai": "Mạnh về Performance Max và Demand Gen.",
        "ky_nang": "Google Ads, Performance Max, Demand Gen, Looker Studio",
        "kinh_nghiem_nam": "4",
        "truong_dai_hoc": "Đại học Ngoại Thương",
        "tom_tat": "Ứng viên test 3 — Google Ads Lead 4 năm.",
    },
    {
        "ho_ten": "Linh Test 4 - Account Manager",
        "vi_tri_ung_tuyen": "Account Manager (Performance)",
        "lich_pv": lich_pv_offset(2, 10, 0),
        "diem_ai": "78",
        "ghi_chu_ai": "Đã quản 8 khách hàng F&B + retail.",
        "ky_nang": "Account Management, Client Servicing, Performance Marketing",
        "kinh_nghiem_nam": "3",
        "truong_dai_hoc": "Đại học Thương Mại",
        "tom_tat": "Ứng viên test 4 — Account Manager Performance.",
    },
    {
        "ho_ten": "Linh Test 5 - Content SEO",
        "vi_tri_ung_tuyen": "Biên tập viên Content SEO",
        "lich_pv": lich_pv_offset(2, 15, 30),
        "diem_ai": "71",
        "ghi_chu_ai": "Có portfolio 50+ bài top 3 Google.",
        "ky_nang": "Content Writing, SEO On-page, Keyword Research, AEO",
        "kinh_nghiem_nam": "2",
        "truong_dai_hoc": "Đại học KHXH&NV",
        "tom_tat": "Ứng viên test 5 — Content SEO.",
    },
    {
        "ho_ten": "Linh Test 6 - Data Analyst",
        "vi_tri_ung_tuyen": "Data Analyst Marketing",
        "lich_pv": lich_pv_offset(3, 9, 30),
        "diem_ai": "80",
        "ghi_chu_ai": "SQL + Python + Looker Studio fluently.",
        "ky_nang": "SQL, Python, Looker Studio, BigQuery, GA4",
        "kinh_nghiem_nam": "3",
        "truong_dai_hoc": "Đại học Bách Khoa Hà Nội",
        "tom_tat": "Ứng viên test 6 — Data Analyst Marketing.",
    },
]

# Common fields cho tất cả
COMMON = {
    "email": TEST_EMAIL,
    "sdt": "0901707090",
    "nguon": "Thêm tay",
    "email_from": TEST_EMAIL,
    "ngay_nhan": COMMON_NGAY_NHAN,
    "trang_thai": "Quản lý đã duyệt",
    "tinh_trang": "Phù hợp",
    "quan_ly_duyet": "Quản lý đã duyệt",
    "de_xuat_ai": "Mời phỏng vấn",
    "diem_manh": "Phù hợp ngành agency Digital Marketing, có kinh nghiệm thực chiến.",
    "diem_yeu": "Cần làm rõ thêm về case studies thật.",
    # Email status: rỗng → sẽ hiện nút "✉️ Gửi mời PV" trên dashboard
    "email_invite_status": "",
    "email_invite_sent_at": "",
    "email_invite_error": "",
}

if __name__ == "__main__":
    print(f"Tạo {len(candidates)} ứng viên 'Linh Test' với email {TEST_EMAIL}...")
    for i, c in enumerate(candidates, 1):
        # Sinh email_id duy nhất để tránh dedup trùng
        from datetime import datetime
        unique = f"manual_linhtest{i}_{int(datetime.now().timestamp())}"
        payload = {**COMMON, **c, "email_id": unique}
        new_id = db.add_candidate(payload)
        print(f"  [{i}/5] ✅ {c['ho_ten']} → id={new_id} (vị trí: {c['vi_tri_ung_tuyen']}, Lịch PV: {c['lich_pv']})")
    print(f"\n🎉 Done. Mở https://ngoclinhhrm.com/tuyen-dung/ để xem 5 ứng viên mới.")
