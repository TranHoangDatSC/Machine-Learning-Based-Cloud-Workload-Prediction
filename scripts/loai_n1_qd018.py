"""QĐ-018 điểm 1 — danh sách chuỗi bị loại khỏi TẬP HUẤN LUYỆN ở N1.

    python scripts/loai_n1_qd018.py

Luật: `max |z_t|` trên `[0, 1957)` vượt giới hạn Samuelson `(n − 1)/√n` của chính cửa sổ
train `[0, 1612)`. Không tham số tự do. Ghi `config/qd018_loai_n1.csv` một lần; lần sau
chỉ đối chiếu, khác thì thoát 1 — cùng cách đóng băng của QĐ-009 và QĐ-017.

In kèm số chuỗi **vi phạm giới hạn ngay trong cửa sổ train**. Con số đó phải bằng 0 ở mọi
môi trường, vì đó là định lý; khác 0 nghĩa là hiện thực giới hạn sai.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
ENVS = ("E1", "E2", "E3", "E1a", "E1g")
W, TRAIN_END, FIT_END = 2304, 1612, 1957
COT = ["env", "series_id", "n_train", "mu", "sd", "max_abs_z_khop", "bien_samuelson"]


def bien_samuelson(n) -> np.ndarray:
    """`(n − 1)/√n` — cận trên của `|x − x̄|/s` (ddof = 1) trong mẫu `n` điểm."""
    n = np.asarray(n, dtype="float64")
    return (n - 1.0) / np.sqrt(n)


def xet_moi_truong(env: str, ids: list[str], Y: np.ndarray) -> tuple[pd.DataFrame, int]:
    """Bảng mọi chuỗi của một môi trường kèm cờ `loai`, và số vi phạm trong train."""
    tr = Y[:, :TRAIN_END]
    n = np.isfinite(tr).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = np.nanmean(tr, axis=1)
        sd = np.nanstd(tr, axis=1, ddof=1)
        z_tr = np.abs((tr - mu[:, None]) / sd[:, None])
        z_khop = np.abs((Y[:, :FIT_END] - mu[:, None]) / sd[:, None])
    b = bien_samuelson(n)
    # Chuỗi sd = 0 (hay NaN) đã không có dòng N1 nào theo QĐ-016 — không cần loại.
    dung = np.isfinite(sd) & (sd > 0)
    m_tr = np.where(dung, np.nanmax(np.where(np.isfinite(z_tr), z_tr, -np.inf), axis=1), np.nan)
    m_kh = np.where(dung, np.nanmax(np.where(np.isfinite(z_khop), z_khop, -np.inf), axis=1), np.nan)
    vi_pham = int((dung & (m_tr > b * (1 + 1e-12))).sum())
    df = pd.DataFrame({"env": env, "series_id": ids, "n_train": n, "mu": mu, "sd": sd,
                       "max_abs_z_khop": m_kh, "bien_samuelson": b})
    df["loai"] = dung & (m_kh > b)
    return df, vi_pham


def nap(env: str, proc: Path) -> tuple[list[str], np.ndarray]:
    d = (pd.read_parquet(proc / f"{env}.parquet", columns=["series_id", "bucket", "y"])
         .sort_values(["series_id", "bucket"], kind="mergesort"))
    ids = d["series_id"].drop_duplicates().tolist()
    if len(d) != len(ids) * W:
        raise ValueError(f"{env}: lưới không đều")
    return ids, d["y"].to_numpy("float64").reshape(len(ids), W)


def main() -> int:
    proc = ROOT / "data" / "processed"
    p = ROOT / "config" / "qd018_loai_n1.csv"
    phan, loi = [], 0
    for env in ENVS:
        df, vp = xet_moi_truong(env, *nap(env, proc))
        loi += vp
        l = df[df["loai"]]
        print(f"{env:4} {len(df):>4} chuỗi · vi phạm trong train: {vp} · loại: {len(l)}"
              + (f"  {', '.join(l['series_id'])}" if 0 < len(l) <= 12 else ""))
        phan.append(l[COT])
    if loi:
        print("CHƯA ĐẠT — có chuỗi vượt giới hạn Samuelson ngay trong cửa sổ train: "
              "hiện thực giới hạn sai.")
        return 1
    moi = pd.concat(phan, ignore_index=True)
    if p.exists():
        cu = pd.read_csv(p)
        khop = (cu[["env", "series_id"]].equals(moi[["env", "series_id"]])
                and np.allclose(cu[COT[2:]].to_numpy(float), moi[COT[2:]].to_numpy(float),
                                rtol=1e-12, atol=1e-12))
        if not khop:
            print(f"CHƯA ĐẠT — {p.name} khác bản tính lại. Không ghi đè (QĐ-018 điểm 1).")
            return 1
        print(f"Đối chiếu {p.name}: khớp.")
    else:
        moi.to_csv(p, index=False, float_format="%.17g")
        print(f"Đóng băng {p.relative_to(ROOT)} — {len(moi)} dòng")
    return 0


if __name__ == "__main__":
    sys.exit(main())
