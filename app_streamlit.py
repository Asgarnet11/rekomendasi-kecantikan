# Streamlit UI untuk BeautyProductRecommendationSystem (refactor modular)
from __future__ import annotations

import io
import re
import numpy as np
import pandas as pd
import streamlit as st

from bprs import (
    BeautyProductRecommendationSystem,
    read_csv_flex,
    safe_price_bounds,
    PINK_AND_CARD_CSS,
)

st.set_page_config(page_title="Sistem Rekomendasi Kecantikan", page_icon="💗", layout="wide")

# CSS
st.markdown(PINK_AND_CARD_CSS, unsafe_allow_html=True)
st.markdown('<div class="pink-bg"><h2>Sistem Rekomendasi Produk Kecantikan</h2></div>', unsafe_allow_html=True)
st.caption("Menggunakan Metode *Machine Learning*.")

# Load data (upload optional)
uploaded = st.sidebar.file_uploader("Unggah CSV (opsional)", type=["csv"])
recomm = BeautyProductRecommendationSystem()

if uploaded is not None:
    up_df = read_csv_flex(uploaded)
    st.success(f"CSV terunggah: {uploaded.name} — {len(up_df)} baris")
    recomm.load_and_preprocess_data(uploaded_df=up_df)
else:
    # Otomatis baca data/products_seed.csv
    recomm.load_and_preprocess_data()

# Build similarity
recomm.build_similarity_matrix()
df = recomm.products_df.copy()

# Sidebar filters
st.sidebar.header("Preferensi Pengguna")
skin_universe = set()
for s in df["jenis_kulit_kompatibel"].dropna().astype(str):
    tokens = re.split(r"[,\|]", s)
    skin_universe.update([t.strip().lower() for t in tokens if t.strip()])
skin_opts = sorted(skin_universe) if skin_universe else ["berjerawat","berminyak","kering","sensitif","normal","kombinasi","kusam","semua jenis kulit"]
skin_display = [s.title() for s in skin_opts]
skin_choice = st.sidebar.selectbox("Jenis kulit Anda", skin_display, index=0)
skin_choice_raw = skin_opts[skin_display.index(skin_choice)]

sub_opts = sorted(df["sub_kategori"].dropna().astype(str).str.strip().unique().tolist())
sub_kat = st.sidebar.selectbox("Sub Kategori (opsional)", ["(Semua)"] + sub_opts, index=0)

if sub_kat != "(Semua)":
    brand_pool = df.loc[df["sub_kategori"].astype(str).str.strip() == sub_kat, "brand"]
else:
    brand_pool = df["brand"]
brand_opts = ["(Semua)"] + sorted(brand_pool.dropna().astype(str).unique().tolist())
brand_choice = st.sidebar.selectbox("Brand (opsional)", brand_opts, index=0)

min_rating = st.sidebar.slider("Rating minimum", 0.0, 5.0, 4.0, 0.1)
lo, hi = safe_price_bounds(df["harga_idr"])
default_lo, default_hi = lo, min(hi, lo + 300_000)
if default_lo >= default_hi:
    default_hi = default_lo + 1
price_range = st.sidebar.slider("Harga (IDR)", min_value=int(lo), max_value=int(hi),
                                  value=(int(default_lo), int(default_hi)))

top_n = st.sidebar.slider("Top-N", 3, 20, 8)

chip = lambda s: f"<span class='chip'>{s}</span>"
chips = chip(f"Skin: <b>{skin_choice}</b>")
if sub_kat != "(Semua)":
    chips += chip(f"Sub: <b>{sub_kat}</b>")
if brand_choice != "(Semua)":
    chips += chip(f"Brand: <b>{brand_choice}</b>")
chips += chip(f"Rating ≥ <b>{min_rating:.1f}</b>") + chip(f"Harga: <b>Rp {price_range[0]:,}–{price_range[1]:,}</b>")
st.markdown(chips.replace(",","."), unsafe_allow_html=True)

if st.button("✨ Rekomendasikan", use_container_width=True):
    compatible = recomm.find_compatible_products(skin_choice_raw)
    if compatible.empty:
        st.warning("Tidak ada produk yang kompatibel dengan jenis kulit tersebut.")
    else:
        mask = pd.Series(True, index=compatible.index)
        if sub_kat != "(Semua)":
            mask &= compatible["sub_kategori"].astype(str).str.strip().eq(sub_kat)
        if brand_choice != "(Semua)":
            mask &= compatible["brand"].astype(str).str.strip().eq(brand_choice)
        mask &= compatible["rating"].fillna(0) >= float(min_rating)
        mask &= (compatible["harga_idr"].fillna(0) >= price_range[0]) & (compatible["harga_idr"].fillna(0) <= price_range[1])

        filtered = compatible.loc[mask].copy()
        if filtered.empty:
            st.warning("Tidak ada produk sesuai kombinasi filter. Coba longgarkan filter.")
        else:
            idxs = filtered.index.tolist()
            ranked = recomm.rank_on_subset(idxs, top_n=top_n)

            if not ranked:
                st.warning("Tidak ada ranking yang bisa dihitung.")
            else:
                st.subheader(f"Top {len(ranked)} Rekomendasi Produk Untuk Anda")
                cols = st.columns(4)
                for i, (idx, score, prod) in enumerate(ranked):
                    with cols[i % 4]:
                        nama_produk = prod.get("nama_produk", "N/A")
                        brand = prod.get("brand", "N/A")
                        deskripsi = prod.get("deskripsi", "N/A")
                        manfaat = prod.get("Manfaat", "N/A")
                        rating = prod.get("rating", 0)
                        harga = prod.get("harga_idr", 0)
                        size = prod.get("size_ml", 0)

                        rating_text = f"⭐ {rating:.2f}" if rating > 0 else "N/A"
                        harga_text = f"Rp {harga:,.0f}".replace(",",".") if harga > 0 else "N/A"
                        size_text = f"{size:.0f} ml" if size > 0 else ""
                        jenis_kulit = prod.get("jenis_kulit_kompatibel", "N/A")
                        manfaat_text = manfaat if len(manfaat) < 100 else manfaat[:97] + "..."
                        deskripsi_text = deskripsi if len(deskripsi) < 150 else deskripsi[:147] + "..."

                        image_data_uri = recomm.get_product_image_data_uri(
                            brand=brand,
                            sub_kategori=prod.get("sub_kategori", ""),
                            dataset_url=prod.get("image_url", None)
                        )

                        st.markdown(f"""
                        <div class="product-card">
                            <div class="image-container">
                                <img src="{image_data_uri}" alt="{nama_produk}" loading="lazy">
                            </div>
                            <div class="content-wrapper">
                                <div class="header">
                                    <div class="brand">{brand}</div>
                                    <div class="tag rating">{rating_text}</div>
                                </div>
                                <h3 class="product-name">{nama_produk}</h3>
                                <div class="price-section">
                                    <div class="price">{harga_text}</div>
                                    <div class="size">{size_text}</div>
                                </div>
                                <div class="info-section">
                                    <div class="info-row">
                                        <span class="label">Jenis Kulit:</span>
                                        <span class="value">{jenis_kulit}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="label">Manfaat:</span>
                                        <span class="value">{manfaat_text}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="label">Deskripsi:</span>
                                        <span class="value">{deskripsi_text}</span>
                                    </div>
                                </div>
                                <div class="score">
                                    <div class="match-score">Skor Kecocokan: {score:.2f}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")
                rows = []
                for i, (idx, score, prod) in enumerate(ranked, 1):
                    rows.append({
                        "rank": i, "nama_produk": prod.get("nama_produk", ""), "brand": prod.get("brand", ""),
                        "sub_kategori": prod.get("sub_kategori", ""), "rating": prod.get("rating", np.nan),
                        "harga_idr": prod.get("harga_idr", np.nan), "size_ml": prod.get("size_ml", np.nan),
                        "Manfaat": prod.get("Manfaat", ""), "jenis_kulit_kompatibel": prod.get("jenis_kulit_kompatibel", ""),
                        "klaim": prod.get("klaim", ""), "skor_rekomendasi": round(float(score), 4),
                    })
                out_df = pd.DataFrame(rows)
                buf = io.StringIO(); out_df.to_csv(buf, index=False)
                st.download_button("⬇ Unduh Rekomendasi (CSV)", buf.getvalue(),
                                   file_name="rekomendasi.csv", mime="text/csv",
                                   use_container_width=True)

st.sidebar.markdown("---")
with st.sidebar:
    st.subheader("Ringkasan Data")
    st.metric("Total Produk", len(df))
    st.write("Sub Kategori:", ", ".join(sorted(df["sub_kategori"].astype(str).str.strip().unique().tolist())))
    if pd.notna(df["harga_idr"]).any():
        st.write(
            "Rentang Harga: Rp {:,.0f} – {:,.0f}".format(
                float(df["harga_idr"].min()),
                float(df["harga_idr"].max())
            ).replace(",", ".")
        )
