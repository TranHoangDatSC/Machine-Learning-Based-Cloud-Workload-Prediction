"""Bảng phân tầng burstiness và kiểm định Wilcoxon cho GĐ3 (mục 13, 15, QĐ-012).

    python scripts/fig_gd3_results.py --env all

Đọc `results/tables/per_series_gd3.csv` — chỉ số theo **từng chuỗi** mà
`run_experiments.py` đã ghi — rồi sinh:

    results/tables/tang_gd3.csv        chỉ số tách theo ba tầng burstiness
    results/tables/wilcoxon_gd3.csv    mọi cặp model, Wilcoxon + Holm–Bonferroni
    results/tables/ml_vs_naive_gd3.csv câu trả lời cho RQ1, một dòng mỗi (env, h)
    results/figures/gd3/               tám panel .png và một .pdf gộp

Ngưỡng tầng **không hardcode**
------------------------------

Cách chia đọc từ `config/split.yaml` (`stratify.method = percentile_within_env`,
`n_strata = 3`); ngưỡng tính lại từ `results/tables/cv_gd2.csv` mỗi lần chạy. Ngưỡng
tuyệt đối dùng chung cho ba môi trường là **sai** — QĐ-012 điểm 1: tương quan giữa CV
và mức tải đổi dấu giữa Bitbrains và Alibaba, và tam phân vị của E3 chỉ rộng 0,06.

Mỗi bảng phân tầng báo kèm `ti_le_cham_chan` (QĐ-012 điểm 3), để phân biệt một chuỗi
ít bursty **do bản chất** với một chuỗi ít bursty **vì đã cụng trần thang đo 100**.

CV chỉ để **báo cáo** — QĐ-012 điểm 2. Không đặc trưng, không trọng số huấn luyện,
không tiêu chí chọn model: `cv_gd2.csv` tính trên toàn bộ cửa sổ 8 ngày nên nó biết
tương lai.

Kiểm định — protocol mục 15
---------------------------

Wilcoxon signed-rank trên **MAE theo từng chuỗi**, ghép cặp trên đúng tập chuỗi mà cả
hai model đều có số. `alpha = 0,05`. So nhiều model cùng lúc thì hiệu chỉnh
**Holm–Bonferroni**, họ kiểm định là **mọi cặp trong một `(env, h)`**.

*"Không tuyên bố model X tốt hơn model Y nếu chưa có kiểm định. Chênh lệch 2% MAE trên
trung vị hoàn toàn có thể là nhiễu."*
"""

import argparse
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from cwp.evaluation.metrics import METRIC_NAMES
from cwp.evaluation.tang import TEN_TANG, bang_tang, doc_cau_hinh_tang, gan_tang
from cwp.viz.xuat import Panel, chu_giai_duoi, xuat_bo_hinh

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
ENVS = ["E1", "E2", "E3"]
HORIZONS = [1, 6, 12]
ALPHA = 0.05

# Thứ tự đọc bảng: ba baseline trước, rồi năm model ML (protocol mục 11).
THU_TU = ["naive", "ma6", "seasonal", "lr", "ridge", "rf", "xgb", "svr"]
MAU = {
    "naive": "#0b0b0b", "ma6": "#6b6a66", "seasonal": "#a8a6a0",
    "lr": "#3a7ca5", "ridge": "#5fa8d3", "rf": "#2a9d8f",
    "xgb": "#e76f51", "svr": "#9b5de5",
}


def _goi(p: Path) -> str:
    """Đường dẫn gọn so với gốc repo, nhưng không đổ vỡ khi nó nằm ngoài repo."""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


# --------------------------------------------------------------- phân tầng

def bang_phan_tang(ps: pd.DataFrame, tang: pd.DataFrame) -> pd.DataFrame:
    """Năm chỉ số, tách theo ba tầng, kèm `ti_le_cham_chan` trung vị của tầng."""
    d = ps.merge(tang[["series_id", "env", "tang", "cv", "ti_le_cham_chan"]],
                 on=["series_id", "env"], how="left")
    thieu = int(d["tang"].isna().sum())
    if thieu:
        print(f"CẢNH BÁO: {thieu} dòng không gán được tầng (thiếu trong cv_gd2.csv).")

    dong = []
    for (env, h, model, t), g in d.groupby(["env", "h", "model", "tang"], sort=False):
        for m in METRIC_NAMES:
            v = pd.to_numeric(g[m], errors="coerce")
            v = v[np.isfinite(v)]
            if len(v):
                p25, p50, p75 = (float(x) for x in np.percentile(v, [25, 50, 75]))
            else:
                p25 = p50 = p75 = float("nan")
            dong.append({
                "env": env, "h": h, "model": model, "tang": t, "metric": m,
                "p25": p25, "p50": p50, "p75": p75, "iqr": p75 - p25,
                "n_chuoi": int(len(v)), "n_loai": int(len(g) - len(v)),
                "cv_p50": float(g["cv"].median()),
                "ti_le_cham_chan_p50": float(g["ti_le_cham_chan"].median()),
            })
    out = pd.DataFrame(dong)
    out["tang"] = pd.Categorical(out["tang"], categories=list(TEN_TANG), ordered=True)
    out["model"] = pd.Categorical(out["model"], categories=THU_TU, ordered=True)
    out["metric"] = pd.Categorical(out["metric"], categories=METRIC_NAMES, ordered=True)
    return out.sort_values(["env", "h", "model", "tang", "metric"]).reset_index(drop=True)


# ------------------------------------------------------------- kiểm định

def holm(p: np.ndarray) -> np.ndarray:
    """Hiệu chỉnh Holm–Bonferroni (mục 15). Trả về p đã hiệu chỉnh, cắt tại 1."""
    p = np.asarray(p, dtype="float64")
    n = len(p)
    thu_tu = np.argsort(p)
    dieu_chinh = np.empty(n)
    chay = 0.0
    for i, k in enumerate(thu_tu):
        chay = max(chay, (n - i) * p[k])     # đơn điệu không giảm theo thứ hạng
        dieu_chinh[k] = min(chay, 1.0)
    return dieu_chinh


def kiem_dinh_cap(ps: pd.DataFrame) -> pd.DataFrame:
    """Wilcoxon signed-rank cho **mọi cặp model** trong từng `(env, h)` — mục 15."""
    dong = []
    for (env, h), g in ps.groupby(["env", "h"], sort=False):
        rong = g.pivot_table(index="series_id", columns="model", values="mae")
        co = [m for m in THU_TU if m in rong.columns]
        for a, b in combinations(co, 2):
            cap = rong[[a, b]].dropna()
            if len(cap) < 10:
                continue
            va, vb = cap[a].to_numpy(), cap[b].to_numpy()
            hieu = va - vb
            if np.allclose(hieu, 0):
                stat, p = float("nan"), 1.0
            else:
                stat, p = wilcoxon(va, vb, alternative="two-sided")
            dong.append({
                "env": env, "h": h, "model_a": a, "model_b": b,
                "n_chuoi": int(len(cap)),
                "mae_p50_a": float(np.median(va)), "mae_p50_b": float(np.median(vb)),
                # Hai đại lượng KHÁC NHAU, và chúng ngược dấu nhau ở 8 cặp của GĐ3:
                "delta_p50": float(np.median(va) - np.median(vb)),   # hiệu hai trung vị
                "hieu_p50": float(np.median(va - vb)),               # trung vị của hiệu
                "n_a_thap_hon": int((va < vb).sum()),
                "thong_ke": float(stat), "p": float(p),
            })
    out = pd.DataFrame(dong)
    if out.empty:
        return out
    # Họ kiểm định là mọi cặp TRONG MỘT (env, h) — 28 cặp khi đủ tám model.
    out["p_holm"] = np.concatenate([
        holm(g["p"].to_numpy()) for _, g in out.groupby(["env", "h"], sort=False)
    ])
    out["co_y_nghia"] = out["p_holm"] < ALPHA
    # Hướng lấy từ **trung vị của hiệu**, không phải hiệu hai trung vị. Wilcoxon là
    # kiểm định GHÉP CẶP: nó nói về phân phối của `MAE_a − MAE_b` trên từng chuỗi, nên
    # chỉ `median(a − b)` mới cùng một thứ với cái nó kiểm.
    out["tot_hon"] = np.where(
        ~out["co_y_nghia"], "không kết luận",
        np.where(out["hieu_p50"] < 0, out["model_a"], out["model_b"]),
    )
    return out


def bang_ml_vs_naive(wil: pd.DataFrame, ps: pd.DataFrame) -> pd.DataFrame:
    """Một dòng mỗi `(env, h)`: model nào vượt naive, và có ý nghĩa thống kê không.

    Đây là câu trả lời trực tiếp cho RQ1 và cho điều kiện qua cổng ở `gate-gd3.md`
    mục 3.5. **Nếu ML thua naive thì dòng này nói đúng như vậy** — protocol mục 17.
    """
    dong = []
    for (env, h), g in ps.groupby(["env", "h"], sort=False):
        rong = g.pivot_table(index="series_id", columns="model", values="mae")
        if "naive" not in rong.columns:
            continue
        naive_p50 = float(rong["naive"].median())
        w = wil[(wil["env"] == env) & (wil["h"] == h)]
        thang = []
        for m in [c for c in THU_TU if c in rong.columns and c != "naive"]:
            cap = w[((w["model_a"] == m) & (w["model_b"] == "naive"))
                    | ((w["model_b"] == m) & (w["model_a"] == "naive"))]
            if cap.empty:
                continue
            r = cap.iloc[0]
            p50 = float(rong[m].median())
            # Dấu của `hieu_p50` quy về "model m trừ naive" bất kể m nằm ở cột nào.
            hieu = float(r["hieu_p50"]) * (1 if r["model_a"] == m else -1)
            cap_chung = rong[[m, "naive"]].dropna()
            dong.append({
                "env": env, "h": h, "model": m,
                "mae_p50": p50, "mae_p50_naive": naive_p50,
                "ti_so": p50 / naive_p50 if naive_p50 else float("nan"),
                "hieu_p50_theo_chuoi": hieu,
                "n_chuoi_tot_hon": int((cap_chung[m] < cap_chung["naive"]).sum()),
                "n_chuoi": int(len(cap_chung)),
                "p_holm": float(r["p_holm"]),
                "co_y_nghia": bool(r["co_y_nghia"]),
                "vuot_naive": bool(hieu < 0 and r["co_y_nghia"]),
            })
            if hieu < 0 and r["co_y_nghia"]:
                thang.append(m)
    return pd.DataFrame(dong)


# ------------------------------------------------------------------ hình

def _panel_mae_theo_horizon(bang: pd.DataFrame, env: str):
    def ve(ax):
        con = bang[(bang["env"] == env) & (bang["metric"] == "mae")
                   & (bang["split"] == "test")]
        for m in THU_TU:
            g = con[con["model"] == m].sort_values("h")
            if g.empty:
                continue
            ax.plot(g["h"], g["p50"], marker="o", ms=4, lw=1.6,
                    color=MAU[m], label=m,
                    ls="--" if m in ("naive", "ma6", "seasonal") else "-")
        ax.set_xticks(HORIZONS)
        ax.set_xlabel("horizon h (bucket 5 phút)")
        ax.set_ylabel("MAE trung vị theo chuỗi")
        ax.grid(alpha=0.25, lw=0.6)
        chu_giai_duoi(ax, ncol=4)
    return ve


def _panel_phan_tang(tang_bang: pd.DataFrame, env: str, h: int):
    def ve(ax):
        con = tang_bang[(tang_bang["env"] == env) & (tang_bang["h"] == h)
                        & (tang_bang["metric"] == "mae")]
        co = [m for m in THU_TU if m in set(con["model"])]
        x = np.arange(len(TEN_TANG))
        rong = 0.8 / max(len(co), 1)
        for i, m in enumerate(co):
            g = con[con["model"] == m].set_index("tang")["p50"]
            ax.bar(x + i * rong - 0.4 + rong / 2,
                   [g.get(t, np.nan) for t in TEN_TANG],
                   width=rong, color=MAU[m], label=m)
        ax.set_xticks(x)
        ax.set_xticklabels([f"CV {t}" for t in TEN_TANG])
        ax.set_ylabel("MAE trung vị theo chuỗi")
        ax.grid(alpha=0.25, lw=0.6, axis="y")
        chu_giai_duoi(ax, ncol=4)
    return ve


def _panel_cham_chan(tang_bang: pd.DataFrame):
    def ve(ax):
        con = tang_bang[(tang_bang["metric"] == "mae")
                        & (tang_bang["model"] == "naive")]
        x = np.arange(len(TEN_TANG))
        for i, env in enumerate(ENVS):
            g = con[(con["env"] == env) & (con["h"] == 1)].set_index("tang")
            if g.empty:
                continue
            ax.bar(x + i * 0.27 - 0.27,
                   [g["ti_le_cham_chan_p50"].get(t, np.nan) for t in TEN_TANG],
                   width=0.27, label=env,
                   color=["#0b0b0b", "#5fa8d3", "#e76f51"][i])
        ax.axhline(1.0, color="#b00020", lw=1.0, ls="--")
        ax.set_xticks(x)
        ax.set_xticklabels([f"CV {t}" for t in TEN_TANG])
        ax.set_ylabel("tỉ lệ chạm chần (trung vị)")
        ax.grid(alpha=0.25, lw=0.6, axis="y")
        chu_giai_duoi(ax, ncol=3)
    return ve


def _panel_vs_naive(mvn: pd.DataFrame, env: str):
    def ve(ax):
        con = mvn[mvn["env"] == env]
        co = [m for m in THU_TU if m in set(con["model"])]
        x = np.arange(len(HORIZONS))
        rong = 0.8 / max(len(co), 1)
        for i, m in enumerate(co):
            g = con[con["model"] == m].set_index("h")
            cao = [g["ti_so"].get(h, np.nan) for h in HORIZONS]
            b = ax.bar(x + i * rong - 0.4 + rong / 2, cao, width=rong,
                       color=MAU[m], label=m)
            for j, h in enumerate(HORIZONS):
                r = g.loc[h] if h in g.index else None
                if r is not None and not bool(r["co_y_nghia"]):
                    ax.text(b[j].get_x() + b[j].get_width() / 2,
                            (cao[j] or 0) + 0.02, "ns", ha="center",
                            fontsize=6.5, color="#52514e")
        ax.axhline(1.0, color="#0b0b0b", lw=1.2)
        ax.set_xticks(x)
        ax.set_xticklabels([f"h = {h}" for h in HORIZONS])
        ax.set_ylabel("MAE model / MAE naive")
        ax.grid(alpha=0.25, lw=0.6, axis="y")
        chu_giai_duoi(ax, ncol=4)
    return ve


# ------------------------------------------------------------------ main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="all", choices=ENVS + ["all"])
    ap.add_argument("--tables", default="results/tables")
    ap.add_argument("--figures", default="results/figures/gd3")
    a = ap.parse_args()

    envs = ENVS if a.env == "all" else [a.env]
    tab = ROOT / a.tables
    fig_dir = ROOT / a.figures

    p_ps = tab / "per_series_gd3.csv"
    if not p_ps.exists():
        raise SystemExit(
            f"Thiếu {p_ps}. Chạy Bước 5 trước: python scripts/run_experiments.py --env all"
        )
    ps = pd.read_csv(p_ps)
    ps = ps[ps["env"].isin(envs)]

    st = doc_cau_hinh_tang(ROOT / "config" / "split.yaml")
    cv_bang = pd.read_csv(tab / "cv_gd2.csv")
    tang = bang_tang(cv_bang, envs=tuple(envs), n_strata=int(st["n_strata"]))

    print()
    print("=" * 78)
    print("TẦNG BURSTINESS — tam phân vị CV TRONG TỪNG MÔI TRƯỜNG (QĐ-012 điểm 1)")
    print("=" * 78)
    print(f"cách chia: {st['method']}, n_strata = {st['n_strata']} "
          "(đọc từ config/split.yaml, ngưỡng tính lại từ cv_gd2.csv)")
    print(f"{'env':<5}{'ngưỡng thấp/vừa':>18}{'ngưỡng vừa/cao':>17}"
          f"{'số chuỗi mỗi tầng':>22}")
    for env in envs:
        _, ng = gan_tang(cv_bang, env, int(st["n_strata"]))
        dem = tang[tang["env"] == env]["tang"].value_counts().reindex(TEN_TANG)
        print(f"{env:<5}{ng[0]:>18.6f}{ng[1]:>17.6f}"
              f"{' / '.join(str(int(x)) for x in dem):>22}")
    print("=" * 78)

    tb_tang = bang_phan_tang(ps, tang)
    tb_tang.to_csv(tab / "tang_gd3.csv", index=False)

    wil = kiem_dinh_cap(ps)
    wil.to_csv(tab / "wilcoxon_gd3.csv", index=False)

    mvn = bang_ml_vs_naive(wil, ps)
    mvn.to_csv(tab / "ml_vs_naive_gd3.csv", index=False)

    _in_ket_luan(mvn, wil)

    # Bảng gộp cho hình: ưu tiên experiments_gd3.csv, lùi về baselines_gd3.csv.
    phan = []
    for ten in ("experiments_gd3.csv", "baselines_gd3.csv"):
        if (tab / ten).exists():
            phan.append(pd.read_csv(tab / ten))
    gop = pd.concat(phan, ignore_index=True).drop_duplicates(
        ["env", "h", "model", "split", "metric"], keep="first")

    panels = []
    for i, env in enumerate(envs, start=1):
        panels.append(Panel(f"{i:02d}_mae-theo-horizon-{env}",
                            f"{env} — MAE trung vị theo chuỗi, trên test",
                            (7.0, 4.4), _panel_mae_theo_horizon(gop, env)))
    for i, env in enumerate(envs, start=len(envs) + 1):
        panels.append(Panel(f"{i:02d}_phan-tang-{env}-h1",
                            f"{env}, h = 1 — MAE tách theo ba tầng burstiness",
                            (7.0, 4.4), _panel_phan_tang(tb_tang, env, 1)))
    n = 2 * len(envs)
    if not mvn.empty:
        for i, env in enumerate(envs, start=n + 1):
            panels.append(Panel(f"{i:02d}_ti-so-voi-naive-{env}",
                                f"{env} — MAE model chia cho MAE naive",
                                (7.0, 4.4), _panel_vs_naive(mvn, env)))
        n += len(envs)
    panels.append(Panel(f"{n + 1:02d}_ti-le-cham-chan",
                        "Tỉ lệ chạm chần theo tầng — QĐ-012 điểm 3",
                        (7.0, 4.4), _panel_cham_chan(tb_tang)))

    anh, pdf = xuat_bo_hinh(
        panels, fig_dir, "gd3_ket-qua.pdf",
        tieu_de="GĐ3 — Thí nghiệm A, trong cùng môi trường",
        phu=("Tám model của protocol mục 11, ba môi trường, ba horizon. Mọi con số đo "
             "trên tập test, gộp bằng trung vị theo chuỗi kèm IQR (QĐ-013 điểm 5)."),
        dien_giai=_dien_giai(mvn, st, cv_bang, envs),
    )
    print()
    print(f"Ghi {len(anh)} ảnh và {pdf.name} vào {_goi(fig_dir)}/")
    for ten in ("tang_gd3.csv", "wilcoxon_gd3.csv", "ml_vs_naive_gd3.csv"):
        print(f"Ghi {_goi(tab)}/{ten}")
    return 0


def _in_ket_luan(mvn: pd.DataFrame, wil: pd.DataFrame) -> None:
    print()
    print("=" * 78)
    print("ML CÓ VƯỢT NAIVE KHÔNG — RQ1, gate-gd3.md mục 3.5")
    print("=" * 78)
    if mvn.empty:
        print("Chưa có kết quả model ML. Chạy Bước 5 xong rồi chạy lại.")
        return
    print("Wilcoxon signed-rank trên MAE theo chuỗi, Holm–Bonferroni trong từng "
          f"(env, h), alpha = {ALPHA}.")
    print("Hướng lấy từ TRUNG VỊ CỦA HIỆU theo từng chuỗi, không phải hiệu hai trung "
          "vị —")
    print("hai đại lượng này ngược dấu nhau ở 8 cặp của GĐ3.")
    print(f"{'env':<5}{'h':>3}   {'model vượt naive (p_holm < 0,05)':<40}"
          f"{'MAE gộp thấp nhất':>20}")
    for (env, h), g in mvn.groupby(["env", "h"], sort=False):
        thang = g[g["vuot_naive"]]["model"].tolist()
        tot = g.sort_values("mae_p50").iloc[0]
        nhan_tot = f"{tot['model']} {tot['ti_so']:.3f}×"
        print(f"{env:<5}{h:>3}   {(', '.join(thang) if thang else 'KHÔNG CÓ'):<40}"
              f"{nhan_tot:>20}")
    print("=" * 78)
    print("'KHÔNG CÓ' là một kết quả hợp lệ và phải được báo cáo — protocol mục 17: "
          "'Không giấu")
    print("việc baseline naive thắng model ML, nếu điều đó xảy ra.'")


def _dien_giai(mvn, st, cv_bang, envs) -> list[tuple[str, str]]:
    dong = []
    for env in envs:
        _, ng = gan_tang(cv_bang, env, int(st["n_strata"]))
        dong.append(f"{env}: {ng[0]:.6f} / {ng[1]:.6f}")
    thang = "" if mvn.empty else ", ".join(
        f"{e} h{h}: " + (", ".join(g[g['vuot_naive']]['model']) or "không có")
        for (e, h), g in mvn.groupby(["env", "h"], sort=False)
    )
    return [
        ("Đọc hình thế nào",
         "Ba panel đầu là MAE trung vị theo chuỗi trên tập test, một panel mỗi môi "
         "trường, đường đứt là ba baseline của mục 11. Ba panel giữa tách cùng con số "
         "đó theo ba tầng burstiness. Ba panel sau lấy tỉ số MAE model chia MAE naive: "
         "dưới đường 1,0 là tốt hơn naive, chữ 'ns' là chênh lệch không có ý nghĩa "
         "thống kê sau hiệu chỉnh Holm–Bonferroni."),
        ("Tầng burstiness chia thế nào",
         "Tam phân vị của CV tính riêng trong từng môi trường (QĐ-012 điểm 1), ngưỡng "
         "tính lại từ cv_gd2.csv mỗi lần chạy chứ không hardcode — " + "; ".join(dong)
         + ". Không dùng ngưỡng tuyệt đối chung cho ba môi trường: tương quan giữa CV "
         "và mức tải đổi dấu giữa Bitbrains và Alibaba, và tam phân vị của E3 chỉ rộng "
         "0,06 nên nó sẽ bị dồn hết vào tầng thấp nhất của E1."),
        ("CV là biến báo cáo, không phải đặc trưng",
         "cv_gd2.csv tính CV trên toàn bộ cửa sổ 8 ngày, tức có cả phần rơi vào "
         "validation và test. Dùng để nhóm chuỗi khi đọc bảng thì không sao; dùng làm "
         "đặc trưng, trọng số huấn luyện hay tiêu chí chọn model thì là rò rỉ (QĐ-012 "
         "điểm 2). Panel cuối là tỉ lệ chạm chần CV/√((100−m)/m) — chuỗi có tỉ lệ gần "
         "1 thì CV thấp của nó là do cụng trần thang đo 100, không phải do ít bursty."),
        ("Kiểm định",
         "Wilcoxon signed-rank trên MAE theo từng chuỗi, ghép cặp trên đúng tập chuỗi "
         f"mà cả hai model đều có số, alpha = {ALPHA}, hiệu chỉnh Holm–Bonferroni "
         "trong từng (env, h). Model vượt naive có ý nghĩa: "
         + (thang or "chưa có kết quả ML")),
    ]


if __name__ == "__main__":
    sys.exit(main())
