"""feature_store.py — prototipe feature store mini (lapis offline Parquet & online SQLite)."""
from __future__ import annotations

import os
import sqlite3
import pandas as pd

OFFLINE = "data/processed/fitur_offline.parquet"
ONLINE = "data/processed/fitur_online.db"
ENTITAS = "pengajuan_id"
KOLOM_ONLINE = ["rata_saldo_90h", "jumlah_tunggakan_12b", "ragam_penghasilan"]


def tulis_offline(df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(OFFLINE), exist_ok=True)
    df.to_parquet(OFFLINE, index=False)


def materialisasi(df: pd.DataFrame, waktu_materialisasi: str) -> int:
    """Menyalin nilai TERBARU dari lapis offline ke lapis online."""
    os.makedirs(os.path.dirname(ONLINE), exist_ok=True)
    con = sqlite3.connect(ONLINE)
    t = df[[ENTITAS] + KOLOM_ONLINE].copy()
    t["waktu_materialisasi"] = waktu_materialisasi
    t.to_sql("fitur", con, if_exists="replace", index=False)
    con.commit()
    con.close()
    return len(t)


def ambil_online(entitas_id: str) -> dict | None:
    con = sqlite3.connect(ONLINE)
    cur = con.execute(f"SELECT * FROM fitur WHERE {ENTITAS} = ?", (entitas_id,))
    kolom = [d[0] for d in cur.description]
    baris = cur.fetchone()
    con.close()
    return dict(zip(kolom, baris)) if baris else None


def usia_fitur_jam(entitas_id: str, sekarang: pd.Timestamp) -> float | None:
    """Kesegaran fitur wajib dipantau sebagai metrik tersendiri."""
    rec = ambil_online(entitas_id)
    if rec is None:
        return None
    return (sekarang - pd.Timestamp(rec["waktu_materialisasi"])).total_seconds() / 3600


def laporan_kesegaran(sekarang: pd.Timestamp) -> pd.DataFrame:
    """Mengembalikan tabel jumlah entitas per rentang usia fitur pada lapis online."""
    con = sqlite3.connect(ONLINE)
    t = pd.read_sql_query(f"SELECT {ENTITAS}, waktu_materialisasi FROM fitur", con)
    con.close()

    usia = (sekarang - pd.to_datetime(t["waktu_materialisasi"])).dt.total_seconds() / 3600
    batas = [-1e-9, 6, 24, 72, float("inf")]
    label = [
        "0 - 6 jam (Sangat Segar)",
        "6 - 24 jam (Normal / SLA)",
        "24 - 72 jam (Basi / Peringatan)",
        "> 72 jam (Kritis)",
    ]
    kategori = pd.cut(usia, bins=batas, labels=label)
    ringkasan = (
        kategori.value_counts()
        .reindex(label, fill_value=0)
        .rename_axis("rentang_usia")
        .reset_index(name="jumlah_entitas")
    )
    ringkasan["persentase"] = (ringkasan["jumlah_entitas"] / len(t) * 100).round(2)
    return ringkasan