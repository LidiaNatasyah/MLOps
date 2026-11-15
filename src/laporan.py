"""laporan.py — membangkitkan ringkasan metrik evaluasi dalam format Markdown."""
from __future__ import annotations
import argparse, json, os
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", default="artifacts/metadata.json")
    ap.add_argument("--segmen", default="artifacts/metrik_segmen.csv")
    ap.add_argument("--keluaran", default="laporan/ringkasan_metrik.md")
    a = ap.parse_args()

    meta = json.load(open(a.metadata, encoding="utf-8"))
    seg = pd.read_csv(a.segmen)
    oot = meta["metrik_uji_oot"]
    val = meta["metrik_validasi"]

    os.makedirs(os.path.dirname(a.keluaran), exist_ok=True)

    baris = [
        "# Ringkasan Metrik Model Kredit Sumatera",
        "",
        f"- **Versi Model:** `{meta['versi_model']}`",
        f"- **Git Commit:** `{meta['git_commit']}`",
        f"- **Algoritma:** `{meta['algoritma']}`",
        f"- **Parameter:** `{json.dumps(meta['parameter'])}`",
        "",
        "## 1. Metrik Evaluasi Agregat",
        "",
        "| Metrik | Validasi | Uji Out-of-Time (OOT) |",
        "| :--- | :---: | :---: |",
        f"| **AUC** | {val['auc']:.4f} | {oot['auc']:.4f} |",
        f"| **KS** | {val['ks']:.4f} | {oot['ks']:.4f} |",
        f"| **Gini** | {val['gini']:.4f} | {oot['gini']:.4f} |",
        f"| **Ambang Optimal** | {val['ambang_optimal']:.4f} | {oot['ambang_optimal']:.4f} |",
        f"| **Biaya Total (Rp)** | {val['biaya_total']:,.0f} | {oot['biaya_total']:,.0f} |",
        f"| **Jumlah Sampel ($n$)** | {val['n']} | {oot['n']} |",
        "",
        "## 2. Evaluasi Terpilah per Segmen (Uji OOT)",
        "",
        "| Segmen | Jumlah ($n$) | AUC | Laju Target (Gagal Bayar) |",
        "| :--- | :---: | :---: | :---: |",
    ]

    for r in seg.itertuples():
        baris.append(f"| `{r.segmen}` | {r.n} | {r.auc:.6f} | {r.laju_target:.6f} |")

    terlemah = seg.loc[seg["auc"].idxmin()]
    baris.extend([
        "",
        "## 3. Catatan Risiko Segmen",
        "",
        f"Segmen dengan kinerja terlemah adalah **`{terlemah['segmen']}`** "
        f"(AUC = `{terlemah['auc']:.6f}`) meskipun laju gagal bayarnya tinggi "
        f"(`{terlemah['laju_target']:.2%}`). Evaluasi agregat menyembunyikan risiko ini.",
        "",
    ])

    with open(a.keluaran, "w", encoding="utf-8") as f:
        f.write("\n".join(baris))

    print(f"Ringkasan Markdown tersimpan di: {a.keluaran}")


if __name__ == "__main__":
    main()