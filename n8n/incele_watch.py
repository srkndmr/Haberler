#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linkten Haber İncele — izleyici.
WP'deki iş kuyruğunu (haberler/v1/kuyruk) yoklar; her iş için:
  - metin: yapıştırılan varsa onu, yoksa URL'den çekmeyi dener,
  - hibrit-pipeline.process_one ile Opus analizi + otomatik-taslak dosya,
  - işi 'hazir' (post_id ile) / 'atlandi' / 'hata' olarak işaretler.

Kullanım:
  cd n8n && . ./scheduler/.env && python3 incele_watch.py --once      # tek tur
  python3 incele_watch.py --loop [saniye]                              # sürekli (vars. 20s)
"""
import os, re, sys, json, time, base64, html, importlib.util, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("hib", os.path.join(HERE, "hibrit-pipeline.py"))
hib = importlib.util.module_from_spec(spec); spec.loader.exec_module(hib)

WP   = os.environ.get("WP_URL", "http://localhost:8091")
USER = os.environ.get("WP_USER", "pipeline-bot")
APP  = os.environ.get("WP_APP_PASS")
_AUTH = "Basic " + base64.b64encode(f"{USER}:{APP}".encode()).decode()

def _req(path, method="GET", data=None):
    url = f"{WP}/wp-json/haberler/v1{path}"
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method,
        headers={"Authorization": _AUTH, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())

def durum_yaz(job_id, durum, post_id=0, not_=""):
    try:
        _req("/kuyruk/durum", "POST", {"job_id": job_id, "durum": durum, "post_id": post_id, "not": not_})
    except Exception as e:
        print(f"    (durum yazılamadı: {e})")

def metin_cek(url):
    """URL'den en iyi çabayla gövde metni + <title> çıkar. Engellenirse ('', '')."""
    try:
        r = urllib.request.urlopen(urllib.request.Request(url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}), timeout=20)
        raw = r.read().decode("utf-8", "replace")
    except Exception as e:
        return "", "", f"metin çekilemedi ({e})"
    baslik = ""
    mt = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    if mt: baslik = html.unescape(re.sub(r"\s+", " ", mt.group(1))).strip()
    # <article> varsa onu, yoksa tüm body
    mb = re.search(r"<article[^>]*>(.*?)</article>", raw, re.I | re.S) or re.search(r"<body[^>]*>(.*?)</body>", raw, re.I | re.S)
    govde = mb.group(1) if mb else raw
    govde = re.sub(r"(?is)<(script|style|nav|header|footer|form|aside)[^>]*>.*?</\1>", " ", govde)
    govde = re.sub(r"(?s)<[^>]+>", " ", govde)
    govde = html.unescape(re.sub(r"[ \t]+", " ", govde))
    govde = re.sub(r"\n\s*\n\s*\n+", "\n\n", govde).strip()
    return govde[:8000], baslik, ""

def is_gor(j):
    job_id = j.get("job_id"); url = (j.get("url") or "").strip()
    baslik = (j.get("baslik") or "").strip(); metin = (j.get("metin") or "").strip()
    print(f"\n>>> iş {job_id} | {(baslik or url)[:70]}")
    durum_yaz(job_id, "isleniyor")
    kaynak_ad = ""
    # Metin yoksa URL'den çekmeyi dene
    if not metin and url:
        metin, cekilen_baslik, hata = metin_cek(url)
        if not baslik: baslik = cekilen_baslik
        if not metin:
            print(f"    ↷ {hata} — metin yapıştırılmalı");
            durum_yaz(job_id, "atlandi", not_="Site metni engelledi; lütfen haber metnini yapıştırın.")
            return
    if url:
        try: kaynak_ad = re.sub(r"^www\.", "", url.split("/")[2])
        except Exception: kaynak_ad = "kaynak"
    if not baslik:
        baslik = (metin[:80] + "…") if metin else (url or "Başlıksız")
    kaynaklar = [{"kaynak_adi": kaynak_ad or "kaynak", "orijinal_url": hib.resolve(url) if url else "", "yayin_tarihi": ""}]
    try:
        pid = hib.process_one(baslik, metin, kaynaklar)
    except Exception as e:
        print(f"    ✗ hata: {e}"); durum_yaz(job_id, "hata", not_=str(e)[:180]); return
    if pid:
        durum_yaz(job_id, "hazir", post_id=pid, not_="")
        print(f"    ✓ dosya #{pid}")
    else:
        durum_yaz(job_id, "atlandi", not_="Belirgin sorun yok ya da somut iddia yok — dosya oluşturulmadı.")
        print("    ↷ atlandı (sorun yok/iddia yok)")

def tur():
    try:
        bekleyen = _req("/kuyruk")
    except Exception as e:
        print(f"kuyruk okunamadı: {e}"); return 0
    for j in bekleyen:
        is_gor(j)
        time.sleep(2)
    return len(bekleyen)

def main():
    if not APP: print("HATA: WP_APP_PASS gerekli."); sys.exit(1)
    if "--loop" in sys.argv:
        try: bekle = int(sys.argv[sys.argv.index("--loop") + 1])
        except Exception: bekle = 20
        print(f"izleyici döngüde (her {bekle}s)…")
        while True:
            n = tur()
            if n: print(f"  {n} iş işlendi.")
            time.sleep(bekle)
    else:
        n = tur(); print(f"\nBitti: {n} bekleyen iş işlendi.")

if __name__ == "__main__":
    main()
