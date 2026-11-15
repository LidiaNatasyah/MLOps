import yaml
import pandas as pd
from src import features as F


def test_tidak_ada_kolom_terlarang_di_fitur():
    """Memastikan daftar fitur aktif dan matriks hasil terapkan() bebas dari kolom TERLARANG."""
    terlarang = set(F.TERLARANG)
    fitur_aktif = set(F.NUMERIK + F.KATEGORIK)

    irisan_definisi = terlarang.intersection(fitur_aktif)
    assert not irisan_definisi, f"Kolom terlarang ditemukan di definisi fitur: {irisan_definisi}"

    df_sampel = pd.read_csv("data/raw/kredit_sumatera.csv").head(50)
    art = F.pelajari(df_sampel)
    X = F.terapkan(df_sampel, art)

    kolom_bocor_matriks = [
        kol for kol in X.columns
        if kol in terlarang or any(kol.startswith(f"{t}__") for t in terlarang)
    ]
    assert not kolom_bocor_matriks, f"Kebocoran terdeteksi pada matriks fitur: {kolom_bocor_matriks}"


def test_kelengkapan_katalog_fitur():
    """Memastikan seluruh fitur aktif terdokumentasi di conf/katalog_fitur.yaml."""
    with open("conf/katalog_fitur.yaml", encoding="utf-8") as f:
        katalog = yaml.safe_load(f)

    fitur_aktif = set(F.NUMERIK + F.KATEGORIK)
    belum_tercatat = fitur_aktif - set(katalog.keys())
    assert not belum_tercatat, f"Fitur belum terdaftar di katalog: {belum_tercatat}"

    for nama in fitur_aktif:
        entri = katalog[nama]
        assert "kesegaran_maks" in entri, f"Medan kesegaran_maks hilang pada {nama}"
        assert entri.get("nilai_hilang") is not None, f"Kebijakan nilai_hilang kosong pada {nama}"
