from __future__ import annotations
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class BeautyRecommenderV2:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._normalize_columns()
        self._prepare_vectors_and_norms()

    def _normalize_columns(self) -> None:
        # Lowercase semua nama kolom
        self.df.columns = [str(c).lower() for c in self.df.columns]

        required = [
            "nama_produk","brand","sub_kategori","jenis_kulit_kompatibel","rating",
            "harga_idr","size_ml","bahan_aktif","klaim","non_alkohol","non_fragrance",
            "aman_malassezia","komedogenik_score","deskripsi"
        ]
        for c in required:
            if c not in self.df.columns:
                if c in ("rating","harga_idr","size_ml","komedogenik_score"):
                    self.df[c] = 0
                elif c in ("non_alkohol","non_fragrance","aman_malassezia"):
                    self.df[c] = False
                else:
                    self.df[c] = ""

        # Casting tipe data
        self.df["rating"] = pd.to_numeric(self.df["rating"], errors="coerce").fillna(0.0)
        self.df["harga_idr"] = pd.to_numeric(self.df["harga_idr"], errors="coerce").fillna(0.0)
        self.df["size_ml"] = pd.to_numeric(self.df["size_ml"], errors="coerce").fillna(0.0)
        self.df["komedogenik_score"] = pd.to_numeric(self.df["komedogenik_score"], errors="coerce").fillna(0.0)

        # Koersi boolean (jika dibaca sebagai string)
        def to_bool_series(s: pd.Series) -> pd.Series:
            return s.astype(str).str.strip().str.lower().isin(["true","1","yes","y"])

        for bcol in ["non_alkohol","non_fragrance","aman_malassezia"]:
            self.df[bcol] = to_bool_series(self.df[bcol])

        # Pastikan teks NaN -> ""
        for tcol in ["nama_produk","brand","sub_kategori","jenis_kulit_kompatibel","bahan_aktif","klaim","deskripsi"]:
            self.df[tcol] = self.df[tcol].fillna("").astype(str)

    def _prepare_vectors_and_norms(self) -> None:
        # Korpus TF-IDF
        def row_to_text(row: pd.Series) -> str:
            parts = [
                row.get("nama_produk",""),
                row.get("brand",""),
                row.get("sub_kategori",""),
                row.get("jenis_kulit_kompatibel",""),
                row.get("bahan_aktif",""),
                row.get("klaim",""),
                row.get("deskripsi",""),
            ]
            return " ".join([str(p) for p in parts if p])

        self.df["_korpus"] = self.df.apply(row_to_text, axis=1)
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1)
        self.item_matrix = self.vectorizer.fit_transform(self.df["_korpus"])  # shape (N, D)

        # Normalisasi rating 0..1
        r = self.df["rating"].to_numpy(dtype=float)
        self.rating_norm = (r - r.min()) / (r.max() - r.min() + 1e-9)

        # Value-per-harga: ml / rupiah (semakin tinggi semakin baik)
        v = (self.df["size_ml"].replace(0, np.nan) / self.df["harga_idr"].replace(0, np.nan)).fillna(0.0).to_numpy()
        self.value_norm = (v - v.min()) / (v.max() - v.min() + 1e-9)

        # Cheapness (murah): semakin murah semakin tinggi
        h = self.df["harga_idr"].to_numpy(dtype=float)
        self.cheap_norm = (h.max() - h) / (h.max() - h.min() + 1e-9)

        # Token list untuk actives & claims
        self.df["_actives_list"] = (
            self.df["bahan_aktif"].fillna("").str.split("|").apply(lambda xs: [x.strip().lower() for x in xs if x])
        )
        self.df["_claims_list"] = (
            self.df["klaim"].fillna("").str.split("|").apply(lambda xs: [x.strip().lower() for x in xs if x])
        )

    @staticmethod
    def _count_overlap(a: List[str], b: List[str]) -> int:
        if not a or not b:
            return 0
        return len(set(a).intersection(set(b)))

    def _build_query(self,
                     jenis_kulit: str,
                     nama_produk: str = "",
                     brand_pref: Optional[str] = None,
                     sub_pref: Optional[str] = None,
                     wanted_actives: Optional[List[str]] = None,
                     wanted_claims: Optional[List[str]] = None) -> str:
        tokens: List[str] = []
        if nama_produk:
            tokens.append(str(nama_produk))
        if brand_pref and brand_pref.lower() != "tidak spesifik":
            tokens.append(str(brand_pref))
        if sub_pref and sub_pref.lower() != "tidak spesifik":
            tokens.append(str(sub_pref))
        if jenis_kulit:
            tokens.append(str(jenis_kulit))
        if wanted_actives:
            tokens.extend([str(a) for a in wanted_actives])
        if wanted_claims:
            tokens.extend([str(c) for c in wanted_claims])
        return " ".join(tokens)

    def recommend(self,
                  jenis_kulit: str,
                  nama_produk: str = "",
                  brand_pref: Optional[str] = None,
                  sub_pref: Optional[str] = None,
                  min_rating: float = 0.0,
                  price_range: Optional[Tuple[float, float]] = None,
                  must_free_alcohol: bool = False,
                  must_free_fragrance: bool = False,
                  must_malassezia_safe: bool = False,
                  wanted_actives: Optional[List[str]] = None,
                  avoid_actives: Optional[List[str]] = None,
                  wanted_claims: Optional[List[str]] = None,
                  only_skin_match: bool = False,
                  top_k: int = 10,
                  # bobot skor
                  w_content: float = 0.40,
                  w_rating: float = 0.20,
                  w_skin: float = 0.10,
                  w_brand: float = 0.05,
                  w_sub: float = 0.05,
                  w_claim: float = 0.07,
                  w_active: float = 0.08,
                  w_value: float = 0.05,
                  w_cheap: float = 0.00,
                  # penalti
                  penalty_avoid: float = 0.20,
                  penalty_komedo_per_point: float = 0.02,
                  komedo_threshold_for_acne: float = 2.0) -> pd.DataFrame:
        df = self.df.copy()

        # ===== FILTER dasar =====
        df = df[df["rating"] >= float(min_rating)]
        if price_range is not None:
            low, high = price_range
            df = df[(df["harga_idr"] >= float(low)) & (df["harga_idr"] <= float(high))]
        if must_free_alcohol:
            df = df[df["non_alkohol"] == True]
        if must_free_fragrance:
            df = df[df["non_fragrance"] == True]
        if must_malassezia_safe:
            df = df[df["aman_malassezia"] == True]
        if only_skin_match and jenis_kulit:
            df = df[df["jenis_kulit_kompatibel"].str.contains(jenis_kulit, case=False, na=False)]

        if df.empty:
            return self.df.head(0)

        # ===== Cosine similarity terhadap query pengguna =====
        query = self._build_query(
            jenis_kulit=jenis_kulit,
            nama_produk=nama_produk,
            brand_pref=brand_pref,
            sub_pref=sub_pref,
            wanted_actives=[a.lower() for a in (wanted_actives or [])],
            wanted_claims=[c.lower() for c in (wanted_claims or [])]
        )
        user_vec = self.vectorizer.transform([query])
        sim = cosine_similarity(user_vec, self.item_matrix[df.index]).ravel()

        # ===== sinyal kecocokan diskrit =====
        skin_match = df["jenis_kulit_kompatibel"].str.contains(jenis_kulit, case=False, na=False).astype(int).to_numpy()
        brand_match = (
            (df["brand"].str.lower() == (brand_pref or "").lower()).astype(int).to_numpy()
            if brand_pref and brand_pref.lower() != "tidak spesifik" else np.zeros(len(df))
        )
        sub_match = (
            (df["sub_kategori"].str.lower() == (sub_pref or "").lower()).astype(int).to_numpy()
            if sub_pref and sub_pref.lower() != "tidak spesifik" else np.zeros(len(df))
        )

        # ===== klaim & bahan aktif =====
        wanted_actives_lc = [a.lower() for a in (wanted_actives or [])]
        wanted_claims_lc = [c.lower() for c in (wanted_claims or [])]
        avoid_actives_lc = [a.lower() for a in (avoid_actives or [])]

        claim_hits = df["_claims_list"].apply(lambda xs: self._count_overlap(xs, wanted_claims_lc)).to_numpy(dtype=float)
        active_hits = df["_actives_list"].apply(lambda xs: self._count_overlap(xs, wanted_actives_lc)).to_numpy(dtype=float)

        claim_score = (claim_hits / max(1, len(wanted_claims_lc))) if len(wanted_claims_lc) > 0 else np.zeros(len(df))
        active_score = (active_hits / max(1, len(wanted_actives_lc))) if len(wanted_actives_lc) > 0 else np.zeros(len(df))

        has_avoid = df["_actives_list"].apply(lambda xs: 1 if len(set(xs).intersection(set(avoid_actives_lc))) > 0 else 0).to_numpy(dtype=float)
        penalty_avoid_vec = - penalty_avoid * has_avoid

        komedo = df["komedogenik_score"].to_numpy(dtype=float)
        if jenis_kulit and jenis_kulit.strip().lower() == "berjerawat":
            over = np.clip(komedo - float(komedo_threshold_for_acne), a_min=0, a_max=None)
            penalty_komedo = - penalty_komedo_per_point * over
        else:
            penalty_komedo = np.zeros(len(df))

        rating_norm_sub = self.rating_norm[df.index]
        value_norm_sub = self.value_norm[df.index]
        cheap_norm_sub = self.cheap_norm[df.index]

        # ===== skor akhir =====
        score = (
            w_content * sim +
            w_rating * rating_norm_sub +
            w_skin * skin_match +
            w_brand * brand_match +
            w_sub * sub_match +
            w_claim * claim_score +
            w_active * active_score +
            w_value * value_norm_sub +
            w_cheap * cheap_norm_sub +
            penalty_avoid_vec +
            penalty_komedo
        )

        # ===== alasan rekomendasi =====
        reasons: List[str] = []
        for i in range(len(df)):
            parts: List[str] = []
            if skin_match[i] == 1:
                parts.append(f"Cocok untuk {jenis_kulit}")
            if brand_match[i] == 1:
                parts.append("Brand sesuai")
            if sub_match[i] == 1:
                parts.append("Sub-kategori sesuai")
            if active_score[i] > 0:
                parts.append(f"Aktif cocok ({int(active_hits[i])}/{max(1,len(wanted_actives_lc))})")
            if claim_score[i] > 0:
                parts.append("Klaim sesuai")
            if value_norm_sub[i] >= 0.66:
                parts.append("Value per harga bagus")
            if penalty_avoid_vec[i] < 0:
                parts.append("(mengandung bahan yang dihindari)")
            if penalty_komedo[i] < 0:
                parts.append("(potensi komedogenik)")
            flags = []
            if bool(df.iloc[i]["non_alkohol"]): flags.append("no alcohol")
            if bool(df.iloc[i]["non_fragrance"]): flags.append("fragrance-free")
            if bool(df.iloc[i]["aman_malassezia"]): flags.append("malassezia-safe")
            if flags:
                parts.append(", ".join(flags))
            reasons.append("; ".join(parts))

        out = df.assign(
            skor=score,
            s_content=sim,
            s_rating=rating_norm_sub,
            s_skin=skin_match,
            s_brand=brand_match,
            s_sub=sub_match,
            s_claim=claim_score,
            s_active=active_score,
            s_value=value_norm_sub,
            s_cheap=cheap_norm_sub,
            p_avoid=penalty_avoid_vec,
            p_komedo=penalty_komedo,
            alasan=reasons
        ).sort_values("skor", ascending=False)

        # Kolom output
        base_cols = [
            "nama_produk","brand","sub_kategori","rating","harga_idr","size_ml","jenis_kulit_kompatibel",
            "bahan_aktif","klaim","non_alkohol","non_fragrance","aman_malassezia","komedogenik_score",
            "skor","alasan","deskripsi"
        ]
        extra_cols = [
            "s_content","s_rating","s_skin","s_brand","s_sub","s_claim","s_active","s_value","s_cheap","p_avoid","p_komedo"
        ]
        for c in base_cols + extra_cols:
            if c not in out.columns:
                out[c] = None
        return out[base_cols + extra_cols]