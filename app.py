import json
import os
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import altair as alt
import pandas as pd
import streamlit as st


APP_TITLE_LINE_1 = "Tiêu chí Chất lượng cơ bản"
APP_TITLE_LINE_2 = "Bệnh viện Sức khỏe Tâm thần BR-VT"

DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_data() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_PATH):
        return []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            return raw
    except Exception:
        pass
    return []


def save_data(records: List[Dict[str, Any]]) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def mode_label(mode: str) -> str:
    return {
        "tochuc": "Tổ chức - Hành chính",
        "ksnk": "Chống nhiễm khuẩn",
        "duoc": "Dược - XN-CĐHA",
        "kehoach": "Kế hoạch nghiệp vụ",
    }.get(mode, mode)


def get_chuc_danh(record: Dict[str, Any]) -> str:
    # Backward-compatible: dữ liệu cũ có thể dùng key "hospital"
    return (record.get("chuc_danh") or record.get("hospital") or "").strip()


def criteria_defs() -> List[Dict[str, str]]:
    # section: I/II/III/IV/V để thống kê theo nhóm tiêu chuẩn
    return [
        # TCHC - I
        {"key": "standard_1", "label": "1. Bệnh viện phải có địa điểm cố định.*", "section": "I", "mode": "tochuc"},
        {"key": "standard_2", "label": "2. Bệnh viện phải có lối đi cho xe cứu thương ra vào khu vực cấp cứu.*", "section": "I", "mode": "tochuc"},
        {"key": "standard_3_1", "label": "3.1. Được bố trí phù hợp với chức năng của từng bộ phận*", "section": "I", "mode": "tochuc"},
        {"key": "standard_3_2", "label": "3.2. Bảo đảm kết nối về hạ tầng giao thông giữa các bộ phận chuyên môn thuận tiện cho việc khám bệnh, chữa bệnh, an toàn cho người bệnh, người nhà người bệnh và nhân viên y tế.*", "section": "I", "mode": "tochuc"},
        {"key": "standard_4", "label": "4. Có biển hiệu, sơ đồ và biển chỉ dẫn đến các khoa, phòng, bộ phận chuyên môn, hành chính.*", "section": "I", "mode": "tochuc"},
        {"key": "standard_5", "label": "5. Có phương tiện vận chuyển cấp cứu trong và ngoài bệnh viện.*", "section": "I", "mode": "tochuc"},
        {"key": "standard_8", "label": "8. Có điện, nước phục vụ hoạt động của cơ sở khám bệnh, chữa bệnh.*", "section": "I", "mode": "tochuc"},
        # TCHC - II
        {"key": "standard_II_1", "label": "1. Bệnh viện phải có cơ cấu tổ chức gồm các khoa: khám bệnh, lâm sàng, cận lâm sàng, khoa dược và các bộ phận phụ trợ.*", "section": "II", "mode": "tochuc"},
        {"key": "standard_II_2", "label": "2. Khoa khám bệnh phải có nơi tiếp đón, phòng cấp cứu, phòng lưu, phòng khám, phòng thực hiện kỹ thuật, thủ thuật (nếu thực hiện các kỹ thuật, thủ thuật).*", "section": "II", "mode": "tochuc"},
        {"key": "standard_II_3a", "label": "3.a) Đối với bệnh viện đa khoa: có tối thiểu hai trong bốn khoa nội, ngoại, sản, nhi.*", "section": "II", "mode": "tochuc"},
        {"key": "standard_II_3b", "label": "3.b) Đối với bệnh viện chuyên khoa, bệnh viện y học cổ truyền, bệnh viện răng hàm mặt: có tối thiểu một khoa lâm sàng phù hợp với phạm vi hoạt động chuyên môn.*", "section": "II", "mode": "tochuc"},
        {"key": "standard_II_4", "label": "4. Khoa cận lâm sàng: có tối thiểu một phòng xét nghiệm và một phòng chẩn đoán hình ảnh. Riêng đối với bệnh viện chuyên khoa mắt nếu không có bộ phận chẩn đoán hình ảnh thì phải có hợp đồng hỗ trợ chuyên môn với cơ sở khám bệnh, chữa bệnh đã được cấp giấy phép hoạt động có bộ phận chẩn đoán hình ảnh.*", "section": "II", "mode": "tochuc"},
        {"key": "standard_II_5", "label": "5. Khoa dược có các bộ phận: nghiệp vụ dược, kho và cấp phát, thống kê dược, thông tin thuốc và dược lâm sàng.*", "section": "II", "mode": "tochuc"},
        {"key": "standard_II_6", "label": "6. Khoa dinh dưỡng; bộ phận dinh dưỡng lâm sàng; người phụ trách công tác dinh dưỡng; người làm công tác dinh dưỡng.*", "section": "II", "mode": "tochuc"},
        {"key": "standard_II_7", "label": "7. Khoa kiểm soát nhiễm khuẩn; bộ phận kiểm soát nhiễm khuẩn; người làm công tác kiểm soát nhiễm khuẩn.*", "section": "II", "mode": "tochuc"},
        {"key": "standard_II_8", "label": "8. Các bộ phận chuyên môn khác trong bệnh viện phù hợp với phạm vi hoạt động chuyên môn.*", "section": "II", "mode": "tochuc"},
        {"key": "standard_II_9", "label": "9. Các phòng, bộ phận để thực hiện các chức năng về kế hoạch tổng hợp, tổ chức nhân sự, quản lý chất lượng, điều dưỡng, tài chính kế toán, công nghệ thông tin, thiết bị y tế và các chức năng cần thiết khác.*", "section": "II", "mode": "tochuc"},
        # TCHC - III
        {"key": "standard_III_1", "label": "1. Người hành nghề được phân công công việc phù hợp với phạm vi hành nghề được cấp có thẩm quyền phê duyệt.*", "section": "III", "mode": "tochuc"},
        {"key": "standard_III_2", "label": "2. Người hành nghề được cập nhật kiến thức y khoa liên tục.*", "section": "III", "mode": "tochuc"},
        # KSNK - I + V
        {"key": "ksnk_6_1", "label": "6.1. Có biện pháp xử lý chất thải sinh hoạt.*", "section": "I", "mode": "ksnk"},
        {"key": "ksnk_6_2", "label": "6.2. Có biện pháp xử lý chất thải y tế.*", "section": "I", "mode": "ksnk"},
        {"key": "ksnk_V_5", "label": "5. Kiểm soát nhiễm khuẩn bao gồm: tổ chức, phân công nhiệm vụ; xây dựng quy trình.*", "section": "V", "mode": "ksnk"},
        # DƯỢC - I + IV
        {"key": "duoc_7_1", "label": "7.1. Có Giấy phép tiến hành công việc bức xạ.*", "section": "I", "mode": "duoc"},
        {"key": "duoc_7_2", "label": "7.2. Có văn bản phân công người chịu trách nhiệm về công tác an toàn bức xạ.*", "section": "I", "mode": "duoc"},
        {"key": "duoc_7_3", "label": "7.3. Nhân viên thực hiện công việc bức xạ có Chứng chỉ nhân viên bức xạ.*", "section": "I", "mode": "duoc"},
        {"key": "duoc_7_4", "label": "7.4. Có trang bị liều kế cho nhân viên bức xạ.*", "section": "I", "mode": "duoc"},
        {"key": "duoc_IV_1", "label": "1. Thiết bị y tế để thực hiện kỹ thuật thuộc phạm vi hoạt động chuyên môn đã được cấp có thẩm quyền phê duyệt và có hồ sơ quản lý đối với các thiết bị đó.*", "section": "IV", "mode": "duoc"},
        {"key": "duoc_IV_2", "label": "2. Quy chế quản lý, sử dụng, kiểm tra, bảo dưỡng, bảo trì, sửa chữa, thay thế vật tư linh kiện, bảo quản thiết bị y tế tại cơ sở khám bệnh, chữa bệnh.*", "section": "IV", "mode": "duoc"},
        {"key": "duoc_IV_3", "label": "3. Quy trình về sử dụng, vận hành, sửa chữa, bảo dưỡng đảm bảo chất lượng thiết bị y tế.*", "section": "IV", "mode": "duoc"},
        {"key": "duoc_IV_4", "label": "4. Thiết bị y tế thuộc danh mục phải kiểm định, hiệu chuẩn được kiểm định, hiệu chuẩn theo quy định.*", "section": "IV", "mode": "duoc"},
        {"key": "duoc_IV_5", "label": "5. Bộ phận và nhân sự thực hiện nhiệm vụ quản lý việc sử dụng, kiểm tra, bảo dưỡng, bảo trì, sửa chữa, kiểm định, hiệu chuẩn thiết bị y tế.*", "section": "IV", "mode": "duoc"},
        # KẾ HOẠCH - V
        {"key": "kehoach_V_1", "label": "1. Điều trị nội trú, tổ chức trực chuyên môn 24/24 giờ của tất cả các ngày.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_2", "label": "2. Quy trình khám bệnh, chữa bệnh ngoại trú.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_3_1", "label": "3.1. Phổ biến các quy trình kỹ thuật khám bệnh, chữa bệnh do Bộ Y tế hoặc bệnh viện ban hành.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_3_2", "label": "3.2. Phổ biến các hướng dẫn chẩn đoán và điều trị do Bộ Y tế hoặc bệnh viện ban hành.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_3_3", "label": "3.3. Áp dụng các quy trình kỹ thuật khám bệnh, chữa bệnh do Bộ Y tế hoặc bệnh viện ban hành.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_3_4", "label": "3.4. Áp dụng các hướng dẫn chẩn đoán và điều trị do Bộ Y tế hoặc bệnh viện ban hành.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_3_5", "label": "3.5. Tập huấn hoặc phổ biến hoặc có chỉ đạo về việc tuân thủ các quy định trong kê đơn thuốc.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_4_1", "label": "4.1. Thành lập hệ thống quản lý chất lượng.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_4_2", "label": "4.2. Quy chế hoạt động của hội đồng quản lý chất lượng bệnh viện.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_4_3", "label": "4.3. Kế hoạch đổi/ cải tiến chất lượng chung của toàn bệnh viện cho năm hiện tại hoặc cho giai đoạn từ một đến ba năm tiếp theo.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_4_4", "label": "4.4. Chỉ số chất lượng bệnh viện và kết quả đo lường.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_4_5", "label": "4.5. Quản lý chất lượng xét nghiệm gồm: kế hoạch quản lý chất lượng xét nghiệm, xây dựng quy trình hướng dẫn, tập huấn cho nhân viên liên quan, đánh giá thực hiện kế hoạch quản lý chất lượng xét nghiệm liên quan.*", "section": "V", "mode": "kehoach"},
        {"key": "kehoach_V_4_6", "label": "4.6. Báo cáo sự cố y khoa.*", "section": "V", "mode": "kehoach"},
    ]


def criteria_keys_for_mode(mode: str) -> List[str]:
    return [c["key"] for c in criteria_defs() if c["mode"] == mode]


def criteria_label_map() -> Dict[str, str]:
    return {c["key"]: c["label"] for c in criteria_defs()}


def compute_stats(records: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, int]], Dict[str, int], Dict[str, int]]:
    # bySection[I..V] = {co, khong, na}
    by_section = {k: {"co": 0, "khong": 0, "na": 0} for k in ["I", "II", "III", "IV", "V"]}
    by_type = {k: 0 for k in ["tochuc", "ksnk", "duoc", "kehoach"]}
    totals = {"co": 0, "khong": 0, "na": 0}

    key_to_section = {c["key"]: c["section"] for c in criteria_defs()}
    keys = list(key_to_section.keys())

    for r in records:
        m = r.get("mode")
        if m in by_type:
            by_type[m] += 1
        for k in keys:
            v = r.get(k)
            if not v:
                continue
            section = key_to_section[k]
            if v == "Có":
                by_section[section]["co"] += 1
                totals["co"] += 1
            elif v == "Không":
                by_section[section]["khong"] += 1
                totals["khong"] += 1
            elif v == "Không áp dụng":
                by_section[section]["na"] += 1
                totals["na"] += 1

    return by_section, by_type, totals


def filter_records(
    records: List[Dict[str, Any]],
    search: str,
    mode: str,
    criterion_key: str,
    result_value: str,
) -> List[Dict[str, Any]]:
    out = records[:]

    if mode:
        out = [r for r in out if r.get("mode") == mode]

    # Filter by criterion/result
    if criterion_key != "__all__" or result_value:
        all_keys = [c["key"] for c in criteria_defs()]

        def match_value(v: Any) -> bool:
            if not result_value:
                return True
            return v == result_value

        if criterion_key == "__all__":
            if result_value:
                out = [r for r in out if any(match_value(r.get(k)) for k in all_keys)]
        else:
            out = [r for r in out if match_value(r.get(criterion_key))]

    s = (search or "").strip().lower()
    if s:
        def rec_match(r: Dict[str, Any]) -> bool:
            base = f"{get_chuc_danh(r)} {r.get('evaluator','')} {r.get('notes','')}".lower()
            if s in base:
                return True
            # search in criteria answers too
            for k, v in r.items():
                if k in ("id", "mode", "date", "createdAt", "hospital", "chuc_danh", "evaluator", "notes"):
                    continue
                if v and s in str(v).lower():
                    return True
            return False

        out = [r for r in out if rec_match(r)]

    # Sort newest first
    def sort_key(r: Dict[str, Any]):
        d = r.get("date")
        try:
            return datetime.fromisoformat(d) if d else datetime.fromisoformat(r.get("createdAt", "1970-01-01T00:00:00"))
        except Exception:
            return datetime.min

    out.sort(key=sort_key, reverse=True)
    return out


def record_to_row(r: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "id": r.get("id"),
        "Loại phiếu": mode_label(r.get("mode", "")),
        "Chức danh": get_chuc_danh(r),
        "Người đánh giá": r.get("evaluator", ""),
        "Ngày": r.get("date", ""),
        "Ghi chú": r.get("notes", ""),
    }
    labels = criteria_label_map()
    for k in labels.keys():
        row[labels[k]] = r.get(k, "")
    return row


def records_to_df(records: List[Dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    rows = [record_to_row(r) for r in records]
    df = pd.DataFrame(rows)
    return df


def upsert_record(records: List[Dict[str, Any]], rec: Dict[str, Any]) -> None:
    rid = rec.get("id")
    for i, r in enumerate(records):
        if r.get("id") == rid:
            records[i] = rec
            return
    records.append(rec)


def delete_record(records: List[Dict[str, Any]], rid: int) -> None:
    records[:] = [r for r in records if r.get("id") != rid]


def radio_yes_no(label: str, key: str, allow_na: bool = False) -> str:
    options = ["Có", "Không"] + (["Không áp dụng"] if allow_na else [])
    return st.radio(label, options, horizontal=True, key=key)


def _safe_date(value: Optional[str]) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except Exception:
        return date.today()


def _clear_prefix(prefix: str) -> None:
    for k in list(st.session_state.keys()):
        if k.startswith(prefix):
            del st.session_state[k]


def render_form_structured(
    mode: str,
    title: str,
    subtitle: str,
    sections: List[Tuple[str, List[Tuple[Optional[str], str, bool]]]],
) -> None:
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)

    edit_id = st.session_state.get(f"edit_id_{mode}")
    records: List[Dict[str, Any]] = st.session_state.records
    current = next((r for r in records if r.get("id") == edit_id), None) if edit_id else None

    # Prefill widgets when entering edit mode
    prefill_key = f"__prefilled_{mode}"
    if current and st.session_state.get(prefill_key) != current.get("id"):
        st.session_state[f"{mode}_date"] = _safe_date(current.get("date"))
        st.session_state[f"{mode}_evaluator"] = current.get("evaluator", "")
        st.session_state[f"{mode}_chuc_danh"] = get_chuc_danh(current)
        st.session_state[f"{mode}_notes"] = current.get("notes", "")
        for sec_title, items in sections:
            for key, _text, _allow_na in items:
                if not key:
                    continue
                st.session_state[f"{mode}_{key}"] = current.get(key, "Có") or "Có"
        st.session_state[prefill_key] = current.get("id")

    with st.form(key=f"form_{mode}", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            d = st.date_input(
                "Ngày đánh giá",
                value=_safe_date(current.get("date") if current else None),
                key=f"{mode}_date",
            )
        with col2:
            evaluator = st.text_input(
                "Người đánh giá",
                value=current.get("evaluator", "") if current else "",
                key=f"{mode}_evaluator",
            )

        chuc_danh = st.text_input(
            "Chức danh",
            value=get_chuc_danh(current) if current else "",
            key=f"{mode}_chuc_danh",
        )

        st.divider()

        answers: Dict[str, str] = {}
        for sec_title, items in sections:
            st.markdown(f"### {sec_title}")
            for key, text, allow_na in items:
                if key is None:
                    st.markdown(f"**{text}**")
                    continue
                answers[key] = radio_yes_no(text, key=f"{mode}_{key}", allow_na=allow_na)
            st.divider()

        notes = st.text_area(
            "Ghi chú bổ sung",
            value=current.get("notes", "") if current else "",
            key=f"{mode}_notes",
        )

        c1, c2, c3 = st.columns([1, 1, 2])
        save_clicked = c1.form_submit_button("💾 Lưu", type="primary")
        clear_clicked = c2.form_submit_button("🧹 Xóa form")
        if current:
            c3.info(f"Đang sửa phiếu ID: {current['id']}")

    if clear_clicked:
        st.session_state[f"edit_id_{mode}"] = None
        st.session_state[prefill_key] = None
        _clear_prefix(f"{mode}_")
        st.rerun()

    if save_clicked:
        if not evaluator.strip() or not chuc_danh.strip():
            st.error("Vui lòng nhập đầy đủ: Người đánh giá và Chức danh.")
            return

        rid = int(time.time() * 1000) if not current else int(current["id"])
        rec = {
            "id": rid,
            "mode": mode,
            "date": d.isoformat(),
            "evaluator": evaluator.strip(),
            "chuc_danh": chuc_danh.strip(),
            "notes": notes.strip(),
            "createdAt": _now_iso() if not current else current.get("createdAt", _now_iso()),
        }
        rec.update(answers)
        upsert_record(records, rec)
        save_data(records)
        st.session_state[f"edit_id_{mode}"] = None
        st.session_state[prefill_key] = None
        st.success("Đã lưu thành công.")
        st.rerun()


def main() -> None:
    st.set_page_config(page_title=f"{APP_TITLE_LINE_1} - {APP_TITLE_LINE_2}", layout="wide")
    # Theme/CSS: nền xanh nhạt + banner gradient giống ảnh mẫu
    st.markdown(
        """
        <style>
        /* Nền chính */
        [data-testid="stAppViewContainer"] {
          background-color: #e9f2ff; /* xanh nhạt */
        }
        /* Header trong suốt để thấy nền */
        [data-testid="stHeader"] {
          background: rgba(0, 0, 0, 0);
        }
        /* Sidebar xanh nhạt hơn */
        [data-testid="stSidebar"] {
          background-color: #dbeaff;
        }
        /* Giảm padding trên cùng để banner sát hơn */
        .block-container {
          padding-top: 0.75rem;
        }
        /* Banner tràn ngang */
        .hero {
          width: 100vw;
          margin-left: calc(50% - 50vw);
          margin-right: calc(50% - 50vw);
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 42px 18px 34px 18px;
          box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
        }
        .hero-inner {
          max-width: 1200px;
          margin: 0 auto;
          text-align: center;
        }
        .hero-title {
          font-weight: 800;
          letter-spacing: 0.2px;
          text-shadow: 0 3px 10px rgba(0,0,0,0.25);
          line-height: 1.18;
          font-size: 44px;
        }
        .hero-subtitle {
          margin-top: 12px;
          font-size: 18px;
          opacity: 0.92;
        }
        .hero-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 54px;
          height: 54px;
          border-radius: 14px;
          background: rgba(255,255,255,0.18);
          box-shadow: inset 0 0 0 1px rgba(255,255,255,0.22);
          margin-bottom: 14px;
          font-size: 28px;
        }

        /* Tabs: nền trắng cho phần tab */
        [data-testid="stTabs"] [role="tablist"] {
          background: rgba(255,255,255,0.92);
          border-radius: 12px;
          padding: 6px 8px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        }
        [data-testid="stTabs"] [role="tab"] {
          border-radius: 10px;
        }
        [data-testid="stTabs"] [role="tabpanel"] {
          background: rgba(255,255,255,0.96);
          border-radius: 12px;
          padding: 14px 16px 6px 16px;
          box-shadow: 0 2px 12px rgba(0,0,0,0.06);
          margin-top: 10px;
        }
        @media (max-width: 900px) {
          .hero-title { font-size: 34px; }
          .hero-subtitle { font-size: 16px; }
        }
        @media (max-width: 520px) {
          .hero-title { font-size: 26px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-inner">
            <div class="hero-icon">📊</div>
            <div class="hero-title">{APP_TITLE_LINE_1}</div>
            <div class="hero-title">{APP_TITLE_LINE_2}</div>
            <div class="hero-subtitle">Nhập liệu, quản lý và thống kê tiêu chuẩn</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "records" not in st.session_state:
        st.session_state.records = load_data()

    records: List[Dict[str, Any]] = st.session_state.records

    tabs = st.tabs(
        [
            "🏥 Tổ chức - Hành chính",
            "🧼 Chống nhiễm khuẩn",
            "💊 Dược - XN-CĐHA",
            "📑 Kế hoạch nghiệp vụ",
            "📈 Thống kê",
            "📋 Dữ liệu",
        ]
    )

    with tabs[0]:
        labels = criteria_label_map()
        sections = [
            (
                "I. Tiêu chuẩn về cơ sở vật chất",
                [
                    ("standard_1", labels["standard_1"], False),
                    ("standard_2", labels["standard_2"], False),
                    (None, "3. Các khoa, phòng, bộ phận chuyên môn:", False),
                    ("standard_3_1", labels["standard_3_1"], False),
                    ("standard_3_2", labels["standard_3_2"], False),
                    ("standard_4", labels["standard_4"], False),
                    ("standard_5", labels["standard_5"], False),
                    ("standard_8", labels["standard_8"], False),
                ],
            ),
            (
                "II. Tiêu chuẩn về quy mô và cơ cấu tổ chức",
                [
                    ("standard_II_1", labels["standard_II_1"], False),
                    ("standard_II_2", labels["standard_II_2"], False),
                    (None, "3. Khoa lâm sàng:", False),
                    ("standard_II_3a", labels["standard_II_3a"], True),
                    ("standard_II_3b", labels["standard_II_3b"], True),
                    ("standard_II_4", labels["standard_II_4"], False),
                    ("standard_II_5", labels["standard_II_5"], False),
                    ("standard_II_6", labels["standard_II_6"], False),
                    ("standard_II_7", labels["standard_II_7"], False),
                    ("standard_II_8", labels["standard_II_8"], False),
                    ("standard_II_9", labels["standard_II_9"], False),
                ],
            ),
            (
                "III. Tiêu chuẩn về nhân sự",
                [
                    ("standard_III_1", labels["standard_III_1"], False),
                    ("standard_III_2", labels["standard_III_2"], False),
                ],
            ),
        ]
        render_form_structured(
            "tochuc",
            "Phòng Tổ chức - Hành chính quản trị",
            "Đánh giá tiêu chuẩn về cơ sở vật chất, quy mô & cơ cấu tổ chức, nhân sự.",
            sections,
        )

    with tabs[1]:
        labels = criteria_label_map()
        sections = [
            (
                "I. Tiêu chuẩn về cơ sở vật chất",
                [
                    (None, "6. Tiêu chuẩn về môi trường:", False),
                    ("ksnk_6_1", labels["ksnk_6_1"], False),
                    ("ksnk_6_2", labels["ksnk_6_2"], False),
                ],
            ),
            (
                "V. Tiêu chuẩn về chuyên môn",
                [
                    ("ksnk_V_5", labels["ksnk_V_5"], False),
                ],
            ),
        ]
        render_form_structured(
            "ksnk",
            "Tổ chống nhiễm khuẩn",
            "Đánh giá tiêu chuẩn về môi trường và kiểm soát nhiễm khuẩn.",
            sections,
        )

    with tabs[2]:
        labels = criteria_label_map()
        sections = [
            (
                "I. Tiêu chuẩn về cơ sở vật chất",
                [
                    (None, "7. Tiêu chuẩn về an toàn bức xạ:", False),
                    ("duoc_7_1", labels["duoc_7_1"], False),
                    ("duoc_7_2", labels["duoc_7_2"], False),
                    ("duoc_7_3", labels["duoc_7_3"], False),
                    ("duoc_7_4", labels["duoc_7_4"], False),
                ],
            ),
            (
                "IV. Tiêu chuẩn về thiết bị y tế",
                [
                    ("duoc_IV_1", labels["duoc_IV_1"], False),
                    ("duoc_IV_2", labels["duoc_IV_2"], False),
                    ("duoc_IV_3", labels["duoc_IV_3"], False),
                    ("duoc_IV_4", labels["duoc_IV_4"], False),
                    ("duoc_IV_5", labels["duoc_IV_5"], False),
                ],
            ),
        ]
        render_form_structured(
            "duoc",
            "Khoa dược - XN-CĐHA",
            "Đánh giá tiêu chuẩn an toàn bức xạ và thiết bị y tế.",
            sections,
        )

    with tabs[3]:
        labels = criteria_label_map()
        sections = [
            (
                "V. Tiêu chuẩn về chuyên môn",
                [
                    ("kehoach_V_1", labels["kehoach_V_1"], False),
                    ("kehoach_V_2", labels["kehoach_V_2"], False),
                    (None, "3. Phổ biến, áp dụng và xây dựng quy trình chuyên môn về khám bệnh, chữa bệnh:", False),
                    ("kehoach_V_3_1", labels["kehoach_V_3_1"], False),
                    ("kehoach_V_3_2", labels["kehoach_V_3_2"], False),
                    ("kehoach_V_3_3", labels["kehoach_V_3_3"], False),
                    ("kehoach_V_3_4", labels["kehoach_V_3_4"], False),
                    ("kehoach_V_3_5", labels["kehoach_V_3_5"], False),
                    (None, "4. Quản lý chất lượng:", False),
                    ("kehoach_V_4_1", labels["kehoach_V_4_1"], False),
                    ("kehoach_V_4_2", labels["kehoach_V_4_2"], False),
                    ("kehoach_V_4_3", labels["kehoach_V_4_3"], False),
                    ("kehoach_V_4_4", labels["kehoach_V_4_4"], False),
                    ("kehoach_V_4_5", labels["kehoach_V_4_5"], False),
                    ("kehoach_V_4_6", labels["kehoach_V_4_6"], False),
                ],
            ),
        ]
        render_form_structured(
            "kehoach",
            "Kế hoạch nghiệp vụ",
            "Đánh giá tiêu chuẩn về chuyên môn.",
            sections,
        )

    with tabs[4]:
        eval_modes = {"tochuc", "ksnk", "duoc", "kehoach"}
        eval_records = [r for r in records if r.get("mode") in eval_modes]

        if not eval_records:
            st.info("Chưa có phiếu đánh giá để thống kê.")
        else:
            by_section, by_type, totals = compute_stats(eval_records)
            total_records = len(eval_records)
            total_answered = totals["co"] + totals["khong"] + totals["na"]
            denom = totals["co"] + totals["khong"]
            ti_le_co = (totals["co"] / denom) * 100 if denom else 0.0
            today = date.today().isoformat()
            today_records = sum(1 for r in eval_records if r.get("date") == today)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Tổng số phiếu đánh giá", total_records)
            m2.metric("Tổng tiêu chí đã đánh giá", total_answered)
            m3.metric("Tỷ lệ “Có”", f"{ti_le_co:.1f}%")
            m4.metric("Phiếu hôm nay", today_records)

            st.divider()
            st.subheader("Thống kê theo nhóm tiêu chuẩn (I–V)")
            sec_df = pd.DataFrame(
                [
                    {"Nhóm": k, "Kết quả": "Có", "Số lượng": by_section[k]["co"]}
                    for k in ["I", "II", "III", "IV", "V"]
                ]
                + [
                    {"Nhóm": k, "Kết quả": "Không", "Số lượng": by_section[k]["khong"]}
                    for k in ["I", "II", "III", "IV", "V"]
                ]
                + [
                    {"Nhóm": k, "Kết quả": "Không áp dụng", "Số lượng": by_section[k]["na"]}
                    for k in ["I", "II", "III", "IV", "V"]
                ]
            )

            chart = (
                alt.Chart(sec_df)
                .mark_bar()
                .encode(
                    x=alt.X("Nhóm:N", sort=["I", "II", "III", "IV", "V"]),
                    y=alt.Y("Số lượng:Q", stack="zero"),
                    color=alt.Color("Kết quả:N", scale=alt.Scale(domain=["Có", "Không", "Không áp dụng"], range=["#28a745", "#dc3545", "#6c757d"])),
                    tooltip=["Nhóm", "Kết quả", "Số lượng"],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, use_container_width=True)

            st.subheader("Thống kê theo loại phiếu")
            type_df = pd.DataFrame(
                [{"Loại phiếu": mode_label(k), "Số phiếu": v} for k, v in by_type.items()]
            )
            st.bar_chart(type_df.set_index("Loại phiếu"))

    with tabs[5]:
        st.subheader("Dữ liệu")
        eval_modes = {"tochuc", "ksnk", "duoc", "kehoach"}
        eval_records = [r for r in records if r.get("mode") in eval_modes]

        c1, c2, c3, c4 = st.columns([2, 1, 2, 1])
        with c1:
            search = st.text_input("Tìm kiếm", placeholder="Chức danh / người đánh giá / ghi chú / kết quả tiêu chí...")
        with c2:
            mode = st.selectbox("Loại phiếu", ["", "tochuc", "ksnk", "duoc", "kehoach"], format_func=lambda x: "Tất cả" if x == "" else mode_label(x))
        with c3:
            crit_map = criteria_label_map()
            crit_options = ["__all__"] + list(crit_map.keys())
            crit = st.selectbox(
                "Tiêu chí",
                crit_options,
                format_func=lambda x: "Tất cả tiêu chí (I–V)" if x == "__all__" else crit_map.get(x, x),
            )
        with c4:
            result = st.selectbox("Kết quả", ["", "Có", "Không", "Không áp dụng"], format_func=lambda x: "Tất cả" if x == "" else x)

        filtered = filter_records(eval_records, search, mode, crit, result)
        df = records_to_df(filtered)

        st.caption(f"Đang hiển thị: {len(filtered)} phiếu")

        if not df.empty:
            st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
            csv = df.drop(columns=["id"]).to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "📥 Xuất CSV theo kết quả tìm kiếm",
                data=csv,
                file_name=f"du_lieu_tim_kiem_{date.today().isoformat()}.csv",
                mime="text/csv",
            )
        else:
            st.info("Không có dữ liệu phù hợp.")

        st.divider()
        st.subheader("Sửa / Xóa phiếu")
        if not eval_records:
            st.caption("Chưa có phiếu để sửa/xóa.")
        else:
            id_to_label = {r["id"]: f"{mode_label(r['mode'])} | {get_chuc_danh(r) or '-'} | {r.get('date','-')} | ID {r['id']}" for r in eval_records}
            selected_id = st.selectbox("Chọn phiếu", [""] + list(id_to_label.keys()), format_func=lambda x: "—" if x == "" else id_to_label[x])
            if selected_id:
                rec = next((r for r in records if r.get("id") == selected_id), None)
                if rec:
                    b1, b2, b3 = st.columns([1, 1, 2])
                    with b1:
                        if st.button("✏️ Sửa", type="primary"):
                            st.session_state[f"edit_id_{rec['mode']}"] = rec["id"]
                            st.success("Đã chuyển sang chế độ sửa. Hãy mở tab tương ứng để chỉnh.")
                    with b2:
                        if st.button("🗑️ Xóa"):
                            delete_record(records, selected_id)
                            save_data(records)
                            st.success("Đã xóa phiếu.")
                            st.rerun()
                    with b3:
                        st.caption("Khi bấm Sửa, bạn qua đúng tab (Tổ chức/Chống NK/Dược/Kế hoạch) để chỉnh và bấm Lưu.")

        with st.expander("⚠️ Xóa tất cả dữ liệu"):
            if st.button("Xóa tất cả", type="secondary"):
                st.session_state.records = []
                save_data([])
                st.success("Đã xóa toàn bộ dữ liệu.")
                st.rerun()


if __name__ == "__main__":
    main()

