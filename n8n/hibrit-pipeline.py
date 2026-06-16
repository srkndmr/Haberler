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
"yardımcı kanıt bul. Düz metin döndür: (1) haberin/iddiaların kısa özeti, (2) her iddia için bulunan kanıt "
"ve varsa mahkeme/AİHM kararı (karar adı + ne dediği), (3) hukuki statü ipuçları. Tarafsız ol; uydurma yok.")

CLAUDE_SYS = (
"Sen kıdemli bir doğruluk denetimi analisti ve insan hakları/medya hukuku editörüsün. Sana bir haber başlığı "
"ve bir ARAŞTIRMA BRİFİ (web + AİHM/AYM/Yargıtay bulguları) verilecek. Bu kanıtı kullanarak AKICI, ölçülü, "
"hukuk-gazetecilik dilinde TARAFSIZ bir TASLAK rapor üret.\n"
"İLKELER:\n"
"- Masumiyet karinesi: Bir isnadın 'suç' sayılması KESİNLEŞMİŞ mahkûmiyet gerektirir. Kesinleşme yoksa "
"(iddia/soruşturma/iddianame/yerel karar) kişi 'suçlu/terörist' DEĞİLDİR; medya bunu kesin suçmuş gibi sunuyorsa "
"bu bir ÇARPITMA'dır, gerekçede belirt.\n"
"- AİHM/AYM kararları üstün kanıttır: Brifte böyle bir karar varsa (ör. tek başına ByLock/üyelik çıkarımının "
"suç için yeterli sayılmaması) dayanak göster.\n"
"- Olgu/yorum ayır; nötr dil; uydurma yok; tek tarafın beyanıyla 'doğru/yanlış' İLAN ETME.\n"
"- Bir grubu/topluluğu TOPTAN suçlu/dışlayıcı gösteren ifadeler olgu değildir.\n"
"SINIFLANDIRMA: dogru|kismen_dogru|yanlis|dogrulanamaz|mesnetsiz|gorus.\n"
"HABER SORUNU (haber_sorunu dizisi): yalan_haber|iftira|toptan_suclama|carpitma — hiçbiri yoksa [\"sorun_yok\"].\n"
"SADECE şu şemada geçerli JSON döndür (markdown YOK):\n"
'{"ozet":"3-5 cümle","genel_degerlendirme":"3-5 cümle, hukuki statü + AİHM/AYM dayanağı dahil",'
'"haber_sorunu":["..."],"iddialar":[{"iddia_metni":"","siniflandirma":"","gerekce":"2-3 cümle: hukuki statü + kanıt","dayanak_kaynak_url":""}],'
'"isim_verilen_suclama":"evet|hayir","isim_verilen_suclama_gerekce":""}')

def resolve(u):
    u = (u or "").split(",")[0].strip()
    if not u or "grounding-api-redirect" not in u: return u
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=12); f = r.geturl(); r.close(); return f or u
    except Exception: return u

def claude_analyze(baslik, metin, brief, key, model):
    body = json.dumps({"model": model, "max_tokens": 3000, "temperature": 0.2, "system": CLAUDE_SYS,
        "messages": [{"role": "user", "content": f"BAŞLIK: {baslik}\n\nHABER BAĞLAMI: {metin}\n\n=== ARAŞTIRMA BRİFİ (Gemini) ===\n{brief}"}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    data = json.loads(urllib.request.urlopen(req, timeout=90).read())
    t = data["content"][0]["text"]; m = re.search(r"\{.*\}", t, re.DOTALL)
    if not m: raise ValueError("Claude JSON döndürmedi")
    return json.loads(m.group(0))

def wp_create(title, analiz, kaynaklar):
    valid = {"dogru","kismen_dogru","yanlis","dogrulanamaz","mesnetsiz","gorus"}
    sorunlar = {"yalan_haber","iftira","toptan_suclama","carpitma","sorun_yok"}
    iddialar = [{"iddia_metni": str(x.get("iddia_metni",""))[:2000],
                 "siniflandirma": x.get("siniflandirma") if x.get("siniflandirma") in valid else "dogrulanamaz",
                 "gerekce": str(x.get("gerekce","")), "dayanak_kaynak_url": resolve(x.get("dayanak_kaynak_url","") or "")}
                for x in analiz.get("iddialar", [])]
    hs = [s for s in (analiz.get("haber_sorunu") or []) if s in sorunlar] or ["sorun_yok"]
    isim = "hayir" if analiz.get("isim_verilen_suclama") == "hayir" else "evet"
    payload = {"title": title[:120], "status": "draft",
        "content": "Hibrit (Gemini kanıt + Claude analiz) TASLAK — editör/hukuk incelemesi bekliyor.",
        "meta": {"haberler_ozet": analiz.get("ozet",""), "haberler_genel_degerlendirme": analiz.get("genel_degerlendirme",""),
                 "haberler_haber_sorunu": json.dumps(hs, ensure_ascii=False),
                 "haberler_isim_verilen_suclama": isim, "haberler_isim_suclama_gerekce": analiz.get("isim_verilen_suclama_gerekce",""),
                 "haberler_kaynaklar": json.dumps(kaynaklar, ensure_ascii=False), "haberler_iddialar": json.dumps(iddialar, ensure_ascii=False)}}
    auth = base64.b64encode(f"{USER}:{APP}".encode()).decode()
    req = urllib.request.Request(f"{WP}/wp-json/wp/v2/posts", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def main():
    if not (GKEY and CKEY and APP): print("HATA: GEMINI_API_KEY, ANTHROPIC_API_KEY, WP_APP_PASS gerekli."); sys.exit(1)
    if len(sys.argv) > 1:
        baslik = sys.argv[1]; metin = sys.argv[2] if len(sys.argv) > 2 else ""
    else:
        items = ayl.google_news_search(ayl.ANAHTAR_SORGU)
        if not items: print("haber yok"); sys.exit(1)
        baslik = items[0]["baslik"]; metin = items[0].get("ozet", "")

    print(f"BAŞLIK: {baslik}\n1) Gemini kanıt topluyor (web + AİHM/AYM/Yargıtay)...")
    brief, sources, queries = "", [], []
    for attempt in range(4):
        brief, sources, queries = gem.gemini_call(EVIDENCE_SYS,
            f"BAŞLIK: {baslik}\nBAĞLAM: {metin}\nKanıt ve ilgili mahkeme/AİHM kararlarını getir.", GKEY, GMODEL)
        if brief.strip(): break
        print(f"   (boş, tekrar {attempt + 1}/4)"); time.sleep(5)
    if not brief.strip(): print("✗ Gemini kanıt getirmedi; sonra tekrar denenebilir."); sys.exit(2)
    print(f"   arama: {' | '.join(queries)}  | kaynak: {len(sources)}")

    print("2) Claude analiz + rapor yazıyor...")
    analiz = claude_analyze(baslik, metin, brief, CKEY, CMODEL)
    kaynaklar = [{"kaynak_adi": t or "kaynak", "orijinal_url": resolve(u), "yayin_tarihi": ""} for t, u in sources[:8]]
    print(f"   haber_sorunu: {analiz.get('haber_sorunu')} | iddia: {len(analiz.get('iddialar', []))}")

    res = wp_create(baslik, analiz, kaynaklar)
    pid = res.get("id")
    print(f"\n✓ WordPress taslağı: ID={pid}  →  {WP}/wp-admin/post.php?post={pid}&action=edit")

if __name__ == "__main__":
    main()
