"""Nội suy lỗ hổng ngắn có làm sai lệch autocorrelation không?

Đây là câu hỏi quyết định của QĐ-008. Autocorrelation là đại lượng trung tâm của
RQ3; nếu bước xử lý lỗ hổng làm nó tăng giả tạo thì toàn bộ kết luận về "động lực
học có transfer được không" mất giá trị.

Đo ba cách trên cùng một tập chuỗi:
  QUAN SÁT   chỉ dùng các cặp (t-1, t) mà CẢ HAI đều là số liệu thật
  NỘI SUY    nội suy tuyến tính lỗ hổng <= K rồi tính bình thường
  FFILL      forward-fill lỗ hổng <= K rồi tính bình thường  (để đối chứng)

Nếu NỘI SUY lệch không đáng kể so với QUAN SÁT, phép nội suy an toàn.
"""

import glob
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gap_policy_eval import (GRID, MAXLAG, WINDOW, grid_series, interp_short,  # noqa
                             load_alibaba, load_bitbrains, rows_from_mask, RAW)

K = 2


def acf_observed(s, lag):
    """Autocorr chỉ trên các cặp mà cả hai đầu đều là số liệu thật."""
    v = s.values
    a, b = v[:-lag], v[lag:]
    m = ~np.isnan(a) & ~np.isnan(b)
    if m.sum() < 30:
        return np.nan
    a, b = a[m], b[m]
    if a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def acf_filled(s, lag, how):
    if how == "interp":
        f = interp_short(s, K)
    else:
        f = s.copy()
        f = f.ffill(limit=K)
        # chỉ giữ phần được lấp bởi lỗ hổng <= K
        na = s.isna().values
        keep = np.zeros(len(s), bool)
        i = 0
        while i < len(s):
            if na[i]:
                j = i
                while j < len(s) and na[j]:
                    j += 1
                if j - i <= K:
                    keep[i:j] = True
                i = j
            else:
                i += 1
        out = s.copy()
        out.values[keep] = f.values[keep]
        f = out
    return acf_observed(f, lag)


def report(series_list, label):
    rows = []
    for s in series_list:
        if s.isna().all():
            continue
        rows.append(dict(
            obs1=acf_observed(s, 1), int1=acf_filled(s, 1, "interp"),
            ff1=acf_filled(s, 1, "ffill"),
            obs12=acf_observed(s, 12), int12=acf_filled(s, 12, "interp"),
            ff12=acf_filled(s, 12, "ffill"),
        ))
    r = pd.DataFrame(rows).dropna()
    print(f"===== {label}  ({len(r)} chuỗi) =====")
    print(f"  {'':<12}{'quan sát':>11}{'nội suy<=2':>13}{'lệch':>9}"
          f"{'ffill<=2':>11}{'lệch':>9}")
    for lag, a, b, c in [("acf lag-1", "obs1", "int1", "ff1"),
                         ("acf lag-12", "obs12", "int12", "ff12")]:
        o, i_, f = r[a].median(), r[b].median(), r[c].median()
        print(f"  {lag:<12}{o:>11.4f}{i_:>13.4f}{i_-o:>+9.4f}"
              f"{f:>11.4f}{f-o:>+9.4f}")
    # lệch tuyệt đối theo từng chuỗi, không chỉ trung vị
    d_int = (r.int1 - r.obs1).abs()
    d_ff = (r.ff1 - r.obs1).abs()
    print(f"  lệch tuyệt đối lag-1 theo chuỗi: "
          f"nội suy p95 = {d_int.quantile(.95):.4f}   "
          f"ffill p95 = {d_ff.quantile(.95):.4f}")
    print()


def extra_rows(series_list, label):
    """P4 = nội suy <= K rồi che theo dòng (không cắt đoạn)."""
    p1 = p4 = 0
    for s in series_list:
        p1 += rows_from_mask(~s.isna().values, 12)[0]
        p4 += rows_from_mask(~interp_short(s, K).isna().values, 12)[0]
    print(f"  {label}: P1 che dòng = {p1:,}   |   "
          f"P4 nội suy<= {K} + che dòng = {p4:,}   "
          f"({p4/max(p1,1)*100:.0f}%)")


if __name__ == "__main__":
    e1 = load_bitbrains(RAW / "Bitbrains-fastStorage" / "08-2013" / "*.csv", 120)
    e2 = load_bitbrains(RAW / "Bitbrains-Rnd" / "2013-8" / "*.csv", 120)
    e3 = load_alibaba()
    for s, lab in [(e1, "E1"), (e2, "E2"), (e3, "E3")]:
        report(s, lab)
    print("===== Số dòng của phương án P4 =====")
    for s, lab in [(e1, "E1"), (e2, "E2"), (e3, "E3")]:
        extra_rows(s, lab)
