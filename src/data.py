"""data.py — pemuatan, validasi skema, dan pembagian menurut waktu."""
from __future__ import annotations
import pandas as pd

SKEMA = {
    "pengajuan_id": "object",
    "tanggal_pengajuan": "object",
    "periode": "object",
    "segmen": "object",
    "wilayah": "object",
    "kanal": "object",
    "usia": "int64",
    "tanggungan": "int64",
    "lama_usaha_tahun": "float64",
    "penghasilan_bulanan": "float64",
    "ragam_penghasilan": "float64",
    "plafon_diajukan": "float64",
    "tenor_bulan": "int64",
    "bunga_tahunan": "float64",
    "angsuran_bulanan": "float64",
    "rata_saldo_90h": "float64",
    "jumlah_tunggakan_12b": "int64",
    "gagal_bayar": "int64",
    "status_restrukturisasi": "object",
}

RENTANG = {
    "usia": (17, 75),
    "tenor_bulan": (3, 60),
    "bunga_tahunan": (0.05, 0.40),
    "ragam_penghasilan": (0.0, 1.0),
    "gagal_bayar": (0, 1),
    "jumlah_tunggakan_12b": (0, 12),
}

MAKS_HILANG = {
    "rata_saldo_90h": 0.20,
    "lama_usaha_tahun": 0.10,
}


def muat(jalur: str) -> pd.DataFrame:
    return pd.read_csv(jalur)


def validasi(df: pd.DataFrame) -> list[str]:
    """Mengembalikan daftar pelanggaran kontrak data. Kosong berarti lulus."""
    masalah = []

    # 1. Verifikasi keberadaan dan tipe data seluruh kolom SKEMA (19 kolom)
    for kolom, tipe in SKEMA.items():
        if kolom not in df.columns:
            masalah.append(f"kolom hilang: {kolom}")
        elif str(df[kolom].dtype) != tipe:
            masalah.append(f"{kolom}: tipe data {df[kolom].dtype}, seharusnya {tipe}")

    # 2. Verifikasi batas rentang nilai setiap fitur
    for kolom, (bawah, atas) in RENTANG.items():
        if kolom in df:
            luar = ((df[kolom] < bawah) | (df[kolom] > atas)).sum()
            if luar:
                masalah.append(f"{kolom}: {luar} nilai di luar rentang [{bawah}, {atas}]")

    # 3. Verifikasi proporsi nilai hilang maksimum
    for kolom, maks in MAKS_HILANG.items():
        if kolom in df:
            rasio = df[kolom].isna().mean()
            if rasio > maks:
                masalah.append(f"{kolom}: nilai hilang {rasio:.1%} melampaui batas {maks:.0%}")

    # 4. Verifikasi kewajaran tingkat gagal bayar (target balance)
    if "gagal_bayar" in df:
        laju = df["gagal_bayar"].mean()
        if not (0.02 <= laju <= 0.25):
            masalah.append(f"tingkat gagal bayar {laju:.2%} di luar rentang wajar 2%-25%")

    # 5. ATURAN BARU 1: Konsistensi matematis angsuran bulanan terhadap pokok pinjaman
    if {"angsuran_bulanan", "plafon_diajukan", "tenor_bulan"}.issubset(df.columns):
        tenor_valid = df["tenor_bulan"] > 0
        cicilan_pokok = df.loc[tenor_valid, "plafon_diajukan"] / df.loc[tenor_valid, "tenor_bulan"]
        angsuran = df.loc[tenor_valid, "angsuran_bulanan"]
        tidak_konsisten = ((angsuran < cicilan_pokok * 0.99) | (angsuran > cicilan_pokok * 2.50)).sum()
        if tidak_konsisten:
            masalah.append(
                f"angsuran_bulanan: {tidak_konsisten} baris tidak konsisten terhadap plafon_diajukan/tenor_bulan"
            )

    # 6. ATURAN BARU 2: Positivitas variabel moneter utama (penghasilan & plafon)
    for kolom_moneter in ("penghasilan_bulanan", "plafon_diajukan"):
        if kolom_moneter in df:
            non_positif = (df[kolom_moneter] <= 0).sum()
            if non_positif:
                masalah.append(f"{kolom_moneter}: {non_positif} baris bernilai <= 0")

    return masalah


def bagi_waktu(df: pd.DataFrame, batas_latih: str, batas_validasi: str):
    """Pembagian OUT-OF-TIME. Pembagian acak pada data temporal adalah kesalahan."""
    p = df["periode"].astype(str)
    latih = df[p <= batas_latih]
    validasi_ = df[(p > batas_latih) & (p <= batas_validasi)]
    uji = df[p > batas_validasi]
    return latih, validasi_, uji