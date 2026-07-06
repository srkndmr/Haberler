#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini (Google Search grounding) ile kanıt-temelli haber analizi.
Claude'dan farkı: canlı web araması yapıp iddiaları gerçek kaynaklarla test eder.

Kullanım:
  cd n8n && . ./scheduler/.env && python3 gemini-analiz.py "BAŞLIK" "isteğe bağlı bağlam"
Argüman verilmezse örnek bir başlıkla çalışır.
"""
import os, re, sys, json, time, html, urllib.request, urllib.error

SISTEM = (
"Sen kıdemli bir doğruluk denetimi (fact-checking) analistisin; medya hukuku editörü gibi düşünürsün "
"ama hâkim değilsin. GOOGLE ARAMA aracın var: iddiaları doğrulamak için web'de araştır, güvenilir "
"kaynaklara (resmi kurum, mahkeme/savcılık, saygın haber) dayan. Türkçe, akıcı, ölçülü bir hukuk-"
"gazetecilik dili kullan; mekanik olma. İlkeler: olgu/yorum ayır (yorum -> gorus); masumiyet karinesi "
"(suç/örgüt üyeliği isnatları kaynağa atfedilen iddialardır, olgu gibi ileri sürme); nötr dil; uydurma yok.\n"
"SINIFLANDIRMA: dogru | kismen_dogru | yanlis | dogrulanamaz | mesnetsiz | gorus. "
"mesnetsiz=kaynak hiç delil göstermemiş; dayanak var ama teyit edemiyorsan dogrulanamaz; tereddütte dogrulanamaz. "
"TARAFSIZLIK: Tek bir tarafın (özellikle suçlanan kişinin) beyanına dayanarak bir iddiayı 'dogru' ya da "
"'yanlis' İLAN ETME; inkâr da bir iddiadır. 'dogru/yanlis' için bağımsız belge, resmi/mahkeme kararı veya "
"doğrulanabilir kanıt gerekir; yoksa dogrulanamaz. Aramayla net bağımsız kanıt bulursan dogru/yanlis kullan ve dayanak_kaynak_url ver.\n"
"SADECE şu şemada geçerli JSON döndür (markdown/kod bloğu YOK): "
'{"ozet":"3-5 cümle bağlamlı özet","genel_degerlendirme":"3-5 cümle tarafsız değerlendirme",'
'"iddialar":[{"iddia_metni":"","siniflandirma":"","gerekce":"2-3 cümle, arama bulgusuna dayalı","dayanak_kaynak_url":""}],'
'"isim_verilen_suclama":"evet|hayir","isim_verilen_suclama_gerekce":""}'
)

def gemini_call(system, user, key, model):
    """Düşük seviye Gemini grounded çağrısı → (metin, kaynaklar, sorgular). Retry'li."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = json.dumps({
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 3500},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    data = None
    for attempt in range(4):
        try:
            data = json.loads(urllib.request.urlopen(req, timeout=120).read()); break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 3:
                time.sleep((20 if e.code == 429 else 5) * (attempt + 1)); continue
            raise
    if data is None:
        raise RuntimeError("Gemini yanıt vermedi")
    cand = (data.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    gm = cand.get("groundingMetadata", {})
    sources = [(ch.get("web", {}).get("title", ""), ch["web"]["uri"])
               for ch in gm.get("groundingChunks", []) if ch.get("web", {}).get("uri")]
    return text, sources, gm.get("webSearchQueries", [])

def gemini_grounded(baslik, metin, key, model):
    user = f"BAŞLIK: {html.unescape(baslik or '')}\n\nBAĞLAM: {html.unescape(metin or '')}\n\nİddiaları web'de araştırıp şemaya göre değerlendir."
    text, sources, queries = gemini_call(SISTEM, user, key, model)
    analiz = {"_ham": text}
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            analiz = json.loads(m.group(0))
        except Exception:
            analiz = {"_ham": text}
    return analiz, sources, queries

def main():
    key = os.environ.get("GEMINI_API_KEY"); model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    if not key: print("HATA: GEMINI_API_KEY gerekli."); sys.exit(1)
    baslik = sys.argv[1] if len(sys.argv) > 1 else "İzmir'de FETÖ soruşturması: 78 gözaltı kararı"
    metin  = sys.argv[2] if len(sys.argv) > 2 else ""
    print(f"BAŞLIK: {baslik}\nModel: {model} (Google Search grounding)\n" + "="*60)
    a, sources, queries = gemini_grounded(baslik, metin, key, model)
    print("\n— ARAMA SORGULARI —"); print("  " + " | ".join(queries) if queries else "  (yok)")
    print("\n— ÖZET —\n" + (a.get("ozet","") or a.get("_ham","")[:500]))
    print("\n— GENEL DEĞERLENDİRME —\n" + a.get("genel_degerlendirme",""))
    print("\n— İDDİALAR —")
    for i, x in enumerate(a.get("iddialar", []), 1):
        print(f"  [{i}] {x.get('siniflandirma','?').upper()}: {x.get('iddia_metni','')}")
        print(f"      gerekçe: {x.get('gerekce','')}")
        if x.get("dayanak_kaynak_url"): print(f"      dayanak: {x['dayanak_kaynak_url']}")
    print(f"\nisim_verilen_suclama: {a.get('isim_verilen_suclama','?')} — {a.get('isim_verilen_suclama_gerekce','')}")
    print("\n— GROUNDING KAYNAKLARI —")
    for t, u in sources[:8]: print(f"  • {t[:50]} {u}")

if __name__ == "__main__":
    main()
