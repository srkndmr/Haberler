#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HİBRİT pipeline:
  1) Gemini (Google Search grounding) — KANIT toplar: web + AİHM/AYM/Yargıtay kararları (sınıflandırma yapmaz).
  2) Claude — ANALİZ + RAPOR yazar: hukuki statü + masumiyet karinesi + haber_sorunu (yalan/iftira/çarpıtma/toptan suçlama).
  3) WordPress'e TASLAK (otomatik-taslak) yazar.

Kullanım:
  cd n8n && . ./scheduler/.env && python3 hibrit-pipeline.py "BAŞLIK" ["bağlam"]
"""
import os, re, sys, json, time, base64, importlib.util, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
def _load(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(HERE, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
gem = _load("gem", "gemini-analiz.py")
ayl = _load("ayl", "aylik-tarama.py")

GKEY = os.environ.get("GEMINI_API_KEY"); GMODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
CKEY = os.environ.get("ANTHROPIC_API_KEY"); CMODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
WP = os.environ.get("WP_URL", "http://localhost:8091"); USER = os.environ.get("WP_USER", "pipeline-bot"); APP = os.environ.get("WP_APP_PASS")

EVIDENCE_SYS = (
"Sen bir araştırma asistanısın. Verilen haber başlığı/iddiaları hakkında web'de KANIT topla. "
"SINIFLANDIRMA veya HÜKÜM VERME; yalnızca bulgu ve kaynak getir. Özellikle ilgili AİHM kararlarını "
"(örn. Yalçınkaya/Türkiye), AYM ve Yargıtay içtihadını ara; bir isnadın HUKUKİ STATÜSÜNÜ (iddia / "
"soruşturma / iddianame / yerel mahkeme kararı / kesinleşmiş mahkûmiyet / AİHM ihlal kararı) belirlemeye "
"yardımcı kanıt bul. AİHM/AYM içtihadını YALNIZCA haber bir kişiyi/grubu suçlu, örgüt üyesi veya terörist "
"olarak SUNUYORSA ya da kesinleşmemiş bir isnadı kesin suçmuş gibi gösteriyorsa ara (ör. Yalçınkaya 2023, "
"Yasak 2026 ve sonrası lehe kararlar). Haber nötr/olgusalsa (tutuklama, iddianame aktarımı, ölçülü dil) "
"içtihat ARAMA; yalnızca olgu ve kaynak topla. "
"Düz metin döndür: (1) haberin/iddiaların kısa özeti, (2) her iddia için bulunan "
"kanıt ve varsa mahkeme/AİHM/AYM kararı (karar adı + tarihi + ne dediği), (3) hukuki statü ipuçları. "
"Tarafsız ol; karar adı/tarihini uydurma — yalnızca aramada bulduğunu yaz.")

CLAUDE_SYS = (
"Sen kıdemli bir doğruluk denetimi analisti ve insan hakları/medya hukuku editörüsün. Sana bir haber başlığı "
"ve bir ARAŞTIRMA BRİFİ (web + AİHM/AYM/Yargıtay bulguları) verilecek. Bu kanıtı kullanarak AKICI, ölçülü, "
"hukuk-gazetecilik dilinde TARAFSIZ bir TASLAK rapor üret.\n"
"ÜSLUP: Deneyimli bir insan hakları avukatı ve gazeteci gibi DOĞAL, akıcı, ölçülü yaz. Klişe ve şablon "
"kalıplardan, her dosyada aynı cümleleri/atıfları tekrarlamaktan kaçın (özellikle 'AİHM'nin X kararında...' "
"kalıbı yapay durur). İlkeleri kendi cümlelerinle, somut habere bağlayarak anlat.\n"
"İLKELER:\n"
"- Masumiyet karinesi: Bir isnadın 'suç' sayılması KESİNLEŞMİŞ mahkûmiyet gerektirir. Kesinleşme yoksa "
"(iddia/soruşturma/iddianame/yerel karar) kişi 'suçlu/terörist' DEĞİLDİR; medya bunu kesin suçmuş gibi sunuyorsa "
"bu bir ÇARPITMA'dır, gerekçede belirt.\n"
"- HUKUKİ ÇERÇEVE (KOŞULLU): Bu çerçeveyi/yorumu YALNIZCA haber bir kişiyi/grubu suçlu veya örgüt üyesi "
"olarak SUNUYORSA ya da kesinleşmemiş bir isnadı kesin suçmuş gibi gösteriyorsa devreye sok. Haber zaten "
"ölçülüyse ('iddia/şüpheli/iddianame' diyorsa, nötr aktarıyorsa) HUKUK DERSİ VERME; AİHM/ByLock/Bank Asya "
"cümlesi EKLEME — sadece iddiaların hukuki statüsünü (iddia/soruşturma; kesinleşmiş değil) bir-iki cümleyle "
"belirt ve geç. Gerektiğinde ilkeyi deneyimli bir hukukçu gibi KENDİ CÜMLELERİNLE anlat (örgüt üyeliği somut, "
"kişiselleştirilmiş delil ve kast ister; bir listede/uygulamada bulunmak tek başına suç değildir). "
"AİHM/AYM KARAR ADI ANMA — her dosyada tekrar YAPAY durur; ancak o habere doğrudan ve özel emsalse istisnaen "
"bir kez. (Arka plan, gerekmedikçe ANMA: Yalçınkaya, Akgün, Pişkin, Kavala, Demirtaş, Şahin Alpay/Altan, "
"Salduz, Aksoy, Yasak — içeriklerini uydurma.)\n"
"- Olgu/yorum ayır; nötr dil; uydurma yok; tek tarafın beyanıyla 'doğru/yanlış' İLAN ETME.\n"
"- Bir grubu/topluluğu TOPTAN suçlu/dışlayıcı gösteren ifadeler olgu değildir.\n"
"- İHLAL EDİLEN HAKLAR: Haberin veya aktardığı sürecin hangi temel hak ve özgürlükleri ihlal ettiğini/risk "
"altına aldığını belirle ve ihlal_edilen_haklar dizisine ekle. Anahtarlar: ozel_hayat (özel hayatın gizliliği — "
"isim/foto/aile/evlilik gibi mahrem detayların ifşası), din_vicdan (din ve vicdan özgürlüğü), orgutlenme "
"(dernek/vakıf/örgütlenme özgürlüğü), masumiyet (masumiyet karinesi), adil_yargilanma, kanunsuz_ceza, ifade, "
"ayrimcilik. Yalnızca gerçekten zedelenen hakları seç; genel_degerlendirme'de kısaca nasıl zedelendiğini belirt.\n"
"- ÇOKLU KAYNAK: Haber birden çok mecrada yer aldıysa (sana MECRALAR listesi verilecek), "
"genel_degerlendirme'de bunu belirt (kaç mecra ve başlıcaları) ve aynı iddianın çok sayıda mecrada "
"eşzamanlı yayımının kayda değer bir olgu olduğunu not et; ancak bu tek başına suç/iftira kanıtı değildir.\n"
"SINIFLANDIRMA: dogru|yanlis|dogrulanamaz|mesnetsiz|gorus. 'dogru' SADECE iddia sağlam ve doğrulanabilir "
"kanıtla TAM ve şüphesiz doğrulanıyorsa verilir. Bir kısmı doğru bir kısmı kanıtsız/çarpıtılmışsa 'dogru' DEME → "
"dogrulanamaz veya yanlis kullan ve haber_sorunu'na carpitma ekle. 'kısmen doğru' (kismen_dogru) KULLANMA.\n"
"HABER SORUNU (haber_sorunu dizisi): yalan_haber|iftira|toptan_suclama|carpitma — hiçbiri yoksa [\"sorun_yok\"].\n"
"İNGİLİZCE: Uluslararası (AİHM) okuyucu için ayrıca İngilizce çeviri alanları doldur: baslik_en "
"(başlığın İngilizcesi), ozet_en, genel_degerlendirme_en (aynı içeriğin akıcı İngilizcesi).\n"
"SADECE şu şemada geçerli JSON döndür (markdown YOK):\n"
'{"ozet":"3-5 cümle","genel_degerlendirme":"3-5 cümle, hukuki statü + AİHM/AYM dayanağı dahil",'
'"baslik_en":"English title","ozet_en":"English summary","genel_degerlendirme_en":"English assessment",'
'"haber_sorunu":["..."],"ihlal_edilen_haklar":["ozel_hayat","din_vicdan","orgutlenme",...],'
'"iddialar":[{"iddia_metni":"","siniflandirma":"","gerekce":"2-3 cümle: kriter + kanıt","dayanak_kaynak_url":"yalnızca tam http(s) URL; yoksa boş, kaynak adı YAZMA"}],'
'"isim_verilen_suclama":"evet|hayir","isim_verilen_suclama_gerekce":""}')

def resolve(u):
    u = (u or "").split(",")[0].strip()
    if not u or "grounding-api-redirect" not in u: return u
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=12); f = r.geturl(); r.close(); return f or u
    except Exception: return u

def claude_analyze(baslik, metin, brief, key, model, mecralar=None):
    mec = ""
    if mecralar:
        mec = f"\n\nMECRALAR ({len(mecralar)} mecrada yer aldı): {', '.join(mecralar)}"
    body = json.dumps({"model": model, "max_tokens": 3000, "temperature": 0.2, "system": CLAUDE_SYS,
        "messages": [{"role": "user", "content": f"BAŞLIK: {baslik}\n\nHABER BAĞLAMI: {metin}{mec}\n\n=== ARAŞTIRMA BRİFİ (Gemini) ===\n{brief}"}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    data = json.loads(urllib.request.urlopen(req, timeout=90).read())
    t = data["content"][0]["text"]; m = re.search(r"\{.*\}", t, re.DOTALL)
    if not m: raise ValueError("Claude JSON döndürmedi")
    return json.loads(m.group(0))

def wp_create(title, analiz, kaynaklar):
    valid = {"dogru","yanlis","dogrulanamaz","mesnetsiz","gorus"}  # kismen_dogru kullanılmıyor
    sorunlar = {"yalan_haber","iftira","toptan_suclama","carpitma","sorun_yok"}
    iddialar = [{"iddia_metni": str(x.get("iddia_metni",""))[:2000],
                 "siniflandirma": x.get("siniflandirma") if x.get("siniflandirma") in valid else "dogrulanamaz",
                 "gerekce": str(x.get("gerekce","")), "dayanak_kaynak_url": resolve(x.get("dayanak_kaynak_url","") or "")}
                for x in analiz.get("iddialar", [])]
    hs = [s for s in (analiz.get("haber_sorunu") or []) if s in sorunlar] or ["sorun_yok"]
    haklar_ok = {"ozel_hayat","din_vicdan","orgutlenme","masumiyet","adil_yargilanma","kanunsuz_ceza","ifade","ayrimcilik"}
    ih = [h for h in (analiz.get("ihlal_edilen_haklar") or []) if h in haklar_ok]
    isim = "hayir" if analiz.get("isim_verilen_suclama") == "hayir" else "evet"
    payload = {"title": title[:120], "status": "draft",
        "content": "",  # içerik analiz bölümlerinden (the_content filtresi) gelir; placeholder yok
        "meta": {"haberler_ozet": analiz.get("ozet",""), "haberler_genel_degerlendirme": analiz.get("genel_degerlendirme",""),
                 "haberler_baslik_en": analiz.get("baslik_en",""), "haberler_ozet_en": analiz.get("ozet_en",""),
                 "haberler_genel_degerlendirme_en": analiz.get("genel_degerlendirme_en",""),
                 "haberler_haber_sorunu": json.dumps(hs, ensure_ascii=False),
                 "haberler_ihlal_haklar": json.dumps(ih, ensure_ascii=False),
                 "haberler_isim_verilen_suclama": isim, "haberler_isim_suclama_gerekce": analiz.get("isim_verilen_suclama_gerekce",""),
                 "haberler_kaynaklar": json.dumps(kaynaklar, ensure_ascii=False), "haberler_iddialar": json.dumps(iddialar, ensure_ascii=False)}}
    auth = base64.b64encode(f"{USER}:{APP}".encode()).decode()
    req = urllib.request.Request(f"{WP}/wp-json/wp/v2/posts", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# ---- Story clustering: aynı haberi farklı mecralarda yakala ----
def _tok(s):
    return set(w for w in re.sub(r"[^a-z0-9çğıöşü ]", " ", (s or "").lower()).split() if len(w) > 3)
def _jaccard(a, b):
    return len(a & b) / (len(a | b) or 1)
def cluster_items(items, esik=0.5):
    clusters = []
    for it in items:
        t = _tok(it.get("baslik", ""))
        yer = False
        for c in clusters:
            if _jaccard(t, c["tok"]) >= esik:
                c["uyeler"].append(it); c["tok"] |= t; yer = True; break
        if not yer:
            clusters.append({"tok": t, "rep": it, "uyeler": [it]})
    return clusters

def process_one(baslik, metin, kaynaklar=None):
    """Gemini kanıt -> Claude analiz -> WP taslak. kaynaklar=mecra listesi (clustering'den). pid döndürür."""
    print(f"  BAŞLIK: {baslik[:75]}")
    mecralar = sorted({k["kaynak_adi"] for k in (kaynaklar or []) if k.get("kaynak_adi")})
    brief, sources, queries = "", [], []
    for attempt in range(4):
        try:
            brief, sources, queries = gem.gemini_call(EVIDENCE_SYS,
                f"BAŞLIK: {baslik}\nBAĞLAM: {metin}\nKanıt ve ilgili mahkeme/AİHM kararlarını getir.", GKEY, GMODEL)
        except Exception as e:
            print(f"    Gemini hata (kota/ağ?): {e}"); brief = ""
        if brief.strip(): break
        time.sleep(5)
    if not brief.strip():
        print("    ✗ Gemini kanıt yok (atlandı)"); return None
    try:
        analiz = claude_analyze(baslik, metin, brief, CKEY, CMODEL, mecralar)
    except Exception as e:
        print(f"    ✗ Claude hata: {e}"); return None
    if not analiz.get("iddialar"):
        print("    ✗ Somut iddia yok — fact-check konusu değil, atlandı"); return None
    if not kaynaklar:  # clustering yoksa Gemini'nin bulduğu kaynaklar
        kaynaklar = [{"kaynak_adi": t or "kaynak", "orijinal_url": resolve(u), "yayin_tarihi": ""} for t, u in sources[:8]]
    pid = wp_create(baslik, analiz, kaynaklar).get("id")
    print(f"    ✓ taslak ID={pid} | mecra={len(mecralar) or len(kaynaklar)} | sorun={analiz.get('haber_sorunu')} | iddia={len(analiz.get('iddialar', []))}")
    return pid

def main():
    if not (GKEY and CKEY and APP): print("HATA: GEMINI_API_KEY, ANTHROPIC_API_KEY, WP_APP_PASS gerekli."); sys.exit(1)

    # Tek haber modu (argümanla)
    if len(sys.argv) > 1:
        process_one(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
        return

    # GÜNLÜK TOPLU MOD: Google News -> dedup -> ilk N haberi işle (aralıklı)
    limit = int(os.environ.get("HIBRIT_LIMIT", "8"))     # kümeleme sonrası zaten ~4-5 farklı haber kalır
    sleep_s = int(os.environ.get("HIBRIT_SLEEP", "25"))
    state = os.path.join(HERE, "scheduler", "seen-urls.txt")
    seen = set()
    if os.path.exists(state):
        seen = {l.strip() for l in open(state, encoding="utf-8") if l.strip()}
    items = ayl.google_news_search(ayl.ANAHTAR_SORGU)
    # İlgililik süzgeci: başlık/özette FETÖ-çekirdek terim olmalı ("15 Temmuz" tek başına otobüs hattı/okul yakalıyor)
    cekirdek = ("fetö", "feto", "fethullah", "gülen", "gulen", "bylock")
    items = [it for it in items if any(k in ((it.get("baslik", "") + " " + it.get("ozet", "")).lower()) for k in cekirdek)]
    yeni = [it for it in items if it.get("orijinal_url") and it["orijinal_url"] not in seen]
    # Aynı haberi farklı mecralarda topla; çok mecralı kümeler önce (daha yüksek haber değeri)
    kumeler = cluster_items(yeni)
    kumeler.sort(key=lambda c: len(c["uyeler"]), reverse=True)
    print(f"{len(items)} haber | {len(yeni)} yeni | {len(kumeler)} küme | hedef: {limit} dosya (küme arası {sleep_s}s)")
    os.makedirs(os.path.dirname(state), exist_ok=True)
    done = attempts = 0
    for c in kumeler:
        if done >= limit or attempts >= limit * 2: break  # kotayı korumak için deneme tavanı
        attempts += 1
        rep = c["rep"]
        kayn = {}
        for m in c["uyeler"]:
            ad = m.get("kaynak_adi") or "kaynak"
            kayn.setdefault(ad, {"kaynak_adi": ad, "orijinal_url": m.get("orijinal_url", ""), "yayin_tarihi": m.get("yayin_tarihi", "")})
        print(f"\n[küme: {len(kayn)} mecra — {', '.join(list(kayn)[:5])}]")
        pid = process_one(rep["baslik"], rep.get("ozet", ""), list(kayn.values()))
        with open(state, "a", encoding="utf-8") as fh:   # kümedeki tüm URL'ler işaretlenir
            for m in c["uyeler"]:
                if m.get("orijinal_url"): fh.write(m["orijinal_url"] + "\n")
        if pid:
            done += 1
        if done < limit and attempts < limit * 2:
            time.sleep(sleep_s)
    print(f"=== Bitti: {done} dosya üretildi (otomatik-taslak; insan/hukuk onayı bekler) ===")

if __name__ == "__main__":
    main()
