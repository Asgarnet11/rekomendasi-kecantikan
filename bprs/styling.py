PINK_AND_CARD_CSS = """
<style>
  :root{--pink-1:#ffe6f1;--pink-3:#ff8ab8;--pink-4:#ff5fa2}
  .pink-bg{background:radial-gradient(900px 400px at 0% 0%, var(--pink-1), transparent 60%)}
  .stButton>button{background:linear-gradient(90deg,var(--pink-4),var(--pink-3));color:#fff;border:none;border-radius:999px;padding:.55rem 1rem}
  .stButton>button:hover{transform:translateY(-1px);box-shadow:0 8px 22px rgba(255,95,162,.25)}
  .chip{display:inline-flex;gap:.35rem;padding:.2rem .6rem;border-radius:999px;background:#fff0f7;border:1px solid #ffd6e8;color:#7d2a4f;font-size:.8rem;font-weight:600;margin-right:.35rem;margin-bottom:.35rem}
  .product-card {background:#fff;border:1px solid #ffd6e8;border-radius:16px;margin-bottom:1.25rem;box-shadow:0 4px 16px rgba(255,138,184,.08);transition:all .3s ease;height:100%;display:flex;flex-direction:column;position:relative;overflow:hidden}
  .product-card:hover{transform:translateY(-5px);box-shadow:0 8px 24px rgba(255,95,162,.15);border-color:var(--pink-3)}
  .product-card .image-container{position:relative;width:100%;height:250px;overflow:hidden;border-bottom:1px solid #ffd6e8;background:linear-gradient(45deg,#fff5f9,#fff)}
  .product-card .image-container img{width:100%;height:100%;object-fit:contain;transition:transform .3s ease;padding:10px}
  .product-card:hover .image-container img{transform:scale(1.05)}
  .product-card .content-wrapper{padding:1.25rem;display:flex;flex-direction:column;gap:.75rem;flex:1}
  .product-card .header{display:flex;justify-content:space-between;align-items:center}
  .product-card .brand{font-size:.85rem;color:var(--pink-4);font-weight:600;text-transform:uppercase;letter-spacing:.5px}
  .product-card .tag.rating{background:#fff0f7;color:var(--pink-4);padding:.25rem .75rem;border-radius:999px;font-weight:600;font-size:.85rem}
  .product-card .product-name{font-size:1.15rem;font-weight:700;color:#2c2c2c;margin:0;line-height:1.4}
  .product-card .price-section{display:flex;align-items:baseline;gap:.75rem;padding-bottom:.5rem;border-bottom:1px dashed #ffd6e8}
  .product-card .price{font-size:1.25rem;font-weight:700;color:var(--pink-4)}
  .product-card .size{font-size:.9rem;color:#888}
  .product-card .info-section{display:flex;flex-direction:column;gap:.75rem}
  .product-card .info-row{display:flex;flex-direction:column;gap:.25rem}
  .product-card .info-row .label{font-size:.85rem;font-weight:600;color:#666}
  .product-card .info-row .value{font-size:.9rem;color:#2c2c2c;line-height:1.5}
  .product-card .score{margin-top:auto;padding-top:.75rem;border-top:1px solid #ffd6e8}
  .product-card .match-score{text-align:right;font-size:.9rem;font-weight:600;color:var(--pink-4);background:linear-gradient(90deg,transparent,#fff0f7);padding:.5rem;border-radius:8px}
</style>
"""
