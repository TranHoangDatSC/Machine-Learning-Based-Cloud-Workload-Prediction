"""HẬU KIỂM Q3 của GĐ4 — bất đối xứng đo bằng mốc nào.

    python scripts/hau_kiem_q3_gd4.py

Chỉ đọc, không ghi tệp nào. Đặt ra trong buổi rà soát 2026-09-13, **sau khi** đã có
bảng Q3. Cân p-value đúng mức.

Vì sao cần: Q3 trong `fig_gd4_transfer.py` so tỉ số `MAE transfer / MAE naive tại
đích`. Nhưng GĐ3 cho thấy naive **vượt được** ở E3 và **gần như không vượt được** ở
E1/E2. Tỉ số với naive vì thế trộn hai thứ: *đích dễ hay khó* và *transfer mất bao
nhiêu*. Ở đây mốc là **cùng model train ngay trên chuỗi đích** (`per_series_gd3.csv`),
nên tỉ số chỉ còn phần mất mát do transfer.

Giới hạn còn lại: mốc GĐ3 là chế độ N0. Ở N1, N2 tỉ số vẫn trộn hiệu ứng của chính
phép chuẩn hoá — muốn tách phải chạy đường chéo (E1→E1, ...) ở N1, N2, việc chưa làm.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

TAB = Path(__file__).resolve().parents[1] / "results" / "tables"
DOI_XUNG = [(("E1", "E3"), ("E3", "E1")), (("E2", "E3"), ("E3", "E2")),
            (("E1", "E2"), ("E2", "E1"))]
MODES = ["N0", "N1", "N2"]
HS = [1, 6, 12]
ML = ["lr", "ridge", "rf", "xgb", "svr"]
ALPHA = 0.05


def holm(p: np.ndarray) -> np.ndarray:
    k = len(p)
    out = np.empty(k)
    chay = 0.0
    for r, i in enumerate(np.argsort(p)):
        chay = max(chay, min(1.0, (k - r) * p[i]))
        out[i] = chay
    return out


def main() -> None:
    g4 = pd.read_csv(TAB / "per_series_gd4.csv")
    g3 = (pd.read_csv(TAB / "per_series_gd3.csv")
          [["env", "h", "model", "series_id", "n_dong", "mae"]]
          .rename(columns={"env": "dich", "mae": "mae_gd3", "n_dong": "n_dong_gd3"}))
    x = g4.merge(g3, on=["dich", "h", "model", "series_id"], how="inner")
    lech = x[x["n_dong"] != x["n_dong_gd3"]]
    print(f"dòng GĐ4: {len(g4)}, ghép được: {len(x)}, lệch số dòng test: {len(lech)} "
          f"({lech['series_id'].nunique()} chuỗi, chế độ {sorted(lech['mode'].unique())})")
    x = x[x["mae_gd3"] > 0].copy()
    x["chi_phi"] = x["mae"] / x["mae_gd3"]

    dong = []
    for xuoi, nguoc in DOI_XUNG:
        for md in MODES:
            for h in HS:
                for m in ML:
                    def lay(cp):
                        s = x[(x["nguon"] == cp[0]) & (x["dich"] == cp[1])
                              & (x["mode"] == md) & (x["h"] == h) & (x["model"] == m)]
                        return s["chi_phi"].to_numpy()
                    a, b = lay(xuoi), lay(nguoc)
                    u, p = mannwhitneyu(a, b, alternative="two-sided")
                    dong.append({"xuoi": f"{xuoi[0]}->{xuoi[1]}", "mode": md, "h": h,
                                 "model": m, "p50_xuoi": np.median(a),
                                 "p50_nguoc": np.median(b),
                                 # > 0: chiều xuôi có hạng lớn hơn, tức tốn hơn
                                 "rank_biserial": 2.0 * u / (len(a) * len(b)) - 1.0,
                                 "p": p})
    o = pd.DataFrame(dong)
    o["p_holm"] = holm(o["p"].to_numpy())
    o["ket_luan"] = np.where(o["p_holm"] >= ALPHA, "không khác",
                             np.where(o["rank_biserial"] < 0, "xuôi rẻ hơn", "ngược rẻ hơn"))
    print(o.groupby(["xuoi", "mode"])["ket_luan"].value_counts().unstack(fill_value=0))
    print()
    print(o.groupby(["xuoi", "mode"])[["p50_xuoi", "p50_nguoc"]].median().round(3))


if __name__ == "__main__":
    main()
