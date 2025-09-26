from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional


DATE_FMT = "%Y-%m-%d"


def parse_date(value: str) -> Optional[date]:
    if not value:
        return None
    for fmt in (DATE_FMT, "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.date()
        except ValueError:
            continue
    return None


def format_date(d: Optional[date]) -> str:
    return d.strftime(DATE_FMT) if d else ""


@dataclass
class Xe:
    id: str
    ngay_xuat: Optional[date]
    trang_thai: str
    ghi_chu: str = ""
    ngay_du_kien: Optional[date] = None
    ten_nha_cung_cap: str = ""
    trang_thai_thanh_toan: str = ""
    bien_kiem_soat: str = ""
    lai_xe: str = ""
    sbt_lai_xe: str = ""
    ghi_chu_khac: str = ""

    def to_record(self) -> Dict[str, Any]:
        return {
            "ID": self.id,
            "NgayXuat": format_date(self.ngay_xuat),
            "TrangThai": self.trang_thai,
            "GhiChu": self.ghi_chu,
            "NgayDuKien": format_date(self.ngay_du_kien),
            # The following keys align with Vietnamese headers if present in the sheet
            "Tên nhà cung cấp": self.ten_nha_cung_cap,
            "Trạng thái thanh toán": self.trang_thai_thanh_toan,
            "Biển kiểm soát": self.bien_kiem_soat,
            "Lái xe": self.lai_xe,
            "SBT lái xe": self.sbt_lai_xe,
            "Ghi chú": self.ghi_chu_khac,
        }


@dataclass
class XepHang:
    id: str
    xe_id: str
    bill_id: str
    so_luong: float
    stt: int
    ngay_du_kien: Optional[date]

    def to_record(self) -> Dict[str, Any]:
        return {
            "ID": self.id,
            "Xe": self.xe_id,
            "Bill": self.bill_id,
            "SoLuong": self.so_luong,
            "STT": self.stt,
            "NgayDuKien": format_date(self.ngay_du_kien),
        }

