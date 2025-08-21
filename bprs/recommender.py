from __future__ import annotations
from pathlib import Path
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from .utils import read_csv_flex
from .images import get_product_image_data_uri, get_product_image

class BeautyProductRecommendationSystem:
    def _init_(self):
        # dibiarkan seperti semula (tidak diubah) sesuai permintaan
        self.products_df = None
        self.tfidf_vectorizer = None
        self.similarity_matrix = None
        self.scaler = StandardScaler()

    # ============== Parser jenis kulit (dipertahankan) ==============
    def _canonicalize_skin_token(self, raw: str) -> str | None:
        if not raw:
            return None
        t = str(raw).lower().strip()
        t = re.sub(r"\bkulit\b", "", t).strip()
        t = re.sub(r"\bdan\b", "", t).strip()

        CANON = {"berjerawat","berminyak","kering","sensitif","normal","kombinasi","kusam","semua"}
        if t in CANON:
            return t

        if "semua" in t:
            return "semua"
        if "acne" in t or "jerawat" in t:
            return "berjerawat"
        if "oily" in t or "berminyak" in t or "minyak" in t:
            return "berminyak"
        if "dry" in t or "kering" in t:
            return "kering"
        if "sensitive" in t or "sensitif" in t:
            return "sensitif"
        if "comb" in t or "kombinasi" in t:
            return "kombinasi"
        if "dull" in t or "kusam" in t:
            return "kusam"
        return None

    def _parse_skin_tokens(self, s) -> set[str]:
        if s is None or (isinstance(s, float) and pd.isna(s)):
            return {"semua"}
        text = str(s).lower()
        if "semua jenis kulit" in text or re.search(r"\bsemua\b", text):
            return {"semua"}
        parts = re.split(r"\s*(?:,|/|\||;|&|\bdan\b)\s*", text)
        toks = set()
        for p in parts:
            tok = self._canonicalize_skin_token(p)
            if tok:
                toks.add(tok)
        if not toks:
            if "acne" in text or "jerawat" in text:
                toks.add("berjerawat")
            if "oily" in text or "berminyak" in text:
                toks.add("berminyak")
            if "dry" in text or "kering" in text:
                toks.add("kering")
            if "sensitive" in text or "sensitif" in text:
                toks.add("sensitif")
            if "comb" in text or "kombinasi" in text:
                toks.add("kombinasi")
            if "dull" in text or "kusam" in text:
                toks.add("kusam")
        return toks if toks else {"semua"}

    def _normalize_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        def norm(c):
            c = str(c).strip()
            return c.lower().replace(".", "").replace(" ", "_")
        df.rename(columns={c: norm(c) for c in df.columns}, inplace=True)
        alias_to_canonical = {
            "id": "id","nama_produk": "nama_produk","product_name": "nama_produk",
            "brand": "brand","merek": "brand",
            "sub_kategori": "sub_kategori","subkategori": "sub_kategori",
            "manfaat": "Manfaat",
            "jenis_kulit_kompatibel": "jenis_kulit_kompatibel","skin_type": "jenis_kulit_kompatibel",
            "rating": "rating","deskripsi": "deskripsi","description": "deskripsi",
            "harga_idr": "harga_idr","harga": "harga_idr","price": "harga_idr",
            "size_ml": "size_ml","size": "size_ml",
            "bahan_aktif": "bahan_aktif","active_ingredients": "bahan_aktif",
            "klaim": "klaim","klaim_": "klaim",
        }
        for col in list(df.columns):
            if col in alias_to_canonical:
                canon = alias_to_canonical[col]
                if col != canon and canon not in df.columns:
                    df.rename(columns={col: canon}, inplace=True)

        required = ["id","nama_produk","brand","sub_kategori","Manfaat","jenis_kulit_kompatibel",
                    "rating","deskripsi","harga_idr","size_ml","bahan_aktif","klaim"]
        for col in required:
            if col not in df.columns:
                df[col] = np.nan if col in ("rating","harga_idr","size_ml") else ""
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df["harga_idr"] = pd.to_numeric(df["harga_idr"].astype(str).str.replace(r"[^0-9]", "", regex=True), errors="coerce")
        df["size_ml"] = pd.to_numeric(df["size_ml"], errors="coerce")
        for c in ["nama_produk","brand","sub_kategori","Manfaat","jenis_kulit_kompatibel","deskripsi","bahan_aktif","klaim"]:
            df[c] = df[c].astype(str)
        return df

    # Expose helper dari modul images agar API tetap sama
    def get_product_image(self, brand: str, product_name: str) -> str:
        return get_product_image(brand, product_name)

    def get_product_image_data_uri(self, brand: str, sub_kategori: str, dataset_url: str | None = None) -> str:
        return get_product_image_data_uri(brand, sub_kategori, dataset_url)

    # ================== Data loading & preprocessing ==================
    def load_and_preprocess_data(self, csv_file_path: str | None = None, uploaded_df: pd.DataFrame | None = None):
        if uploaded_df is not None:
            df = uploaded_df.copy()
        else:
            if csv_file_path is None:
                csv_file_path = str(Path(__file__).resolve().parents[1] / "data" / "products_seed.csv")
            df = read_csv_flex(csv_file_path)
        self.products_df = self._normalize_schema(df)
        self.products_df = self.products_df.dropna(subset=['jenis_kulit_kompatibel', 'sub_kategori'])
        self.products_df['combined_features'] = (
            self.products_df['jenis_kulit_kompatibel'].fillna('') + ' ' +
            self.products_df['sub_kategori'].fillna('') + ' ' +
            self.products_df['Manfaat'].fillna('') + ' ' +
            self.products_df['klaim'].fillna('')
        ).str.lower()
        self.products_df["skin_tokens"] = self.products_df["jenis_kulit_kompatibel"].apply(self._parse_skin_tokens)

    def build_similarity_matrix(self):
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words=None, ngram_range=(1, 2))
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.products_df['combined_features'])
        self.similarity_matrix = cosine_similarity(tfidf_matrix)

    def normalize_skin_type(self, user_skin_type):
        skin_type_mapping = {
            'berjerawat': ['berjerawat', 'jerawat', 'acne'],
            'berminyak': ['berminyak', 'oily', 'minyak'],
            'kering': ['kering', 'dry'],
            'sensitif': ['sensitif', 'sensitive'],
            'normal': ['normal'],
            'kombinasi': ['kombinasi', 'combination'],
            'kusam': ['kusam', 'dull']
        }
        user_skin_type_lower = str(user_skin_type).lower()
        for standard_type, variants in skin_type_mapping.items():
            if any(variant in user_skin_type_lower for variant in variants):
                return standard_type
        return user_skin_type_lower

    def find_compatible_products(self, user_skin_type):
        normalized_skin_type = self.normalize_skin_type(user_skin_type)
        df = self.products_df
        if "skin_tokens" not in df.columns:
            df = df.copy()
            df["skin_tokens"] = df["jenis_kulit_kompatibel"].apply(self._parse_skin_tokens)
        if normalized_skin_type == "semua":
            compatible = df.copy()
        else:
            compatible = df[df["skin_tokens"].apply(lambda s: "semua" in s or normalized_skin_type in s)].copy()
        if compatible.empty:
            compatible = df[df['combined_features'].str.contains(normalized_skin_type, case=False, na=False)].copy()
        return compatible

    def rank_on_subset(self, subset_indices: list[int], top_n=5):
        if not subset_indices:
            return []
        sim_scores = []
        for idx in subset_indices:
            scores = self.similarity_matrix[idx][subset_indices]
            avg_score = float(np.mean(scores)) if len(scores) else 0.0
            sim_scores.append((idx, avg_score))
        ranked = []
        for idx, sim_score in sim_scores:
            product = self.products_df.loc[idx]
            final_score = (sim_score * 0.6) + (float(product['rating']) / 5.0 * 0.4)
            ranked.append((idx, final_score, product))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:top_n]
