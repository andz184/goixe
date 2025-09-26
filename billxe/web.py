from __future__ import annotations

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Optional

from .repo import Repo


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR.parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

app = FastAPI(title="BillXe")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    repo = Repo()
    xe_rows = repo.ws_xe.get_all_records()
    template = env.get_template("index.html")
    return template.render(xe_rows=xe_rows)


@app.get("/xe/new", response_class=HTMLResponse)
def xe_new(request: Request):
    template = env.get_template("xe_new.html")
    return template.render()


@app.post("/xe/create")
async def xe_create(
    code: str = Form(None),
    ngay_xuat: Optional[str] = Form(None),
    ghi_chu: str = Form(""),
    ten_ncc: str = Form(""),
    tt_thanh_toan: str = Form(""),
    bien_ks: str = Form(""),
    lai_xe: str = Form(""),
    sbt_lai_xe: str = Form(""),
    ghi_chu_khac: str = Form(""),
    request: Request = None,
):
    # Allow JSON body to avoid reload
    if code is None:
        data = await request.json()
        code = data.get("code")
        ngay_xuat = data.get("ngay_xuat")
        ghi_chu = data.get("ghi_chu", "")
        ten_ncc = data.get("ten_ncc", "")
        tt_thanh_toan = data.get("tt_thanh_toan", "")
        bien_ks = data.get("bien_ks", "")
        lai_xe = data.get("lai_xe", "")
        sbt_lai_xe = data.get("sbt_lai_xe", "")
        ghi_chu_khac = data.get("ghi_chu_khac", "")
        repo = Repo()
        xe = repo.create_xe(
            code,
            ngay_xuat,
            ghi_chu,
            ten_nha_cung_cap=ten_ncc,
            trang_thai_thanh_toan=tt_thanh_toan,
            bien_kiem_soat=bien_ks,
            lai_xe=lai_xe,
            sbt_lai_xe=sbt_lai_xe,
            ghi_chu_khac=ghi_chu_khac,
        )
        return JSONResponse({"ok": True, "xe_id": xe.id})
    else:
        repo = Repo()
        xe = repo.create_xe(
            code,
            ngay_xuat,
            ghi_chu,
            ten_nha_cung_cap=ten_ncc,
            trang_thai_thanh_toan=tt_thanh_toan,
            bien_kiem_soat=bien_ks,
            lai_xe=lai_xe,
            sbt_lai_xe=sbt_lai_xe,
            ghi_chu_khac=ghi_chu_khac,
        )
        return RedirectResponse(url=f"/xe/{code}", status_code=303)


@app.get("/xe/{xe_id}", response_class=HTMLResponse)
def xe_detail(request: Request, xe_id: str):
    repo = Repo()
    xe, items = repo.view_xe(xe_id)
    template = env.get_template("xe_detail.html")
    return template.render(xe=xe, items=items)


@app.post("/xep/add")
async def xep_add(
    xe_id: str = Form(None),
    bill_id: str = Form(None),
    so_luong: float = Form(None),
    stt: int = Form(1),
    request: Request = None,
):
    repo = Repo()
    # Allow JSON body to avoid reload
    if xe_id is None:
        data = await request.json()
        xe_id = data.get("xe_id")
        bill_id = data.get("bill_id")
        so_luong = float(data.get("so_luong"))
        stt = int(data.get("stt", 1))
        xh = repo.add_xep(xe_id, bill_id, so_luong, stt, None)
        return JSONResponse({"ok": True, "xep_id": xh.id})
    else:
        xh = repo.add_xep(xe_id, bill_id, so_luong, stt, None)
        return RedirectResponse(url=f"/xe/{xe_id}", status_code=303)


@app.get("/unassigned", response_class=HTMLResponse)
def unassigned(request: Request):
    repo = Repo()
    rows = repo.view_unassigned()
    template = env.get_template("unassigned.html")
    return template.render(rows=rows)


@app.get("/bills", response_class=HTMLResponse)
def list_bills(request: Request):
    template = env.get_template("bills.html")
    return template.render(bills=[])


@app.get("/api/bills")
def api_bills(page: int = 1, page_size: int = 20):
    repo = Repo()
    rows, total, headers = repo.get_bills_page(page=page, page_size=page_size)
    return JSONResponse({"data": rows, "total": total, "headers": headers})


@app.get("/api/xe")
def api_xe(page: int = 1, page_size: int = 20):
    repo = Repo()
    rows, total, headers = repo.get_xe_page(page=page, page_size=page_size)
    return JSONResponse({"data": rows, "total": total, "headers": headers})


