"""Sinh bản Word của bản thảo từ Markdown, dùng CHÍNH template HJS của tạp chí.

    python scripts/tao_docx.py
    python scripts/tao_docx.py --vao paper/ban-thao-v3.md --ra paper/ban-thao-v3.docx

Không cần pandoc hay python-docx: `.docx` là một tệp zip chứa XML. Script mở
`paper/sample/HJS@Template-OTH.docx`, **giữ nguyên** styles, numbering, header, lề trang,
rồi thay phần thân `word/document.xml` bằng nội dung sinh từ Markdown.

Cú pháp Markdown được hiểu:

| Dòng | Style HJS |
|---|---|
| `::tieu-de::`, `::en-tieu-de::` | Title |
| `::tac-gia::`, `::en-tac-gia::` | Subtitle |
| `::co-quan::`, `::email::` | đoạn canh giữa, cỡ 9 |
| `::tom-tat::`, `::tu-khoa::`, `::abstract::`, `::keywords::`, `::tieu-su::` | Abstract (phần trước dấu — in đậm) |
| `#`, `##`, `###`, `####` | Heading1–4 (template tự đánh I., A., 1., a)) |
| `::hinh:: đường-dẫn \\| chú thích \\| rộng-cm` | ảnh + Figure (template tự đánh "Hình N.") |
| `::bang:: chú thích` rồi các dòng `\\| … \\|` | Table (tự đánh "Bảng N.") + bảng |
| `::cong-thuc::` | đoạn canh giữa, nghiêng |
| `::tltk::` | reference |
| `::trang-moi::` | ngắt trang |
| `- mục`, `  - mục con` | List Paragraph |
| `1. mục` | đoạn thụt lề, giữ số |
| đoạn thường | Body Text, canh đều |

Trong dòng: `**đậm**`, `*nghiêng*`. Đoạn `⟦…⟧` được tô vàng để nhóm tác giả thấy chỗ cần
điền.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import zipfile
from pathlib import Path
from xml.dom import minidom

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
MAU = ROOT / "paper" / "sample" / "HJS@Template-OTH.docx"
RONG_VUNG_CHU = 9582            # twip: khổ 11624 trừ hai lề 1021
TIEU_DE_NGAN = "HỌC MÁY DỰ ĐOÁN TẢI CPU TRÊN ĐÁM MÂY"
TAC_GIA_HEADER = "Trần Hoàng Đạt, Trần Hoàng Phát, Lương Trần Ngọc Khiết"


# --------------------------------------------------------------- chữ trong dòng

def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def runs(text: str, rpr: str = "") -> str:
    """`**đậm**`, `*nghiêng*`, `⟦…⟧` → các `w:r`. `rpr` là thuộc tính chung."""
    out = []
    for phan in re.split(r"(⟦[^⟧]*⟧)", text):
        if not phan:
            continue
        to = "<w:highlight w:val=\"yellow\"/>" if phan.startswith("⟦") else ""
        for m in re.finditer(r"\*\*(.+?)\*\*|\*(.+?)\*|([^*]+|\*)", phan):
            if m.group(1) is not None:
                t, them = m.group(1), "<w:b/>"
            elif m.group(2) is not None:
                t, them = m.group(2), "<w:i/>"
            else:
                t, them = m.group(3), ""
            pr = f"<w:rPr>{rpr}{them}{to}</w:rPr>" if (rpr or them or to) else ""
            out.append(f"<w:r>{pr}<w:t xml:space=\"preserve\">{esc(t)}</w:t></w:r>")
    return "".join(out)


def doan(text: str, style: str | None = None, ppr: str = "", rpr: str = "") -> str:
    s = f"<w:pStyle w:val=\"{style}\"/>" if style else ""
    return f"<w:p><w:pPr>{s}{ppr}</w:pPr>{runs(text, rpr)}</w:p>"


def doan_dam_dau(text: str, style: str) -> str:
    """`TÓM TẮT— nội dung`: phần trước và cả dấu — in đậm."""
    i = text.find("—")
    if i < 0:
        return doan(text, style, "<w:jc w:val=\"both\"/>")
    return (f"<w:p><w:pPr><w:pStyle w:val=\"{style}\"/><w:jc w:val=\"both\"/></w:pPr>"
            f"{runs('**' + text[:i + 1] + '**')}{runs(text[i + 1:])}</w:p>")


# ---------------------------------------------------------------------- ảnh

def kich_thuoc_png(p: Path) -> tuple[int, int]:
    b = p.read_bytes()[:24]
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{p} không phải PNG")
    return struct.unpack(">II", b[16:24])


def anh(rid: str, stt: int, p: Path, rong_cm: float) -> str:
    w, h = kich_thuoc_png(p)
    cx = int(rong_cm * 360000)
    cy = int(cx * h / w)
    return (
        "<w:p><w:pPr><w:pStyle w:val=\"BodyText\"/><w:keepNext/><w:spacing w:before=\"120\" "
        "w:after=\"0\"/><w:jc w:val=\"center\"/></w:pPr><w:r><w:rPr><w:noProof/></w:rPr>"
        f"<w:drawing><wp:inline distT=\"0\" distB=\"0\" distL=\"0\" distR=\"0\">"
        f"<wp:extent cx=\"{cx}\" cy=\"{cy}\"/><wp:docPr id=\"{1000 + stt}\" name=\"Hinh {stt}\"/>"
        "<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a=\"http://schemas.openxmlformats.org/"
        "drawingml/2006/main\" noChangeAspect=\"1\"/></wp:cNvGraphicFramePr>"
        "<a:graphic xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\">"
        "<a:graphicData uri=\"http://schemas.openxmlformats.org/drawingml/2006/picture\">"
        "<pic:pic xmlns:pic=\"http://schemas.openxmlformats.org/drawingml/2006/picture\">"
        f"<pic:nvPicPr><pic:cNvPr id=\"{1000 + stt}\" name=\"{esc(p.name)}\"/><pic:cNvPicPr/>"
        f"</pic:nvPicPr><pic:blipFill><a:blip r:embed=\"{rid}\"/><a:stretch><a:fillRect/>"
        f"</a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x=\"0\" y=\"0\"/>"
        f"<a:ext cx=\"{cx}\" cy=\"{cy}\"/></a:xfrm><a:prstGeom prst=\"rect\"><a:avLst/>"
        "</a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>"
        "</w:r></w:p>")


# ---------------------------------------------------------------------- bảng

def bang(dong_md: list[str]) -> str:
    hang = [[c.strip() for c in d.strip().strip("|").split("|")] for d in dong_md
            if not re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?", d.strip())]
    n = max(len(h) for h in hang)
    col = RONG_VUNG_CHU // n
    vien = "".join(f"<w:{k} w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
                   for k in ("top", "left", "bottom", "right", "insideH", "insideV"))
    xml = [f"<w:tbl><w:tblPr><w:tblW w:w=\"5000\" w:type=\"pct\"/><w:jc w:val=\"center\"/>"
           f"<w:tblBorders>{vien}</w:tblBorders><w:tblCellMar><w:left w:w=\"60\" w:type=\"dxa\"/>"
           f"<w:right w:w=\"60\" w:type=\"dxa\"/></w:tblCellMar></w:tblPr><w:tblGrid>"
           + "".join(f"<w:gridCol w:w=\"{col}\"/>" for _ in range(n)) + "</w:tblGrid>"]
    for i, h in enumerate(hang):
        tr = "<w:trPr><w:tblHeader/></w:trPr>" if i == 0 else ""
        o = []
        for j in range(n):
            t = h[j] if j < len(h) else ""
            dam = "<w:b/>" if i == 0 else ""
            o.append("<w:tc><w:tcPr><w:tcW w:w=\"0\" w:type=\"auto\"/></w:tcPr>"
                     + doan(t, "BodyText", "<w:spacing w:before=\"20\" w:after=\"20\"/>"
                            "<w:ind w:left=\"0\" w:firstLine=\"0\"/><w:jc w:val=\"left\"/>",
                            f"<w:sz w:val=\"17\"/>{dam}") + "</w:tc>")
        xml.append(f"<w:tr>{tr}{''.join(o)}</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml) + doan("", "BodyText", "<w:spacing w:after=\"60\"/>")


# ------------------------------------------------------------------ phân tích

def dung_than(md: str, goc: Path) -> tuple[str, list[tuple[str, Path]]]:
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    dong = md.split("\n")
    ra: list[str] = []
    anh_ds: list[tuple[str, Path]] = []
    doan_cho: list[str] = []

    def xa_doan():
        if doan_cho:
            ra.append(doan(" ".join(x.strip() for x in doan_cho), "BodyText",
                           "<w:jc w:val=\"both\"/>"))
            doan_cho.clear()

    i = 0
    while i < len(dong):
        d = dong[i].rstrip()
        s = d.strip()
        m = re.match(r"^::([a-z-]+)::\s*(.*)$", s)
        if not s:
            xa_doan()
        elif m:
            xa_doan()
            the, nd = m.group(1), m.group(2)
            if the in ("tieu-de", "en-tieu-de"):
                ra.append(doan(nd, "Title"))
            elif the in ("tac-gia", "en-tac-gia"):
                ra.append(doan(nd, "Subtitle"))
            elif the == "co-quan":
                ra.append(doan(nd, None, "<w:jc w:val=\"center\"/>",
                               "<w:rFonts w:ascii=\"Cambria\" w:hAnsi=\"Cambria\"/><w:sz w:val=\"18\"/>"))
            elif the == "email":
                ra.append(doan(nd, None, "<w:spacing w:before=\"60\" w:after=\"120\"/><w:jc w:val=\"center\"/>",
                               "<w:rFonts w:ascii=\"Cambria\" w:hAnsi=\"Cambria\"/><w:i/><w:sz w:val=\"18\"/>"))
            elif the in ("tom-tat", "tu-khoa", "abstract", "keywords"):
                ra.append(doan_dam_dau(nd, "Abstract"))
            elif the == "tieu-su":
                ra.append(doan(nd, "Abstract", "<w:jc w:val=\"both\"/>"))
            elif the == "cong-thuc":
                ra.append(doan(nd, "BodyText", "<w:spacing w:before=\"60\" w:after=\"120\"/>"
                                               "<w:jc w:val=\"center\"/>", "<w:i/>"))
            elif the == "tltk":
                ra.append(doan(nd, "reference", "<w:jc w:val=\"both\"/><w:spacing w:after=\"40\"/>"))
            elif the == "trang-moi":
                ra.append("<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>")
            elif the == "hinh":
                duong, cap, rong = [x.strip() for x in nd.split("|")]
                p = goc / duong
                if not p.exists():
                    raise SystemExit(f"Thiếu ảnh {p}")
                rid = f"rIdHinh{len(anh_ds) + 1}"
                anh_ds.append((rid, p))
                ra.append(anh(rid, len(anh_ds), p, float(rong)))
                ra.append(doan(cap, "Figure"))
            elif the == "bang":
                ra.append(doan(nd, "Table", "<w:keepNext/>"))
                i += 1
                while i < len(dong) and not dong[i].strip():
                    i += 1
                khoi = []
                while i < len(dong) and dong[i].strip().startswith("|"):
                    khoi.append(dong[i])
                    i += 1
                if not khoi:
                    raise SystemExit(f"::bang:: '{nd}' không có bảng theo sau")
                ra.append(bang(khoi))
                continue
            else:
                raise SystemExit(f"Thẻ lạ ::{the}::")
        elif s.startswith("#"):
            xa_doan()
            muc = len(s) - len(s.lstrip("#"))
            ra.append(doan(s[muc:].strip(), f"Heading{min(muc, 4)}"))
        elif re.match(r"^\s*- ", d):
            xa_doan()
            cap_do = 1 if d.startswith("  ") else 0
            ra.append(doan(s[2:], "ListParagraph",
                           f"<w:numPr><w:ilvl w:val=\"{cap_do}\"/><w:numId w:val=\"2\"/></w:numPr>"
                           "<w:jc w:val=\"both\"/>"))
        elif re.match(r"^\d+\. ", s):
            xa_doan()
            ra.append(doan(s, "BodyText", "<w:ind w:left=\"567\" w:hanging=\"283\"/>"
                                          "<w:jc w:val=\"both\"/>"))
        else:
            doan_cho.append(s)
        i += 1
    xa_doan()
    return "".join(ra), anh_ds


def sua_header(xml: str, moi: str, giu_so: bool) -> str:
    """Thay chữ của header, giữ nguyên các `w:t` chỉ chứa số trang."""
    da_dat = False

    def f(m):
        nonlocal da_dat
        t = m.group(2)
        if giu_so and re.fullmatch(r"\s*\d*\s*", t):
            return m.group(0)
        if not da_dat:
            da_dat = True
            return f"{m.group(1)}{esc(moi)}</w:t>"
        return f"{m.group(1)}</w:t>"
    return re.sub(r"(<w:t(?: [^>]*)?>)([^<]*)</w:t>", f, xml)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--vao", default="paper/ban-thao-v3.md")
    ap.add_argument("--ra", default="paper/ban-thao-v3.docx")
    a = ap.parse_args()
    vao, ra = ROOT / a.vao, ROOT / a.ra

    than, anh_ds = dung_than(vao.read_text(encoding="utf-8"), ROOT)
    z = zipfile.ZipFile(MAU)
    doc = z.read("word/document.xml").decode("utf-8")
    mo = doc[:doc.index("<w:body>") + len("<w:body>")]
    sect = re.findall(r"<w:sectPr.*?</w:sectPr>", doc, flags=re.S)[-1]
    moi_doc = mo + than + sect + "</w:body></w:document>"

    rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    them = "".join(f"<Relationship Id=\"{rid}\" Type=\"http://schemas.openxmlformats.org/"
                   f"officeDocument/2006/relationships/image\" Target=\"media/{p.stem}.png\"/>"
                   for rid, p in anh_ds)
    rels = rels.replace("</Relationships>", them + "</Relationships>")

    ra.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ra, "w", zipfile.ZIP_DEFLATED) as out:
        for item in z.infolist():
            ten = item.filename
            if ten == "word/document.xml":
                data = moi_doc.encode("utf-8")
            elif ten == "word/_rels/document.xml.rels":
                data = rels.encode("utf-8")
            elif ten == "word/header1.xml":
                data = sua_header(z.read(ten).decode("utf-8"), TIEU_DE_NGAN, True).encode("utf-8")
            elif ten == "word/header2.xml":
                data = sua_header(z.read(ten).decode("utf-8"), TAC_GIA_HEADER, True).encode("utf-8")
            elif ten.startswith("word/media/"):
                continue          # ảnh minh hoạ của template, không dùng nữa
            else:
                data = z.read(ten)
            out.writestr(item, data)
        for _, p in anh_ds:
            out.write(p, f"word/media/{p.stem}.png")

    # Bỏ quan hệ tới ảnh cũ của template: đã không chép tệp, nên phải gỡ cả tham chiếu.
    _go_anh_cu(ra, {f"media/{p.stem}.png" for _, p in anh_ds})
    _kiem(ra)
    print(f"Đã ghi {ra.relative_to(ROOT)} — {len(anh_ds)} hình, "
          f"{than.count('<w:tbl>')} bảng, {than.count('<w:p>')} đoạn")
    return 0


def _go_anh_cu(p: Path, giu: set[str]) -> None:
    z = zipfile.ZipFile(p)
    muc = {i.filename: z.read(i.filename) for i in z.infolist()}
    infos = {i.filename: i for i in z.infolist()}
    z.close()
    rels = muc["word/_rels/document.xml.rels"].decode("utf-8")
    rels = re.sub(r"<Relationship [^>]*Target=\"(media/[^\"]+)\"[^>]*/>",
                  lambda m: m.group(0) if m.group(1) in giu else "", rels)
    muc["word/_rels/document.xml.rels"] = rels.encode("utf-8")
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as out:
        for ten, data in muc.items():
            out.writestr(infos[ten], data)


def _kiem(p: Path) -> None:
    """Mọi phần XML phải parse được; mọi r:embed phải có quan hệ; mọi quan hệ ảnh có tệp."""
    z = zipfile.ZipFile(p)
    for ten in z.namelist():
        if ten.endswith(".xml") or ten.endswith(".rels"):
            minidom.parseString(z.read(ten))
    doc = z.read("word/document.xml").decode("utf-8")
    rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    ids = set(re.findall(r"Id=\"([^\"]+)\"", rels))
    for rid in set(re.findall(r"r:(?:embed|id)=\"([^\"]+)\"", doc)):
        if rid not in ids:
            raise SystemExit(f"thiếu quan hệ {rid}")
    for t in re.findall(r"Target=\"(media/[^\"]+)\"", rels):
        if f"word/{t}" not in z.namelist():
            raise SystemExit(f"thiếu tệp word/{t}")


if __name__ == "__main__":
    sys.exit(main())
