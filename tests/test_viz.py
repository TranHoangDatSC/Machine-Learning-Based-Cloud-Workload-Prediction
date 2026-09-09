"""Kiểm `cwp.viz.xuat` — bộ xuất hình dùng chung của các script `fig_*`.

Chạy:  pytest tests/test_viz.py -v

Không kiểm hình vẽ ra có đẹp không — cái đó phải mở ảnh ra nhìn. Kiểm đúng cái hợp
đồng mà ba script `fig_*.py` dựa vào, và đó là những thứ hỏng lặng lẽ:

- Mỗi panel ra **đúng một tệp**, tên đúng như đã khai. Sai tên thì bài báo dẫn hình
  không tồn tại.
- Mỗi tệp ảnh chứa **đúng một hình**. Đây là lý do cả bộ được viết lại; nếu một tệp
  lại chứa hai axes thì mục đích "dán thẳng vào bài" mất.
- PDF có **đủ số trang**: một trang diễn giải cộng mỗi panel một trang. Thiếu trang
  nghĩa là mất hình mà không ai báo.
- Hàm vẽ của panel được gọi **hai lần** (một cho ảnh, một cho PDF) nên nó phải chịu
  được việc gọi lại trên một `Axes` mới. Một hàm vẽ giữ trạng thái sẽ hỏng ở đây.
"""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cwp.viz import xuat

# `pypdf` KHÔNG nằm trong requirements.txt (QĐ-007 ghim đúng 12 gói). Test đếm số
# trang PDF vì thế tự bỏ qua khi thiếu nó, thay vì kéo thêm một phụ thuộc chỉ để
# kiểm một con số.


def _panel(ten="01_thu", tieu_de="Hình thử"):
    return xuat.Panel(ten, tieu_de, (4.0, 3.0), lambda ax: ax.plot([0, 1], [0, 1]))


def test_moi_panel_ra_dung_mot_tep(tmp_path):
    ps = [_panel("01_a", "A"), _panel("02_b", "B"), _panel("03_c", "C")]
    ra = xuat.luu_tung_panel(ps, tmp_path, dpi=50)

    assert len(ra) == 3
    assert [p.name for p in ra] == ["01_a.png", "02_b.png", "03_c.png"]
    assert all(p.exists() and p.stat().st_size > 0 for p in ra)


def test_moi_tep_chua_dung_mot_hinh(tmp_path):
    """Lý do tồn tại của cả bộ xuất này: một tệp ảnh, một hình."""
    ghi_nhan = []

    def ve(ax):
        ghi_nhan.append(ax.get_figure())
        ax.plot([0, 1], [1, 0])

    xuat.luu_tung_panel([xuat.Panel("01_x", "X", (4.0, 3.0), ve)], tmp_path, dpi=50)

    assert len(ghi_nhan) == 1
    assert len(ghi_nhan[0].axes) == 1, "tệp ảnh chứa nhiều hơn một hình"


def test_tieu_de_lay_tu_panel_khong_phai_tu_ham_ve(tmp_path):
    """Hàm vẽ không tự đặt tiêu đề — `luu_tung_panel` đặt, nên đổi tên là một chỗ."""
    giu = {}

    def ve(ax):
        giu["ax"] = ax
        ax.plot([0, 1], [0, 1])

    xuat.luu_tung_panel([xuat.Panel("01_x", "Tiêu đề mong đợi", (4.0, 3.0), ve)],
                        tmp_path, dpi=50)

    assert giu["ax"].get_title(loc="left") == "Tiêu đề mong đợi"


def test_pdf_du_so_trang(tmp_path):
    """Một trang diễn giải + mỗi panel một trang."""
    pytest.importorskip("pypdf")
    from pypdf import PdfReader as R

    ps = [_panel("01_a", "A"), _panel("02_b", "B")]
    dich = xuat.gop_pdf(ps, tmp_path / "t.pdf", tieu_de="T", phu="câu phụ",
                        dien_giai=[("Mục", "nội dung")])

    assert dich.exists()
    assert len(R(str(dich)).pages) == 1 + len(ps)


def test_ham_ve_duoc_goi_lai_cho_pdf(tmp_path):
    """Panel bị vẽ hai lần — một cho ảnh, một cho PDF. Không được giữ trạng thái."""
    dem = {"n": 0}

    def ve(ax):
        dem["n"] += 1
        ax.plot([0, 1], [0, 1])

    xuat.xuat_bo_hinh([xuat.Panel("01_x", "X", (4.0, 3.0), ve)], tmp_path, "t.pdf",
                      tieu_de="T", phu="", dien_giai=[], dpi=50)

    assert dem["n"] == 2


def test_xuat_bo_hinh_tra_ve_ca_anh_lan_pdf(tmp_path):
    anh, pdf = xuat.xuat_bo_hinh(
        [_panel("01_a", "A"), _panel("02_b", "B")], tmp_path, "bo.pdf",
        tieu_de="T", phu="p", dien_giai=[("a", "b")],
        chu_thich={"01_a": "chú thích của hình một"}, dpi=50)

    assert [p.name for p in anh] == ["01_a.png", "02_b.png"]
    assert pdf.name == "bo.pdf"
    assert all(p.exists() for p in list(anh) + [pdf])


def test_tu_tao_thu_muc_neu_chua_co(tmp_path):
    sau = tmp_path / "chua" / "co" / "gd2"
    ra = xuat.luu_tung_panel([_panel()], sau, dpi=50)

    assert sau.is_dir()
    assert ra[0].exists()


def test_khong_de_lai_figure_mo(tmp_path):
    """Rò figure làm matplotlib cảnh báo và ngốn bộ nhớ khi sinh nhiều hình."""
    plt.close("all")
    xuat.xuat_bo_hinh([_panel("01_a", "A"), _panel("02_b", "B")], tmp_path, "t.pdf",
                      tieu_de="T", phu="p", dien_giai=[("a", "b")], dpi=50)

    assert plt.get_fignums() == []
