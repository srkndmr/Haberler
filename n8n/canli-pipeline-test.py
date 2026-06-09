#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canlı pipeline kanıtı (n8n akışının komut satırı eşdeğeri).
Akış: RSS çek -> anahtar kelime filtresi -> dedup -> [AI analiz (opsiyonel)] -> WP taslak.

Kullanım:
  WP_URL=http://localhost:8091 WP_USER=pipeline-bot WP_APP_PASS=xxxx \
  [ANTHROPIC_API_KEY=sk-ant-...] python3 canli-pipeline-test.py

ANTHROPIC_API_KEY verilirse her dosya Claude ile analiz edilir; verilmezse
iddialar boş bırakılıp "doğrulanamaz" güvenli varsayılanla taslak üretilir.
WP'ye HER ZAMAN status=draft gönderilir (sunucu hook'u otomatik-taslak'a çeker).
"""
import os, re, sys, json, base64, urllib.request, xml.etree.ElementTree as ET

FEEDS = [
    {"ad": "Cumhuriyet", "rss": "https://www.cumhuriyet.com.tr/rss"},
    {"ad": "Habertürk",  "rss": "https://www.haberturk.com/rss"},
]
ANAHTAR = ["fetö", "feto", "fethullahçı", "fetullahçı", "gülen", "gulen",
           "bylock", "15 temmuz", "darbe girişimi", "paralel yapı", "fetö/pdy"]

UA = {"User-Agent": "Mozilla/5.0 (HaberlerPipeline/1.0)"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse_rss(xml_bytes, kaynak):
    out = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return out
    for item in root.iter("item"):
        def t(tag):
            el = item.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""
        out.append({
            "kaynak_adi": kaynak,
            "baslik": t("title"),
            "orijinal_url": t("link"),
            "ozet": re.sub("<[^>]+>", "", t("description")),
            "yayin_tarihi": t("pubDate"),
        })
    return out

def keyword_filter(items):
    res = []
    for it in items:
        blob = f"{it['baslik']} {it['ozet']}".lower()
        if any(k in blob for k in ANAHTAR):
            res.append(it)
    return res

def analyze_with_claude(item, api_key):
    sys_prompt = (
        "Sen kıdemli bir doğruluk denetimi (fact-checking) analistisin; medya hukuku editörü gibi "
        "düşünürsün ama hâkim değilsin. Türkçe haber metnini inceleyip insan editör ve hukuk "
        "danışmanının önüne gelecek AKICI ve OKUNABİLİR bir taslak hazırlarsın. Mekanik, tek cümlelik, "
        "robotik ifadelerden kaçın; gerekçeli, bağlamı açıklayan, ölçülü bir hukuk-gazetecilik dili kullan. "
        "İlkeler: sonuç önceden belli değildir, atıfta bulunulabilir kanıt yoksa dogrulanamaz de; olgu ile "
        "yorumu ayır (yorum -> gorus); masumiyet karinesi: suç/örgüt üyeliği isnatları kaynağa atfedilen "
        "iddialardır, olgu gibi ileri sürme; nötr dil, uydurma kaynak yok. "
        "ÜRETECEĞİN ALANLAR: ozet (3-5 cümle, bağlamı kuran akıcı paragraf); genel_degerlendirme (3-5 cümle, "
        "hukuk-gazetecilik dilinde tarafsız değerlendirme: dayanak/delil durumu, olgu-yorum dengesi, eksik "
        "bağlam, masumiyet karinesi; hüküm verme); iddialar (her biri iddia_metni, siniflandirma "
        "[dogru|kismen_dogru|yanlis|dogrulanamaz|gorus], gerekce [2-3 cümle: neden bu sınıf + doğrulanması "
        "için hangi delil gerekir], dayanak_kaynak_url); isim_verilen_suclama (evet|hayir) ve "
        "isim_verilen_suclama_gerekce. SADECE geçerli JSON döndür; markdown/kod bloğu/önsöz YOK."
    )
    body = json.dumps({
        "model": os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        "max_tokens": 2500, "temperature": 0.2,
        "system": sys_prompt,
        "messages": [{"role": "user", "content": f"BAŞLIK: {item['baslik']}\n\nÖZET: {item['ozet']}"}],
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    text = data["content"][0]["text"]
    # Model bazen ```json ... ``` ile sarar; ilk { ile son } arasını al.
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("yanıtta JSON bulunamadı")
    return json.loads(m.group(0))

def safe_default(item):
    return {"ozet": item["ozet"][:400], "genel_degerlendirme": "", "iddialar": [],
            "isim_verilen_suclama": "evet",  # AI yoksa güvenli taraf: hukuk kapısı açık
            "isim_verilen_suclama_gerekce": "AI analizi yapılmadı; manuel inceleme gerekir."}

def wp_create_draft(item, analiz, wp_url, user, app_pass):
    valid = {"dogru","kismen_dogru","yanlis","dogrulanamaz","gorus"}
    iddialar = [{
        "iddia_metni": str(x.get("iddia_metni",""))[:2000],
        "siniflandirma": x.get("siniflandirma") if x.get("siniflandirma") in valid else "dogrulanamaz",
        "gerekce": str(x.get("gerekce","")),
        "dayanak_kaynak_url": x.get("dayanak_kaynak_url","") or "",
    } for x in analiz.get("iddialar", [])]
    isim = "hayir" if analiz.get("isim_verilen_suclama") == "hayir" else "evet"
    payload = {
        "title": item["baslik"][:120] or "Başlıksız dosya",
        "status": "draft",  # ASLA publish
        "content": "Otomatik üretilmiş TASLAK — editör/hukuk incelemesi bekliyor.",
        "meta": {
            "haberler_ozet": analiz.get("ozet",""),
            "haberler_genel_degerlendirme": analiz.get("genel_degerlendirme",""),
            "haberler_isim_verilen_suclama": isim,
            "haberler_isim_suclama_gerekce": analiz.get("isim_verilen_suclama_gerekce",""),
            "haberler_kaynaklar": json.dumps([{
                "kaynak_adi": item["kaynak_adi"], "orijinal_url": item["orijinal_url"],
                "yayin_tarihi": item["yayin_tarihi"]}], ensure_ascii=False),
            "haberler_iddialar": json.dumps(iddialar, ensure_ascii=False),
        },
    }
    auth = base64.b64encode(f"{user}:{app_pass}".encode()).decode()
    req = urllib.request.Request(f"{wp_url}/wp-json/wp/v2/posts", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def main():
    wp_url = os.environ.get("WP_URL", "http://localhost:8091")
    user   = os.environ.get("WP_USER", "pipeline-bot")
    app    = os.environ.get("WP_APP_PASS")
    api    = os.environ.get("ANTHROPIC_API_KEY")
    if not app:
        print("HATA: WP_APP_PASS gerekli."); sys.exit(1)

    all_items = []
    for f in FEEDS:
        try:
            items = parse_rss(fetch(f["rss"]), f["ad"])
            print(f"  {f['ad']}: {len(items)} haber çekildi")
            all_items += items
        except Exception as e:
            print(f"  {f['ad']}: ATLANDI ({e})")  # bir kaynak düşerse akış durmaz

    print(f"Toplam {len(all_items)} haber. Anahtar kelime filtresi uygulanıyor...")
    matched = keyword_filter(all_items)

    # Kalıcı URL dedup: daha önce işlenen URL'ler state dosyasında tutulur,
    # böylece günlük çalıştırmalar aynı haberi tekrar tekrar TASLAK YAPMAZ.
    state_path = os.environ.get("STATE_FILE",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduler", "seen-urls.txt"))
    processed = set()
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as fh:
            processed = {ln.strip() for ln in fh if ln.strip()}

    seen, uniq = set(), []
    for it in matched:
        u = it["orijinal_url"]
        if u and u not in seen and u not in processed:
            seen.add(u); uniq.append(it)
    skipped = len(matched) - len(uniq)
    print(f"Konuyla eşleşen: {len(matched)} | yeni (işlenecek): {len(uniq)} | "
          f"daha önce işlenmiş (atlandı): {skipped}")

    if not uniq:
        print("Bugünkü feed'lerde konuyla eşleşen haber yok. (Filtre doğru çalışıyor — uydurma yok.)")
        return

    limit = int(os.environ.get("LIMIT", "2"))
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    for it in uniq[:limit]:
        print(f"\n-> İşleniyor: {it['baslik'][:70]}")
        if api:
            try:
                analiz = analyze_with_claude(it, api); print("   AI analiz: tamam")
            except Exception as e:
                analiz = safe_default(it); print(f"   AI analiz başarısız ({e}) -> güvenli varsayılan")
        else:
            analiz = safe_default(it); print("   AI anahtarı yok -> güvenli varsayılan (iddialar boş, hukuk kapısı açık)")
        res = wp_create_draft(it, analiz, wp_url, user, app)
        print(f"   WP taslak oluşturuldu: ID={res.get('id')} status={res.get('status')}")
        # Başarılı taslak sonrası URL'yi kalıcı olarak işaretle (mükerrer önleme)
        with open(state_path, "a", encoding="utf-8") as fh:
            fh.write(it["orijinal_url"] + "\n")

if __name__ == "__main__":
    main()
