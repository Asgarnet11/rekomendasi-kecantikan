import io
import time
import numpy as np
import pandas as pd
import streamlit as st
from recommender import BeautyRecommenderV2

st.set_page_config(page_title="Sistem Rekomendasi Kecantikan v2", page_icon="💗", layout="wide")

# ==========================
# ✨ THEME & GLOBAL STYLES ✨
# ==========================
PINK_CSS = """
<style>
  :root{
    --pink-1:#ffe6f1;  /* background */
    --pink-2:#ffb6d1;  /* accent soft */
    --pink-3:#ff8ab8;  /* accent mid */
    --pink-4:#ff5fa2;  /* primary */
    --pink-5:#e0488a;  /* primary dark */
    --ink-1:#1f1f1f;   /* text */
  }
  /* gradient background */
  .pink-bg{
    background: radial-gradient(1200px 600px at 0% 0%, var(--pink-1), transparent 60%),
                radial-gradient(900px 500px at 100% 0%, #fff0f6, transparent 55%),
                linear-gradient(180deg, #fff, #fff);
    animation: fadeIn 0.6s ease-out both;
    padding: 0.25rem 0 0.75rem 0;
  }
  @keyframes fadeIn{from{opacity:.0;transform:translateY(6px)}to{opacity:1;transform:none}}
  @keyframes floaty{0%{transform:translateY(0)}50%{transform:translateY(-6px)}100%{transform:translateY(0)}}
  @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(255,95,162,.45)}70%{box-shadow:0 0 0 12px rgba(255,95,162,0)}100%{box-shadow:0 0 0 0 rgba(255,95,162,0)}}

  /* Title badge */
  .title-wrap{display:flex; align-items:center; gap:.6rem;}
  .title-emoji{font-size:1.8rem; animation: floaty 4s ease-in-out infinite;}
  .title-badge{display:inline-flex; align-items:center; gap:.4rem; padding:.25rem .6rem; border-radius:999px; background:linear-gradient(90deg,var(--pink-3),var(--pink-4)); color:white; font-weight:600; letter-spacing:.2px}

  /* Buttons */
  .stButton > button{
    background: linear-gradient(90deg, var(--pink-4), var(--pink-3));
    color: #fff; border: none; padding:.6rem 1rem; border-radius:999px;
    transition: transform .08s ease, box-shadow .2s ease;
  }
  .stButton > button:hover{ transform: translateY(-1px); box-shadow:0 8px 22px rgba(255,95,162,.25)}
  .stButton > button:active{ transform: translateY(0); box-shadow:0 3px 10px rgba(255,95,162,.35)}

  /* Checkboxes / widgets accent */
  input[type="checkbox" i]{ accent-color: var(--pink-4); }
  .stSlider > div [role=slider]{ border:2px solid var(--pink-3); }

  /* Cards grid */
  .beauty-card{ background:#fff; border:1px solid #ffe3f0; border-radius:18px; padding:14px 16px; margin-bottom:14px;
                box-shadow:0 6px 24px rgba(255,90,160,.08); transition:transform .12s ease, box-shadow .2s ease;}
  .beauty-card:hover{ transform: translateY(-2px); box-shadow:0 10px 26px rgba(255,90,160,.15)}
  .beauty-card .hdr{ display:flex; align-items:center; justify-content:space-between; gap:.6rem; margin-bottom:.4rem}
  .beauty-badge{ font-size:.75rem; font-weight:600; color:#8a2b52; background:#fff2f8; border:1px solid #ffd2e6; padding:.16rem .5rem; border-radius:999px}
  .beauty-score{ font-weight:700; color:#9d2c59; background:#ffe6f2; border-radius:10px; padding:.12rem .5rem}
  .beauty-name{ font-weight:700; font-size:1.02rem; color:#261622; margin:.15rem 0}
  .beauty-brand{ color:#8b4564; font-weight:600; font-size:.9rem}
  .beauty-rating{ color:#b03d73; font-weight:600; font-size:.9rem; margin-top:.1rem}
  .beauty-meta{ color:#6b2c49; font-size:.86rem; opacity:.9 }
  .beauty-reasons{ font-size:.86rem; color:#53233a; margin-top:.35rem }
  .beauty-reasons ul{ margin: .35rem 0 0 .9rem }

  /* Chips */
  .chip{ display:inline-flex; align-items:center; gap:.35rem; padding:.2rem .6rem; border-radius:999px; background:#fff0f7; border:1px solid #ffd6e8; color:#7d2a4f; font-size:.8rem; font-weight:600; margin-right:.35rem; margin-bottom:.35rem}
  .chip b{ color:#9d2c59 }

  /* Dataframe tweaks */
  div[data-testid="stDataFrame"] { animation: fadeIn .4s ease both; border-radius:14px; overflow:hidden; border:1px solid #ffe3f0; }
</style>
"""

st.markdown(PINK_CSS, unsafe_allow_html=True)

# Header block
st.markdown('<div class="pink-bg">', unsafe_allow_html=True)
colh1, colh2 = st.columns([3,1])
with colh1:
    st.markdown(
        '<div class="title-wrap">'
        '<div class="title-emoji">💗</div>'
        '<h1 style="margin:0">Sistem Rekomendasi Produk Kecantikan</h1>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption("Hybrid content-based + preferensi + quality signals · Nuansa Pink ✨")
with colh2:
    st.write("")
    if st.button("Reset filter", type="secondary"):
        st.session_state.clear(); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_data(path: str = "data/produk_kecantikan_v2.csv") -> pd.DataFrame:
    return pd.read_csv(path)

# ==== Sidebar: Dataset & Preferensi ====
st.sidebar.header("📦 Dataset")
user_csv = st.sidebar.file_uploader("Unggah CSV v2 (opsional)", type=["csv"])
if user_csv is not None:
    df = pd.read_csv(user_csv)
else:
    df = load_data()

# Normalisasi kolom
df.columns = [str(c).lower() for c in df.columns]

# Validasi minimal kolom
required_cols = {"nama_produk","brand","sub_kategori","jenis_kulit_kompatibel","rating","harga_idr","size_ml","bahan_aktif","klaim"}
if not required_cols.issubset(set(df.columns)):
    st.error("CSV v2 wajib punya kolom minimal: " + ", ".join(sorted(required_cols)))
    st.stop()

# Koersi tipe (khusus boolean bila berupa string)
def to_bool_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().isin(["true","1","yes","y"])
for bcol in ["non_alkohol","non_fragrance","aman_malassezia"]:
    if bcol in df.columns:
        df[bcol] = to_bool_series(df[bcol])

brands = sorted([str(x) for x in df["brand"].dropna().unique().tolist()])
subcats = sorted([str(x) for x in df["sub_kategori"].dropna().unique().tolist()])

# Opsi actives & claims dari data
actives_opts = sorted(set(
    a.strip() for a in df["bahan_aktif"].fillna("").str.split("|").explode().dropna().unique().tolist() if a
))
claims_opts = sorted(set(
    a.strip() for a in df["klaim"].fillna("").str.split("|").explode().dropna().unique().tolist() if a
))

with st.sidebar:
    st.header("🎯 Preferensi Anda")
    jenis_kulit = st.selectbox("Jenis Kulit", ["Kering","Berminyak","Kombinasi","Normal","Sensitif","Berjerawat"], index=0,
                               help="Jenis kulit utama untuk mengarahkan rekomendasi.")
    nama_produk = st.text_input("Nama Produk (opsional)", placeholder="mis. Niacinamide, Cica, Retinol…")
    brand_pref = st.selectbox("Brand", ["Tidak spesifik"] + brands)
    sub_pref = st.selectbox("Sub Kategori", ["Tidak spesifik"] + subcats)
    min_rating = st.slider("Rating minimum", 0.0, 5.0, 4.0, 0.1)

    st.caption("Filter lanjutan")
    harga_min = float(df["harga_idr"].min()) if "harga_idr" in df else 0
    harga_max = float(df["harga_idr"].max()) if "harga_idr" in df else 0
    if harga_min == harga_max:
        harga_min = 0.0
    price_range = st.slider(
        "Rentang harga (IDR)",
        min_value=int(harga_min),
        max_value=int(max(harga_max, harga_min + 1)),
        value=(int(harga_min), int(min(harga_max, harga_min + 300000)))
    )

    colA, colB, colC = st.columns(3)
    with colA:
        must_free_alcohol = st.checkbox("Tanpa alkohol saja")
    with colB:
        must_free_fragrance = st.checkbox("Fragrance-free saja")
    with colC:
        must_malassezia_safe = st.checkbox("Aman malassezia saja")

    wanted_actives = st.multiselect("Bahan aktif yang diinginkan", options=actives_opts)
    avoid_actives = st.multiselect("Bahan aktif yang dihindari", options=actives_opts)
    wanted_claims = st.multiselect("Prioritas klaim", options=claims_opts)
    only_skin_match = st.checkbox("Hanya tampilkan yang cocok jenis kulit")

    st.caption("Bobot & Penalti (lanjutan)")
    w_content = st.slider("w_content (kemiripan konten)", 0.0, 1.0, 0.40, 0.05)
    w_rating  = st.slider("w_rating", 0.0, 1.0, 0.20, 0.05)
    w_skin    = st.slider("w_skin", 0.0, 1.0, 0.10, 0.05)
    w_brand   = st.slider("w_brand", 0.0, 1.0, 0.05, 0.05)
    w_sub     = st.slider("w_sub", 0.0, 1.0, 0.05, 0.05)
    w_claim   = st.slider("w_claim", 0.0, 1.0, 0.07, 0.05)
    w_active  = st.slider("w_active", 0.0, 1.0, 0.08, 0.05)
    w_value   = st.slider("w_value (value per harga)", 0.0, 1.0, 0.05, 0.05)
    w_cheap   = st.slider("w_cheap (lebih murah lebih baik)", 0.0, 1.0, 0.00, 0.05)

    penalty_avoid = st.slider("Penalti bahan dihindari", 0.0, 1.0, 0.20, 0.05)
    penalty_komedo_per_point = st.slider("Penalti komedogenik / poin", 0.0, 0.2, 0.02, 0.01)
    komedo_threshold_for_acne = st.slider("Ambang komedogenik utk Berjerawat", 0.0, 5.0, 2.0, 0.5)

    top_k = st.slider("Jumlah rekomendasi (Top‑K)", 5, 30, 10)

# ===== Small chips to summarize filters =====
def chip(label: str) -> str:
    return f'<span class="chip">{label}</span>'

chip_row = ""
if brand_pref and brand_pref != "Tidak spesifik":
    chip_row += chip(f"Brand: <b>{brand_pref}</b>")
if sub_pref and sub_pref != "Tidak spesifik":
    chip_row += chip(f"Sub: <b>{sub_pref}</b>")
if wanted_actives:
    chip_row += chip("Aktif: <b>" + ", ".join(wanted_actives[:3]) + ("…" if len(wanted_actives)>3 else "") + "</b>")
if wanted_claims:
    chip_row += chip("Klaim: <b>" + ", ".join(wanted_claims[:3]) + ("…" if len(wanted_claims)>3 else "") + "</b>")
if must_free_alcohol: chip_row += chip("No alcohol")
if must_free_fragrance: chip_row += chip("Fragrance‑free")
if must_malassezia_safe: chip_row += chip("Malassezia‑safe")
if chip_row:
    st.markdown(chip_row, unsafe_allow_html=True)

# ===== Helpers for rendering =====
rec = BeautyRecommenderV2(df)

def idr(x) -> str:
    try:
        n = float(x)
        s = f"Rp {n:,.0f}"
        return s.replace(",", ".")
    except Exception:
        return "-"

def stars(r: float) -> str:
    if pd.isna(r):
        return ""
    full = int(round(r))
    return "★" * full + "☆" * (5 - full)

# ------- View mode -------
view_mode = st.radio("Mode tampilan", ["Kartu", "Tabel"], horizontal=True, index=0)

col1, col2 = st.columns([3,2])
with col1:
    st.subheader("Hasil Rekomendasi")
    go = st.button("✨ Rekomendasikan", use_container_width=True)

    if go:
        with st.spinner("Mencari yang paling cocok untukmu…"):
            result = rec.recommend(
                jenis_kulit=jenis_kulit,
                nama_produk=nama_produk,
                brand_pref=brand_pref,
                sub_pref=sub_pref,
                min_rating=min_rating,
                price_range=price_range,
                must_free_alcohol=must_free_alcohol,
                must_free_fragrance=must_free_fragrance,
                must_malassezia_safe=must_malassezia_safe,
                wanted_actives=wanted_actives,
                avoid_actives=avoid_actives,
                wanted_claims=wanted_claims,
                only_skin_match=only_skin_match,
                top_k=top_k,
                w_content=w_content,
                w_rating=w_rating,
                w_skin=w_skin,
                w_brand=w_brand,
                w_sub=w_sub,
                w_claim=w_claim,
                w_active=w_active,
                w_value=w_value,
                w_cheap=w_cheap,
                penalty_avoid=penalty_avoid,
                penalty_komedo_per_point=penalty_komedo_per_point,
                komedo_threshold_for_acne=komedo_threshold_for_acne,
            )
        if result.empty:
            st.warning("Tidak ada hasil sesuai filter. Coba longgarkan filter atau turunkan rating minimum.")
        else:
            base_cols = [
                "nama_produk","brand","sub_kategori","rating","harga_idr","size_ml","jenis_kulit_kompatibel",
                "bahan_aktif","klaim","non_alkohol","non_fragrance","aman_malassezia","komedogenik_score","skor","alasan"
            ]
            extra_cols = [
                "s_content","s_rating","s_skin","s_brand","s_sub","s_claim","s_active","s_value","s_cheap","p_avoid","p_komedo"
            ]

            result_show = result[base_cols + (extra_cols if st.checkbox("Tampilkan breakdown skor per komponen", value=False) else [])].head(top_k)

            if view_mode == "Tabel":
                st.dataframe(result_show, use_container_width=True, height=540)
            else:
                # Render as cards (2-column responsive)
                cols = st.columns(2)
                for i, row in result_show.reset_index(drop=True).iterrows():
                    with cols[i % 2]:
                        size_txt = (f"{int(row['size_ml'])} ml" if pd.notna(row['size_ml']) and float(row['size_ml']).is_integer() else f"{row['size_ml']} ml") if pd.notna(row['size_ml']) and row['size_ml'] != 0 else "—"
                        reasons_html = ""
                        if isinstance(row["alasan"], str) and row["alasan"].strip():
                            items = [f"<li>{x.strip()}</li>" for x in row["alasan"].split("; ") if x.strip()]
                            reasons_html = "<ul>" + "".join(items) + "</ul>"
                        card_html = f"""
                        <div class='beauty-card'>
                          <div class='hdr'>
                            <div class='beauty-badge'>{row['sub_kategori'] or '-'}</div>
                            <div class='beauty-score'>Skor {row['skor']:.3f}</div>
                          </div>
                          <div class='beauty-name'>{row['nama_produk']}</div>
                          <div class='beauty-brand'>{row['brand']}</div>
                          <div class='beauty-rating'>{stars(row['rating'])} <span style='opacity:.8'>({row['rating']:.1f})</span></div>
                          <div class='beauty-meta'>{idr(row['harga_idr'])} • {size_txt} • Kulit: {row['jenis_kulit_kompatibel']}</div>
                          <div class='beauty-reasons'>{reasons_html}</div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)

            csv_buf = io.StringIO()
            result_show.to_csv(csv_buf, index=False)
            st.download_button(
                "⬇️ Unduh Hasil (CSV)",
                csv_buf.getvalue(),
                file_name="rekomendasi_v2.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.toast("Rekomendasi siap ✨", icon="🎉")
            
    else:
        st.info("Isi preferensi di sidebar lalu klik **✨ Rekomendasikan**.")

with col2:
    st.subheader("Ringkasan Dataset")
    st.metric("Jumlah Produk", len(df))
    st.write("**Brand populer:**", ", ".join(brands[:8]) + (" …" if len(brands) > 8 else ""))
    st.write("**Sub kategori:**", ", ".join(subcats))
    if "harga_idr" in df:
        st.write("**Rentang harga:** IDR {:,.0f} – {:,.0f}".format(float(df["harga_idr"].min()), float(df["harga_idr"].max())))
    st.caption("Catatan: Rekomendasi bersifat edukatif, bukan pengganti saran medis.")

st.caption("Tip: Ganti dataset via sidebar untuk data bisnis nyata.")