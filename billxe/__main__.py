from __future__ import annotations

import typer
from rich import print
from rich.table import Table

from .repo import Repo

app = typer.Typer(add_completion=False)


@app.command()
def init():
    """Ensure required sheets and headers exist."""
    repo = Repo()
    repo.ensure_schema()
    print("[green]Initialized schema for Xe and XepHang[/green]")


xe_app = typer.Typer()
xep_app = typer.Typer()
view_app = typer.Typer()
app.add_typer(xe_app, name="xe")
app.add_typer(xep_app, name="xep")
app.add_typer(view_app, name="view")


@xe_app.command("create")
def xe_create(
    code: str = typer.Option(..., "--code", help="Xe ID/Code"),
    ngay_xuat: str = typer.Option(None, "--ngay_xuat", help="YYYY-MM-DD"),
    ghi_chu: str = typer.Option("", "--ghi_chu"),
    trang_thai: str = typer.Option("Moi", "--trang_thai"),
    ten_ncc: str = typer.Option("", "--ten_ncc"),
    tt_thanh_toan: str = typer.Option("", "--tt_thanh_toan"),
    bien_ks: str = typer.Option("", "--bien_ks"),
    lai_xe: str = typer.Option("", "--lai_xe"),
    sbt_lai_xe: str = typer.Option("", "--sbt_lai_xe"),
    ghi_chu_khac: str = typer.Option("", "--ghi_chu_khac"),
):
    repo = Repo()
    xe = repo.create_xe(
        code,
        ngay_xuat,
        ghi_chu,
        trang_thai,
        ten_nha_cung_cap=ten_ncc,
        trang_thai_thanh_toan=tt_thanh_toan,
        bien_kiem_soat=bien_ks,
        lai_xe=lai_xe,
        sbt_lai_xe=sbt_lai_xe,
        ghi_chu_khac=ghi_chu_khac,
    )
    print({"created": xe.id})


@xep_app.command("add")
def xep_add(
    xe_id: str = typer.Option(..., "--xe_id"),
    bill_id: str = typer.Option(..., "--bill_id"),
    so_luong: float = typer.Option(..., "--so_luong"),
    stt: int = typer.Option(1, "--stt"),
    ngay_du_kien: str = typer.Option(None, "--ngay_du_kien"),
):
    repo = Repo()
    xh = repo.add_xep(xe_id, bill_id, so_luong, stt, ngay_du_kien)
    print({"xep_id": xh.id})


@view_app.command("xe")
def view_xe(xe_id: str = typer.Option(..., "--xe_id")):
    repo = Repo()
    xe, items = repo.view_xe(xe_id)
    if not xe:
        print("[red]Xe not found[/red]")
        raise typer.Exit(code=1)
    table = Table(title=f"Xe {xe.id} - TrangThai: {xe.trang_thai}")
    table.add_column("STT")
    table.add_column("Bill")
    table.add_column("SoLuong")
    table.add_column("NgayDuKien")
    for r in items:
        table.add_row(str(r.get("STT")), str(r.get("Bill")), str(r.get("SoLuong")), str(r.get("NgayDuKien")))
    print(table)


@view_app.command("unassigned")
def view_unassigned():
    repo = Repo()
    rows = repo.view_unassigned()
    if not rows:
        print("[yellow]No Bill sheet or no pending bills[/yellow]")
        return
    table = Table(title="Bills pending or partially assigned")
    table.add_column("BillID")
    table.add_column("Total")
    table.add_column("Assigned")
    table.add_column("Remaining")
    for r in rows:
        table.add_row(str(r["BillID"]), str(r["Total"]), str(r["Assigned"]), str(r["Remaining"]))
    print(table)


if __name__ == "__main__":
    app()

