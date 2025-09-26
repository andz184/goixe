from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

import gspread

from .gsheets import get_or_create_worksheet, open_sheet, find_worksheet_by_alias
from .model import Xe, XepHang, parse_date


XE_HEADERS = [
    "ID",
    "NgayXuat",
    "TrangThai",
    "GhiChu",
    "NgayDuKien",
    "Tên nhà cung cấp",
    "Trạng thái thanh toán",
    "Biển kiểm soát",
    "Lái xe",
    "SBT lái xe",
    "Ghi chú",
]
XEP_HEADERS = ["ID", "Xe", "Bill", "SoLuong", "STT", "NgayDuKien"]


class Repo:
    def __init__(self) -> None:
        self.ss = open_sheet()
        # Auto-detect sheets by aliases
        xe_ws = find_worksheet_by_alias(self.ss, ["Xe", "xe", "Xê", "Xe vận tải"]) or get_or_create_worksheet(self.ss, "Xe", XE_HEADERS)
        xep_ws = find_worksheet_by_alias(self.ss, ["XepHang", "Xếp hàng", "Xếp hàng ", "Xếp hàng xe"]) or get_or_create_worksheet(self.ss, "XepHang", XEP_HEADERS)
        self.ws_xe = xe_ws
        self.ws_xep = xep_ws
        # Bill sheet optional but referenced
        try:
            self.ws_bill = find_worksheet_by_alias(self.ss, ["Bill", "Hóa đơn", "Đơn hàng", "Bill ", "BILL"]) or self.ss.worksheet("Bill")
        except gspread.WorksheetNotFound:
            self.ws_bill = None

    def ensure_schema(self) -> None:
        get_or_create_worksheet(self.ss, "Xe", XE_HEADERS)
        get_or_create_worksheet(self.ss, "XepHang", XEP_HEADERS)

    def create_xe(
        self,
        xe_id: str,
        ngay_xuat_str: Optional[str],
        ghi_chu: str = "",
        trang_thai: str = "Moi",
        ten_nha_cung_cap: str = "",
        trang_thai_thanh_toan: str = "",
        bien_kiem_soat: str = "",
        lai_xe: str = "",
        sbt_lai_xe: str = "",
        ghi_chu_khac: str = "",
    ) -> Xe:
        ngay_xuat = parse_date(ngay_xuat_str) if ngay_xuat_str else None
        ngay_du_kien = (ngay_xuat + timedelta(days=3)) if ngay_xuat else None
        xe = Xe(
            id=xe_id,
            ngay_xuat=ngay_xuat,
            trang_thai=trang_thai,
            ghi_chu=ghi_chu,
            ngay_du_kien=ngay_du_kien,
            ten_nha_cung_cap=ten_nha_cung_cap,
            trang_thai_thanh_toan=trang_thai_thanh_toan,
            bien_kiem_soat=bien_kiem_soat,
            lai_xe=lai_xe,
            sbt_lai_xe=sbt_lai_xe,
            ghi_chu_khac=ghi_chu_khac,
        )
        from .gsheets import upsert_record

        upsert_record(self.ws_xe, "ID", xe.to_record())
        return xe

    def add_xep(self, xe_id: str, bill_id: str, so_luong: float, stt: int, ngay_du_kien_str: Optional[str]) -> XepHang:
        ngay_du_kien = parse_date(ngay_du_kien_str) if ngay_du_kien_str else None
        if not ngay_du_kien:
            # derive from Xe.NgayXuat + 3
            xe = self.get_xe(xe_id)
            if xe and xe.ngay_du_kien:
                ngay_du_kien = xe.ngay_du_kien
        xh = XepHang(id=str(uuid.uuid4())[:8], xe_id=xe_id, bill_id=bill_id, so_luong=so_luong, stt=stt, ngay_du_kien=ngay_du_kien)
        from .gsheets import append_record

        append_record(self.ws_xep, xh.to_record())
        return xh

    def get_xe(self, xe_id: str) -> Optional[Xe]:
        records = self.ws_xe.get_all_records()
        for r in records:
            if str(r.get("ID")) == str(xe_id):
                return Xe(
                    id=str(r.get("ID")),
                    ngay_xuat=parse_date(r.get("NgayXuat")),
                    trang_thai=str(r.get("TrangThai")),
                    ghi_chu=str(r.get("GhiChu", "")),
                    ngay_du_kien=parse_date(r.get("NgayDuKien")),
                    ten_nha_cung_cap=str(r.get("Tên nhà cung cấp", "")),
                    trang_thai_thanh_toan=str(r.get("Trạng thái thanh toán", "")),
                    bien_kiem_soat=str(r.get("Biển kiểm soát", "")),
                    lai_xe=str(r.get("Lái xe", "")),
                    sbt_lai_xe=str(r.get("SBT lái xe", "")),
                    ghi_chu_khac=str(r.get("Ghi chú", "")),
                )
        return None

    def view_xe(self, xe_id: str):
        xe = self.get_xe(xe_id)
        items = self.get_xep_for_xe(xe_id)
        items.sort(key=lambda r: int(r.get("STT") or 0))
        return xe, items

    def view_unassigned(self):
        # If Bill sheet exists, compute remaining quantities vs XepHang
        if not self.ws_bill:
            return []
        bills = self.ws_bill.get_all_records()
        xeps = self.ws_xep.get_all_records()

        # detect quantity header in Bill sheet
        bill_headers = self.get_bill_headers() if hasattr(self, 'get_bill_headers') else self.ws_bill.row_values(1)
        qty_candidates = [
            "SoLuong", "Số lượng", "Số kiện", "So Kien", "SoKien", "Soluong",
        ]
        qty_col = next((h for h in qty_candidates if h in bill_headers), None)

        bill_id_to_total = {}
        bill_id_to_assigned = {}
        for b in bills:
            bill_id = str(b.get("ID"))
            total = 0.0
            if qty_col is not None:
                total = float(b.get(qty_col, 0) or 0)
            bill_id_to_total[bill_id] = total
            bill_id_to_assigned[bill_id] = 0.0
        for x in xeps:
            bid = str(x.get("Bill"))
            bill_id_to_assigned[bid] = bill_id_to_assigned.get(bid, 0.0) + float(x.get("SoLuong", 0) or 0)

        pending = []
        for bill_id, total in bill_id_to_total.items():
            assigned = bill_id_to_assigned.get(bill_id, 0.0)
            if assigned < total:
                pending.append({
                    "BillID": bill_id,
                    "Total": total,
                    "Assigned": assigned,
                    "Remaining": total - assigned,
                })
        return pending

    # ---- XepHang optimized retrieval by Xe ----
    _xep_headers_cache: List[str] | None = None

    def get_xep_headers(self) -> List[str]:
        if self._xep_headers_cache:
            return self._xep_headers_cache
        self._xep_headers_cache = self.ws_xep.row_values(1)
        return self._xep_headers_cache

    def get_xep_for_xe(self, xe_id: str) -> List[dict]:
        headers = self.get_xep_headers()
        try:
            xe_col_index = headers.index("Xe") + 1  # 1-based
        except ValueError:
            # Fallback: full scan (rare)
            rows = self.ws_xep.get_all_records()
            return [r for r in rows if str(r.get("Xe")) == str(xe_id)]

        xe_col = self.ws_xep.col_values(xe_col_index)
        match_rows = [idx for idx, val in enumerate(xe_col[1:], start=2) if str(val) == str(xe_id)]
        if not match_rows:
            return []
        last_col_letter = self._col_index_to_letter(len(headers))
        # Batch get all needed rows in one API call
        ranges = [f"A{r}:{last_col_letter}{r}" for r in match_rows]
        batch_vals = self.ws_xep.batch_get(ranges)
        results: List[dict] = []
        for row in batch_vals:
            row0 = row[0] if row else []
            merged = {headers[i]: (row0[i] if i < len(row0) else "") for i in range(len(headers))}
            results.append(merged)
        return results


    # ---- Fast pagination helpers ----
    _bill_headers_cache: List[str] | None = None

    def _col_index_to_letter(self, idx: int) -> str:
        letters = ""
        while idx:
            idx, rem = divmod(idx - 1, 26)
            letters = chr(65 + rem) + letters
        return letters

    def get_bill_headers(self) -> List[str]:
        if not self.ws_bill:
            return []
        if self._bill_headers_cache:
            return self._bill_headers_cache
        headers = self.ws_bill.row_values(1)
        self._bill_headers_cache = headers
        return headers

    def get_bills_page(self, page: int = 1, page_size: int = 20) -> tuple[List[dict], int, List[str]]:
        if not self.ws_bill:
            return [], 0, []
        headers = self.get_bill_headers()
        if not headers:
            return [], 0, []
        total_rows = max(0, len(self.ws_bill.col_values(1)) - 1)
        start_row = max(2, 2 + (page - 1) * page_size)
        end_row = max(start_row, start_row + page_size - 1)
        last_col_letter = self._col_index_to_letter(len(headers))
        rng = f"A{start_row}:{last_col_letter}{end_row}"
        values = self.ws_bill.get(rng)
        rows: List[dict] = []
        for row in values:
            merged = {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
            if any(str(merged.get(h, "")).strip() for h in headers):
                rows.append(merged)
        return rows, total_rows, headers

    def get_xe_headers(self) -> List[str]:
        return self.ws_xe.row_values(1)

    def get_xe_page(self, page: int = 1, page_size: int = 20) -> tuple[List[dict], int, List[str]]:
        headers = self.get_xe_headers()
        total_rows = max(0, len(self.ws_xe.col_values(1)) - 1)
        start_row = max(2, 2 + (page - 1) * page_size)
        end_row = max(start_row, start_row + page_size - 1)
        last_col_letter = self._col_index_to_letter(len(headers))
        rng = f"A{start_row}:{last_col_letter}{end_row}"
        values = self.ws_xe.get(rng)
        rows: List[dict] = []
        for row in values:
            merged = {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
            if any(str(merged.get(h, "")).strip() for h in headers):
                rows.append(merged)
        return rows, total_rows, headers

