# README — Sistem Rekomendasi Kecantikan

Aplikasi ini adalah **sistem rekomendasi produk kecantikan** berbasis _content & preference_ dengan antarmuka **Streamlit**. Pengguna bisa memfilter berdasarkan **jenis kulit, brand, sub-kategori, rating, harga**, serta preferensi lanjut seperti **bahan aktif yang diinginkan/dihindari, klaim, dan opsi free‑from**. Hasil rekomendasi diberi **skor multi‑kriteria** disertai **alasan** dan opsi **breakdown skor per komponen**.

UI/UX mengusung **nuansa pink** dengan micro‑animations, pilihan tampilan **Kartu** atau **Tabel**, **chips** ringkasan filter, tombol **Reset filter**, dan tombol **Unduh CSV** untuk hasil.

---

## ✨ Fitur Utama

- **Filter utama:** Jenis kulit, nama produk (kata kunci), brand, sub‑kategori, rating minimum, rentang harga.
- **Preferensi lanjut:**

  - **Bahan aktif** yang ingin dicari (mis. _niacinamide, centella, AHA_).
  - **Bahan aktif** yang ingin dihindari (akan diberi **penalti** pada skor).
  - **Klaim/tujuan** (mis. _brightening, soothing, oil control_).
  - **Free‑from:** _non_alkohol_, _non_fragrance_, _aman_malassezia_.
  - **Mode only skin match** untuk menampilkan hanya produk yang cocok jenis kulit.

- **Penilaian multi‑kriteria (scoring):** gabungan kemiripan konten, rating, kecocokan jenis kulit, brand/sub, kecocokan klaim & aktif, value per harga, dan murah.
- **Explainability:** tampilkan **alasan** + opsi **breakdown skor** per komponen.
- **UI Pink:** card hover animation, gradient header, badge, chips ringkasan filter, toast sukses.
- **Ekspor:** hasil rekomendasi bisa diunduh sebagai **CSV**.

---

## 🧱 Arsitektur Singkat

- **`app.py`**: antarmuka Streamlit (tema pink, input filter, render kartu/tabel, unduh CSV).
- **`recommender.py`**: logika rekomendasi (`BeautyRecommenderV2`) — normalisasi data, TF‑IDF, kalkulasi skor, dan alasan.
- **`data/produk_kecantikan_v2.csv`**: dataset contoh (bisa diganti dengan data Anda).

---

## 📂 Struktur Proyek

```
rekomendasi-kecantikan/
├─ app.py                     # Aplikasi Streamlit (UI pink)
├─ recommender.py             # Model rekomendasi multi-kriteria (V2)
├─ requirements.txt           # Dependensi Python
└─ data/
   └─ produk_kecantikan_v2.csv  # Dataset contoh (bisa diganti)
```

---

## 🔧 Instalasi

1. **Opsional**: buat virtual env

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

2. **Install dependensi**

```bash
pip install -r requirements.txt
```

---

## ▶️ Menjalankan

```bash
streamlit run app.py
```

Aplikasi terbuka di browser (biasanya `http://localhost:8501`).

---

## 📊 Dataset (Skema CSV)

**Kolom minimal wajib** (huruf kecil semua; gunakan `|` sebagai pemisah multi‑nilai):

| Kolom                    | Jenis     | Wajib      | Contoh                        | Keterangan                            |                          |                                           |     |
| ------------------------ | --------- | ---------- | ----------------------------- | ------------------------------------- | ------------------------ | ----------------------------------------- | --- |
| `nama_produk`            | string    | ✓          | _Miraculous Refining Toner_   | Nama item                             |                          |                                           |     |
| `brand`                  | string    | ✓          | _Avoskin_                     | Merek                                 |                          |                                           |     |
| `sub_kategori`           | string    | ✓          | _Toner_, _Serum_, _Sunscreen_ | Kategori produk                       |                          |                                           |     |
| `jenis_kulit_kompatibel` | string    | ✓          | \*Kering                      | Normal                                | Sensitif\*               | Daftar jenis kulit yang cocok, dipisah \` | \`  |
| `rating`                 | float 0–5 | ✓          | `4.5`                         | Rating agregat                        |                          |                                           |     |
| `harga_idr`              | integer   | ✓          | `162000`                      | Harga Rupiah (tanpa titik/koma)       |                          |                                           |     |
| `size_ml`                | float/int | ✓          | `100`                         | Ukuran (ml/g). Isi `0` jika tidak ada |                          |                                           |     |
| `bahan_aktif`            | string    | ✓          | \*Niacinamide                 | AHA                                   | PHA\*                    | Bahan aktif, dipisah \`                   | \`  |
| `klaim`                  | string    | ✓          | \*Brightening                 | Soothing\*                            | Klaim/tujuan, dipisah \` | \`                                        |     |
| `non_alkohol`            | bool      | disarankan | `True/False`                  | _Free‑from_                           |                          |                                           |     |
| `non_fragrance`          | bool      | disarankan | `True/False`                  | _Free‑from_                           |                          |                                           |     |
| `aman_malassezia`        | bool      | disarankan | `True/False`                  | _Free‑from_                           |                          |                                           |     |
| `komedogenik_score`      | float     | disarankan | `1–3`                         | Perkiraan potensi komedogenik         |                          |                                           |     |
| `deskripsi`              | string    | opsional   | teks                          | Ringkasan singkat                     |                          |                                           |     |

**Catatan:**

- Nilai boolean boleh `True/False`, `1/0`, atau `Yes/No` — aplikasi akan mengonversi otomatis.
- Jika ingin menambahkan kolom lain (mis. `source_url` untuk audit), tidak masalah — kolom tak dikenal akan diabaikan.

**Cuplikan CSV:**

```csv
nama_produk,brand,sub_kategori,jenis_kulit_kompatibel,rating,harga_idr,size_ml,bahan_aktif,klaim,non_alkohol,non_fragrance,aman_malassezia,komedogenik_score,deskripsi
"Miraculous Refining Toner",Avoskin,Toner,"Normal|Kombinasi|Berminyak",4.8,162000,100,"AHA|BHA|PHA|PGA|Niacinamide","Exfoliating|Brightening",True,False,True,2,"Toner eksfoliasi lembut"
```

---

## 🧠 Cara Kerja Rekomendasi

1. **Normalisasi data**: tipe numerik, boolean, dan teks.
2. **Representasi konten**: buat korpus gabungan (_nama, brand, sub_kategori, kulit, aktif, klaim, deskripsi_) → **TF‑IDF**.
3. **Query pengguna**: dibentuk dari filter utama (jenis kulit, brand/sub pilihan, kata kunci, aktif & klaim yang diinginkan).
4. **Kemiripan**: **cosine similarity** antara query dan item.
5. **Sinyal tambahan**: kecocokan jenis kulit, brand/sub, kecocokan klaim & aktif, serta normalisasi **rating**, **value/price (ml per rupiah)**, dan **cheapness**.
6. **Penalti**: jika mengandung **bahan dihindari** atau **komedogenik** (khusus kulit **Berjerawat**, di atas ambang tertentu).
7. **Skor akhir**: penjumlahan berbobot dari semua komponen, lalu diurutkan menurun.

### Rumus Skor (ringkas)

`score = w_content·sim + w_rating·rating + w_skin·skin + w_brand·brand + w_sub·sub + w_claim·claim + w_active·active + w_value·value + w_cheap·cheap - penalty_avoid - penalty_komedo`

Bobot default (dapat diubah di UI):

- `w_content=0.40`, `w_rating=0.20`, `w_skin=0.10`, `w_brand=0.05`, `w_sub=0.05`, `w_claim=0.07`, `w_active=0.08`, `w_value=0.05`, `w_cheap=0.00`
- Penalti: `penalty_avoid=0.20`, `penalty_komedo_per_point=0.02` (aktif jika jenis kulit **Berjerawat** & skor komedogenik > ambang, default `2.0`).

Hasil dilengkapi **alasan** (mis. _Cocok untuk Berjerawat; Aktif cocok (2/3); Value per harga bagus; no alcohol, fragrance‑free_). Anda juga bisa menyalakan **breakdown skor** untuk melihat kontribusi tiap komponen (`s_content, s_rating, s_skin, ...`).

---

## 🖥️ Panduan UI/UX

- **Sidebar — Preferensi**

  - **Jenis Kulit**: Kering, Berminyak, Kombinasi, Normal, Sensitif, Berjerawat.
  - **Nama Produk**: kata kunci bebas (mis. _niacinamide, retinol_).
  - **Brand/Sub‑kategori**: pilih spesifik atau _Tidak spesifik_.
  - **Rating Minimum** dan **Rentang Harga** (IDR).
  - **Free‑from**: centang untuk hanya menampilkan yang memenuhi.
  - **Bahan aktif/Klaim**: pilih multi‑opsi; **Hindari bahan** memberi penalti.
  - **Only skin match**: tampilkan item yang memuat jenis kulit Anda.
  - **Bobot & Penalti**: geser untuk menyesuaikan logika skor.
  - **Top‑K**: jumlah item teratas yang ditampilkan.

- **Header**

  - **Reset filter**: membersihkan semua input dan memuat ulang aplikasi.

- **Hasil Rekomendasi**

  - **Mode**: **Kartu** (2 kolom) atau **Tabel**.
  - **Kartu** berisi: sub‑kategori, **Skor**, nama, brand, rating (★), **harga**, **ukuran**, jenis kulit, dan **alasan**.
  - **Breakdown skor** (opsional) menambahkan kolom komponen ke tabel/kartu.
  - **Unduh CSV**: menyimpan hasil yang sedang ditampilkan.

- **Ringkasan Dataset**

  - Menampilkan metrik jumlah produk, daftar brand & sub‑kategori, serta rentang harga.

---

## ✅ Praktik Terbaik Menyiapkan Data

- Tulis **harga** sebagai angka murni (mis. `162000`, bukan `Rp 162.000`).
- Gunakan pemisah `|` untuk multi‑nilai (aktif/klaim/kulit).
- Isi **0** pada `size_ml` jika tidak diketahui.
- Isi boolean sebagai `True/False` atau `1/0` atau `Yes/No`.
- Gunakan **huruf kecil** pada nama kolom agar konsisten.

---

## 🚀 Performa & Skala

- Dataset puluhan–ratusan item berjalan cepat dengan TF‑IDF.
- Untuk ribuan item: aktifkan **cache** (sudah digunakan di `@st.cache_data`) dan pertimbangkan berpindah ke **embeddings** (Sentence Transformers) + penyimpanan vektor.

---

## 🛠️ Troubleshooting

- **Error: kolom wajib tidak ditemukan**
  Pastikan CSV Anda memiliki kolom minimal: `nama_produk, brand, sub_kategori, jenis_kulit_kompatibel, rating, harga_idr, size_ml, bahan_aktif, klaim`.

- **Boolean tidak terbaca**
  Aplikasi mengonversi otomatis dari `"true"/"1"/"yes"` (case‑insensitive). Cek ejaan.

- **Angka terdeteksi sebagai teks**
  Pastikan tidak ada tanda `Rp`, titik, atau koma pada `harga_idr`. Gunakan integer murni.

- **Skor terasa tidak wajar**
  Coba turunkan `w_content` dan naikkan `w_active`/`w_claim` sesuai kebutuhan. Untuk kulit **Berjerawat**, atur `komedo_threshold_for_acne` dan `penalty_komedo_per_point`.

- **Tabel tidak muncul / hasil kosong**
  Longgarkan filter (turunkan rating minimum, hilangkan pembatas _free‑from_, atau matikan _only skin match_).

---

## 🤝 Kontribusi & Kustomisasi

- Anda dapat menambah field baru di CSV (mis. `source_url`) tanpa mengubah kode.
- Ingin menambah **gambar produk**? Tambahkan kolom `image_url` di CSV dan render di kartu (modifikasi kecil pada `app.py`).
- Formula skor dan bobot bisa diubah dari UI atau langsung di `recommender.py`.

---

## ⚖️ Disclaimer

Rekomendasi bersifat **edukatif**. Selalu periksa **komposisi resmi** dan **kondisi kulit pribadi**. Jika ragu, konsultasikan dengan tenaga profesional (dermatologis).

---

## 🗺️ Roadmap (Opsional)

- Dukungan **embeddings** untuk pencarian semantik yang lebih akurat.
- **Bandingkan produk** (shortlist & compare) dengan highlight per komponen skor.
- Integrasi **gambar** dan **tautan langsung** ke halaman official.

---

## Bug

- Masih Terdapat Bug ketika Menambahkan Url Gambar Untuk Produk
