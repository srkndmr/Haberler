#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini (Google Search grounding) ile analiz et -> WordPress'e TASLAK yaz.
Sonuç wp-admin'de 'Otomatik Taslak' olarak görünür (insan/hukuk onayı bekler).

Kullanım:
  cd n8n && . ./scheduler/.env && python3 gemini-pipeline.py "BAŞLIK" ["bağlam"]
Argümansız: Google News'ten güncel bir FETÖ haberi çeker.
"""
import os, re, sys, json, time, base64, importlib.util, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
gem = _load("gem", "gemini-analiz.py")
ayl = _load("ayl", "aylik-tarama.py")

KEY = os.environ.get("GEMINI_API_KEY"); MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
WP = os.environ.get("WP_URL", "http://localhost:8091"); USER = os.environ.get("WP_USER", "pipeline-bot")
APP = os.environ.get("WP_APP_PASS")

def resolve(u):
    """grounding redirect linkini gerçek mecra URL'sine çöz (best-effort)."""
    u = (u or "").split(",")[0].strip()  # Gemini bazen birden çok URL'yi virgülle birleştirir
    if not u or "grounding-api-redirect" not in u: return u
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=12)
        final = r.geturl(); r.close()
        return final or u
    except Exception:
        return u

def wp_create(title, analiz, kaynaklar):
    valid = {"dogru","kismen_dogru","yanlis","dogrulanamaz","mesnetsiz","gorus"}
    iddialar = [{"iddia_metni": str(x.get("iddia_metni",""))[:2000],
                 "siniflandirma": x.get("siniflandirma") if x.get("siniflandirma") in valid else "dogrulanamaz",
                 "gerekce": str(x.get("gerekce","")), "dayanak_kaynak_url": resolve(x.get("dayanak_kaynak_url","") or "")}
                for x in analiz.get("iddialar", [])]
    isim = "hayir" if analiz.get("isim_verilen_suclama") == "hayir" else "evet"
    payload = {"title": title[:120], "status": "draft",
        "content": "",
        "meta": {"haberler_ozet": analiz.get("ozet",""),
                 "haberler_genel_degerlendirme": analiz.get("genel_degerlendirme",""),
                 "haberler_isim_verilen_suclama": isim,
                 "haberler_isim_suclama_gerekce": analiz.get("isim_verilen_suclama_gerekce",""),
                 "haberler_kaynaklar": json.dumps(kaynaklar, ensure_ascii=False),
                 "haberler_iddialar": json.dumps(iddialar, ensure_ascii=False)}}
    auth = base64.b64encode(f"{USER}:{APP}".encode()).decode()
    req = urllib.request.Request(f"{WP}/wp-json/wp/v2/posts", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def main():
    if not KEY or not APP: print("HATA: GEMINI_API_KEY ve WP_APP_PASS gerekli."); sys.exit(1)
    if len(sys.argv) > 1:
        baslik = sys.argv[1]; metin = sys.argv[2] if len(sys.argv) > 2 else ""
    else:
        items = ayl.google_news_search(ayl.ANAHTAR_SORGU)
        if not items: print("Google News'ten haber gelmedi."); sys.exit(1)
        baslik = items[0]["baslik"]; metin = items[0].get("ozet", "")
    print(f"BAŞLIK: {baslik}\nGemini grounded analiz...")
    # Gemini grounded kararsız olabilir (bazen boş döner); dolu sonuç gelene dek birkaç kez dene
    analiz, sources, queries = {}, [], []
    for attempt in range(4):
        analiz, sources, queries = gem.gemini_grounded(baslik, metin, KEY, MODEL)
        if analiz.get("ozet") or analiz.get("iddialar"):
            break
        print(f"  (boş sonuç, tekrar {attempt + 1}/4)")
        time.sleep(5)
    # Hâlâ boşsa WP'ye YAZMA (boş dosya oluşturma)
    if not analiz.get("ozet") and not analiz.get("iddialar"):
        print("✗ Gemini yapılandırılmış sonuç döndürmedi; WP'ye yazılmadı. Sonra tekrar denenebilir.")
        sys.exit(2)
    # kaynakları gerçek URL'ye çöz
    kaynaklar = []
    for t, u in sources[:8]:
        kaynaklar.append({"kaynak_adi": t or "kaynak", "orijinal_url": resolve(u), "yayin_tarihi": ""})
    print(f"  arama: {' | '.join(queries)}")
    print(f"  iddia sayısı: {len(analiz.get('iddialar', []))} | kaynak: {len(kaynaklar)}")
    res = wp_create(baslik, analiz, kaynaklar)
    pid = res.get("id")
    print(f"\n✓ WordPress taslağı oluşturuldu: ID={pid} (durum: draft → otomatik-taslak)")
    print(f"  Admin: {WP}/wp-admin/post.php?post={pid}&action=edit")

if __name__ == "__main__":
    main()
