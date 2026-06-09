#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEK SEFERLİK aylık backfill: belirli bir ay için konuya özel haber taraması.
RSS son ~100 haberi verdiğinden, ay genelini taramak için Google News RSS ARAMA kullanır.
Akış: Google News arama -> ay filtresi -> dedup -> Claude analiz -> WP otomatik-taslak.

Kullanım:
  cd n8n/scheduler && . ./.env && cd .. && \
  AY=Jun YIL=2026 LIMIT=10 ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY WP_APP_PASS=$WP_APP_PASS \
  python3 aylik-tarama.py
"""
import os, re, sys, json, base64, urllib.parse, urllib.request, xml.etree.ElementTree as ET

ANAHTAR_SORGU = '(fetö OR fethullahçı OR fetullahçı OR gülen OR bylock OR "fetö/pdy" OR "15 temmuz")'
UA = {"User-Agent": "Mozilla/5.0 (HaberlerPipeline/1.0)"}

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()

def google_news_search(query, gun="45d"):
    q = urllib.parse.quote(f"{query} when:{gun}")
    url = f"https://news.google.com/rss/search?q={q}&hl=tr&gl=TR&ceid=TR:tr"
    items = []
    root = ET.fromstring(fetch(url))
    for it in root.iter("item"):
        src = it.find("source")
        items.append({
            "baslik": (it.findtext("title") or "").strip(),
            "orijinal_url": (it.findtext("link") or "").strip(),
            "ozet": re.sub("<[^>]+>", "", it.findtext("description") or "").strip(),
            "yayin_tarihi": (it.findtext("pubDate") or "").strip(),
            "kaynak_adi": (src.text.strip() if src is not None and src.text else "Google News"),
        })
    return items

def analyze_with_claude(item, api_key, model):
    sysp = ("Sen kıdemli bir doğruluk denetimi analistisin; medya hukuku editörü gibi düşünürsün ama "
            "hâkim değilsin. Türkçe haber metnini inceleyip insan editör/hukuk danışmanının önüne gelecek "
            "AKICI, OKUNABİLİR bir taslak hazırlarsın. Mekanik tek cümlelik ifadelerden kaçın; gerekçeli, "
            "bağlamı açıklayan, ölçülü bir hukuk-gazetecilik dili kullan. İlkeler: kanıt yoksa dogrulanamaz; "
            "olgu/yorum ayrımı (yorum -> gorus); masumiyet karinesi (suç/üyelik isnatları kaynağa atfedilir, "
            "olgu gibi ileri sürülmez); nötr dil, uydurma yok. Alanlar: ozet (3-5 cümle bağlamlı paragraf); "
            "genel_degerlendirme (3-5 cümle tarafsız hukuki-gazetecilik değerlendirmesi: dayanak/delil durumu, "
            "olgu-yorum dengesi, eksik bağlam; hüküm verme); iddialar (iddia_metni, siniflandirma "
            "[dogru|kismen_dogru|yanlis|dogrulanamaz|mesnetsiz|gorus] (mesnetsiz=kaynak hiç delil/dayanak "
            "göstermemiş; dayanak var ama teyit edilemiyorsa dogrulanamaz; tereddütte dogrulanamaz), gerekce [2-3 cümle: neden bu sınıf + hangi delil "
            "gerekir], dayanak_kaynak_url); isim_verilen_suclama (evet/hayir), isim_verilen_suclama_gerekce. "
            "Belirli kişi/kurum adı + ağır suçlama varsa evet; kararsızsan evet. "
            "Gerekçeleri kalıp cümlelerle TEKRARLAMA; her biri o iddiaya özgü olsun. Başlıktaki abartı/değer "
            "yargısı ifadelerini tırnak içinde kaynağa atfet. 'Doğrulanamadı' suçlama değil kanıt eksikliği "
            "tespitidir. SADECE geçerli JSON, markdown YOK.")
    body = json.dumps({"model": model, "max_tokens": 2500, "temperature": 0.2, "system": sysp,
        "messages": [{"role": "user", "content": f"BAŞLIK: {item['baslik']}\n\nÖZET: {item['ozet']}"}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    data = json.loads(urllib.request.urlopen(req, timeout=60).read())
    m = re.search(r"\{.*\}", data["content"][0]["text"], re.DOTALL)
    if not m: raise ValueError("JSON yok")
    return json.loads(m.group(0))

def wp_create_draft(item, a, wp_url, user, app):
    valid = {"dogru","kismen_dogru","yanlis","dogrulanamaz","mesnetsiz","gorus"}
    iddialar = [{"iddia_metni": str(x.get("iddia_metni",""))[:2000],
                 "siniflandirma": x.get("siniflandirma") if x.get("siniflandirma") in valid else "dogrulanamaz",
                 "gerekce": str(x.get("gerekce","")), "dayanak_kaynak_url": x.get("dayanak_kaynak_url","") or ""}
                for x in a.get("iddialar", [])]
    isim = "hayir" if a.get("isim_verilen_suclama") == "hayir" else "evet"
    payload = {"title": item["baslik"][:120] or "Başlıksız", "status": "draft",
        "content": "Otomatik üretilmiş TASLAK (aylık backfill) — editör/hukuk incelemesi bekliyor.",
        "meta": {"haberler_ozet": a.get("ozet",""), "haberler_genel_degerlendirme": a.get("genel_degerlendirme",""), "haberler_isim_verilen_suclama": isim,
            "haberler_isim_suclama_gerekce": a.get("isim_verilen_suclama_gerekce",""),
            "haberler_kaynaklar": json.dumps([{"kaynak_adi": item["kaynak_adi"],
                "orijinal_url": item["orijinal_url"], "yayin_tarihi": item["yayin_tarihi"]}], ensure_ascii=False),
            "haberler_iddialar": json.dumps(iddialar, ensure_ascii=False)}}
    auth = base64.b64encode(f"{user}:{app}".encode()).decode()
    req = urllib.request.Request(f"{wp_url}/wp-json/wp/v2/posts", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def main():
    wp_url = os.environ.get("WP_URL", "http://localhost:8091")
    user   = os.environ.get("WP_USER", "pipeline-bot")
    app    = os.environ.get("WP_APP_PASS"); api = os.environ.get("ANTHROPIC_API_KEY")
    model  = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    ay     = os.environ.get("AY", "Jun"); yil = os.environ.get("YIL", "2026")
    limit  = int(os.environ.get("LIMIT", "10"))
    if not app or not api: print("HATA: WP_APP_PASS ve ANTHROPIC_API_KEY gerekli."); sys.exit(1)

    print(f"Google News arama: {ANAHTAR_SORGU}")
    items = google_news_search(ANAHTAR_SORGU)
    print(f"  toplam sonuç: {len(items)}")

    # Ay filtresi (pubDate ör: 'Mon, 09 Jun 2026 ...')
    etiket = f"{ay} {yil}"
    ayinkiler = [it for it in items if etiket in it["yayin_tarihi"]]
    print(f"  {etiket} içindekiler: {len(ayinkiler)}")

    # Dedup (scheduler/seen-urls.txt ortak state)
    state = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduler", "seen-urls.txt")
    seen = set()
    if os.path.exists(state):
        seen = {l.strip() for l in open(state, encoding="utf-8") if l.strip()}
    yeni, görülen = [], set()
    for it in ayinkiler:
        u = it["orijinal_url"]
        if u and u not in seen and u not in görülen:
            görülen.add(u); yeni.append(it)
    print(f"  yeni (işlenecek): {len(yeni)} | daha önce işlenmiş: {len(ayinkiler)-len(yeni)}")
    if len(yeni) > limit:
        print(f"  NOT: maliyet için ilk {limit} tanesi işlenecek, kalan {len(yeni)-limit} atlanıyor.")

    os.makedirs(os.path.dirname(state), exist_ok=True)
    uretilen = 0
    for it in yeni[:limit]:
        print(f"\n-> {it['kaynak_adi']}: {it['baslik'][:70]}")
        try:
            a = analyze_with_claude(it, api, model); print("   AI analiz: tamam")
        except Exception as e:
            print(f"   AI başarısız ({e}) -> atlanıyor"); continue
        try:
            res = wp_create_draft(it, a, wp_url, user, app)
            print(f"   WP taslak: ID={res.get('id')}")
            with open(state, "a", encoding="utf-8") as fh: fh.write(it["orijinal_url"] + "\n")
            uretilen += 1
        except Exception as e:
            print(f"   WP hata ({e})")
    print(f"\n=== Bitti: {uretilen} taslak üretildi ({etiket}) ===")

if __name__ == "__main__":
    main()
