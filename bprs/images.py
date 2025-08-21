# images.py (versi simple & tegas, anti-Tokopedia/Shopee)
from __future__ import annotations

import os
import io
import base64
import requests
import pandas as pd
from typing import Dict, Tuple, Optional
from urllib.parse import urlparse

# =========================================================
# Konfigurasi dasar
# =========================================================
IMAGE_CSV_PATH = os.environ.get("BPRS_IMAGE_CSV", "images_map.csv")
EMBED_AS_DATA_URI = True  # jika False, kembalikan URL mentah (as is)

# Domain yang TIDAK boleh dipakai (bikin gambar gak muncul)
_BANNED_DOMAINS = {
    "tokopedia.com",
    "images.tokopedia.net",
    "shopee.co.id",
    "cf.shopee.co.id",
    "img.susercontent.com",
    "down-id.img.susercontent.com",
    "down-my.img.susercontent.com",
    "susercontent.com",
}

# Placeholder 1x1 PNG
_PLACEHOLDER_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO1aG+QAAAAASUVORK5CYII="
)

# cache mapping
_IMAGE_MAP: Dict[Tuple[str, str, str], str] = {}
_LOADED_PATH: Optional[str] = None


# =========================================================
# Util sederhana
# =========================================================
def _norm(s: Optional[str]) -> str:
    return (str(s or "").strip().lower())

def _is_banned(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return any(host.endswith(b) for b in _BANNED_DOMAINS)
    except Exception:
        return False

def _guess_mime_from_url_or_name(u: str) -> str:
    u = u.lower()
    if u.endswith(".png"):
        return "image/png"
    if u.endswith(".webp"):
        return "image/webp"
    if u.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"

def _read_bytes(url_or_path: str, timeout: float = 15.0) -> Optional[bytes]:
    # http(s)
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        try:
            r = requests.get(
                url_or_path,
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                },
            )
            if r.status_code == 200 and r.content and len(r.content) > 256:
                return r.content
        except Exception:
            return None
        return None
    # local file
    try:
        with open(url_or_path, "rb") as f:
            b = f.read()
            return b if b and len(b) > 256 else None
    except Exception:
        return None


# =========================================================
# Loader mapping
# =========================================================
def configure(images_csv_path: Optional[str] = None, embed_as_data_uri: Optional[bool] = None) -> None:
    """Opsional: panggil sekali di awal app untuk set path CSV & mode embed."""
    global IMAGE_CSV_PATH, EMBED_AS_DATA_URI, _LOADED_PATH, _IMAGE_MAP
    if images_csv_path:
        IMAGE_CSV_PATH = images_csv_path
        _LOADED_PATH = None  # force reload
        _IMAGE_MAP.clear()
    if embed_as_data_uri is not None:
        EMBED_AS_DATA_URI = bool(embed_as_data_uri)

def _load_map_if_needed() -> None:
    """Baca images_map.csv → dict key (brand, sub, nama) → url"""
    global _LOADED_PATH, _IMAGE_MAP
    if _LOADED_PATH == IMAGE_CSV_PATH and _IMAGE_MAP:
        return
    _IMAGE_MAP.clear()
    _LOADED_PATH = IMAGE_CSV_PATH
    if not os.path.exists(IMAGE_CSV_PATH):
        # tidak ada file → biarkan kosong (pakai placeholder)
        return
    df = pd.read_csv(IMAGE_CSV_PATH)
    # normalisasi nama kolom
    cols = {c.lower().strip(): c for c in df.columns}
    need = {"brand", "sub_kategori", "nama_produk", "url"}
    if not need.issubset(set(cols.keys())):
        raise ValueError(
            f"images_map.csv harus punya kolom: {sorted(need)}. Kolom saat ini: {sorted(cols.keys())}"
        )
    for _, row in df.iterrows():
        key = (_norm(row[cols["brand"]]), _norm(row[cols["sub_kategori"]]), _norm(row[cols["nama_produk"]]))
        url = str(row[cols["url"]]).strip()
        if not url:
            continue
        _IMAGE_MAP[key] = url


# =========================================================
# API utama yang dipakai app
# =========================================================
def get_product_image(brand: str, product_name: str) -> str:
    """
    Kompatibilitas lama (dikembalikan URL mentah — kalau ada di CSV).
    Jika tak ketemu → placeholder.
    """
    _load_map_if_needed()
    # cari dengan nama_produk (tidak pakai sub_kategori)
    brand_n = _norm(brand)
    name_n = _norm(product_name)
    # scan sederhana (brand, *, nama)
    for (b, s, n), url in _IMAGE_MAP.items():
        if b == brand_n and n == name_n:
            return url
    # fallback placeholder
    return "data:image/png;base64," + _PLACEHOLDER_BASE64


def get_product_image_data_uri(
    brand: str,
    sub_kategori: str,
    dataset_url: Optional[str] = None,
    nama_produk: Optional[str] = None,
) -> str:
    """
    Cara paling simpel untuk app:
    1) Kalau dataset_url dikasih & bukan domain terlarang → pakai itu.
    2) Kalau tidak ada, cari di images_map.csv (brand+sub+nama).
       - mencoba urutan ketat → (brand, sub, nama) → (brand, *, nama) → (brand, sub, *)
    3) Jika gagal → placeholder.
    NOTE: Tokopedia/Shopee ditolak tegas.
    """
    _load_map_if_needed()

    # 1) dataset_url dari dataset
    if dataset_url:
        url = dataset_url.strip()
        if not _is_banned(url):
            return _to_data_or_url(url)
        # kalau terlarang → abaikan dan lanjut cari di mapping

    brand_n = _norm(brand)
    sub_n   = _norm(sub_kategori)
    name_n  = _norm(nama_produk) if nama_produk is not None else None

    # 2) cari di mapping
    # 2a. (brand, sub, nama)
    if name_n is not None:
        url = _IMAGE_MAP.get((brand_n, sub_n, name_n))
        if url and not _is_banned(url):
            return _to_data_or_url(url)

    # 2b. (brand, *, nama)
    if name_n is not None:
        for (b, s, n), url in _IMAGE_MAP.items():
            if b == brand_n and n == name_n and not _is_banned(url):
                return _to_data_or_url(url)

    # 2c. (brand, sub, *)
    for (b, s, n), url in _IMAGE_MAP.items():
        if b == brand_n and s == sub_n and not _is_banned(url):
            return _to_data_or_url(url)

    # 3) fallback → placeholder
    return "data:image/png;base64," + _PLACEHOLDER_BASE64


def _to_data_or_url(url: str) -> str:
    """Kembalikan data-URI bila EMBED_AS_DATA_URI=True, selain itu kembalikan URL mentah."""
    if _is_banned(url):
        # hard reject agar gampang kamu ketahui dan ganti URL-nya
        return "data:image/png;base64," + _PLACEHOLDER_BASE64
    if not EMBED_AS_DATA_URI:
        return url
    b = _read_bytes(url)
    if not b:
        return "data:image/png;base64," + _PLACEHOLDER_BASE64
    mime = _guess_mime_from_url_or_name(url)
    return f"data:{mime};base64,{base64.b64encode(b).decode('ascii')}"


# =========================================================
# Opsional: helper untuk memastikan "tak ada yang kurang"
# =========================================================
def export_template_from_products(products_df: pd.DataFrame, out_path: str = "images_map.csv") -> None:
    """
    Buat template CSV yang PERSIS mengikuti dataset (unik per brand+sub+nama).
    Kamu tinggal isi kolom 'url' dengan link gambar (bukan Tokopedia/Shopee).
    Kalau file sudah ada, baris lama dipertahankan; baris baru ditambahkan.
    """
    need_cols = {"brand", "sub_kategori", "nama_produk"}
    cols = {c.lower(): c for c in products_df.columns}
    if not need_cols.issubset(set(cols.keys())):
        raise ValueError(f"Dataset harus punya kolom: {sorted(need_cols)}")

    base = products_df[[cols["brand"], cols["sub_kategori"], cols["nama_produk"]]].copy()
    base.columns = ["brand", "sub_kategori", "nama_produk"]
    base["brand"] = base["brand"].astype(str).str.strip()
    base["sub_kategori"] = base["sub_kategori"].astype(str).str.strip()
    base["nama_produk"] = base["nama_produk"].astype(str).str.strip()
    base.drop_duplicates(subset=["brand", "sub_kategori", "nama_produk"], inplace=True)
    base["url"] = base["url"]  # kosong dulu

    if os.path.exists(out_path):
        old = pd.read_csv(out_path)
        # normalisasi kolom lama
        oc = {c.lower(): c for c in old.columns}
        if {"brand", "sub_kategori", "nama_produk", "url"}.issubset(set(oc.keys())):
            old = old[[oc["brand"], oc["sub_kategori"], oc["nama_produk"], oc["url"]]].copy()
            old.columns = ["brand", "sub_kategori", "nama_produk", "url"]
            # merge → pertahankan url lama
            base = base.merge(old, on=["brand", "sub_kategori", "nama_produk"], how="left", suffixes=("", "_old"))
            base["url"] = base["url"].where(base["url"].astype(str).str.len() > 0, base["url_old"])
            base.drop(columns=["url_old"], inplace=True)

    base.to_csv(out_path, index=False)

def assert_all_images_present(products_df: pd.DataFrame, raise_on_banned: bool = True) -> None:
    """
    Cek ketuntasan: semua baris dataset punya gambar & (opsional) tidak memakai domain terlarang.
    Lempar ValueError berisi daftar yang belum ada/ganti.
    """
    _load_map_if_needed()
    missing = []
    banned  = []
    cols = {c.lower(): c for c in products_df.columns}
    for _, r in products_df.iterrows():
        brand = _norm(r[cols["brand"]]) if "brand" in cols else ""
        sub   = _norm(r[cols["sub_kategori"]]) if "sub_kategori" in cols else ""
        name  = _norm(r[cols["nama_produk"]]) if "nama_produk" in cols else ""

        # dataset_url kalau ada
        durl = None
        if "image_url" in cols:
            durl = str(r[cols["image_url"]]).strip()
            if durl == "" or durl.lower() == "nan":
                durl = None

        url = None
        if durl and not _is_banned(durl):
            url = durl
        if url is None:
            url = _IMAGE_MAP.get((brand, sub, name))
        if url is None:
            # cari variasi lain
            for (b, s, n), u in _IMAGE_MAP.items():
                if b == brand and n == name:
                    url = u; break
            if url is None:
                for (b, s, n), u in _IMAGE_MAP.items():
                    if b == brand and s == sub:
                        url = u; break

        if not url:
            missing.append((brand, sub, name))
        elif raise_on_banned and _is_banned(url):
            banned.append((brand, sub, name, url))

    if missing or banned:
        msg = []
        if missing:
            msg.append("Gambar BELUM diisi untuk (brand,sub,nama):")
            msg += [f"  - {b} | {s} | {n}" for (b, s, n) in missing]
        if banned:
            msg.append("\nGanti URL terlarang (Tokopedia/Shopee) berikut:")
            msg += [f"  - {b} | {s} | {n} → {u}" for (b, s, n, u) in banned]
        raise ValueError("\n".join(msg))
