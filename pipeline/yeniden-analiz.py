#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mevcut taslakları ZENGİN promptla yeniden analiz eder (yerinde günceller).
Kullanım:
  cd n8n && . ./scheduler/.env && python3 yeniden-analiz.py 38 40 42 44 46 48 50 52
Argüman verilmezse WP'den tüm 'otomatik-taslak' dosyaları bulmaya çalışır (ID'ler önerilir).
"""
import os, re, sys, json, base64, urllib.request

SISTEM = (
"Sen kıdemli bir doğruluk denetimi (fact-checking) analistisin; medya hukuku editörü gibi "
"düşünürsün ama hâkim değilsin. Türkçe bir haber metnini inceleyip insan editör ve hukuk "
"danışmanının önüne gelecek, AKICI ve OKUNABİLİR bir taslak hazırlarsın. Mekanik, tek cümlelik, "
"robotik ifadelerden kaçın; gerekçeli, bağlamı açıklayan, ölçülü bir hukuk-gazetecilik dili kullan.\n\n"
"İlkeler:\n"
"- Sonuç önceden belli değildir; yalnızca atıfta bulunulabilir kanıt destekliyorsa sınıflandır, "
"aksi halde dogrulanamaz de.\n"
"- Olgu ile yorumu ayır (yorum/değer yargısı -> gorus).\n"
"- Masumiyet karinesi: suç veya örgüt üyeliği isnatları kaynağa atfedilen iddialardır; olgu gibi "
"ileri sürme, kendi sesinle tekrarlama.\n"
"- Nötr, ölçülü dil; siyasi/ahlaki taraf tutma. Uydurma kaynak/veri yok.\n\n"
"Üreteceğin alanlar:\n"
"- ozet: 3-5 cümlelik, bağlamı kuran, haberin neyi iddia ettiğini ve denetimin kapsamını "
"açıklayan akıcı bir paragraf.\n"
"- genel_degerlendirme: 3-5 cümlelik, hukuk-gazetecilik dilinde TARAFSIZ değerlendirme: "
"iddiaların dayanak/delil durumu, olgu-yorum dengesi, varsa eksik bağlam ve masumiyet karinesi "
"açısından dikkat edilmesi gerekenler. Hüküm verme; 'şu doğrulanabilir, şu şu delili gerektirir' "
"biçiminde yaz.\n"
"- iddialar: her somut iddia için iddia_metni; siniflandirma (dogru|kismen_dogru|yanlis|"
"dogrulanamaz|mesnetsiz|gorus); gerekce (2-3 cümle: neden bu sınıfa konduğu VE doğrulanması için hangi "
"delilin gerekeceği); dayanak_kaynak_url (varsa, yoksa boş).\n"
"- isim_verilen_suclama (evet|hayir) ve isim_verilen_suclama_gerekce.\n\n"
"DİL KURALLARI: Gerekçeleri kalıp cümlelerle TEKRARLAMA; her iddianın gerekçesi o iddiaya özgü ve "
"özgün olsun (aynı 'mahkeme kararları, tanık ifadeleri gereklidir' kalıbını her maddede tekrarlama). "
"Başlık veya metindeki abartı/değer yargısı ifadelerini ('planı patladı' gibi) tırnak içinde ve "
"kaynağa atfederek aktar; kendi sesinle benimseme. 'Doğrulanamadı' bir suçlama değil, kanıt eksikliği "
"tespitidir; bunu ima eden ölçülü bir dil kullan.\n"
"SINIFLANDIRMA AYRIMI: 'mesnetsiz' = kaynak, iddiayı HİÇBİR delil/dayanak/atıf göstermeden ileri "
"sürmüşse (kaynağın eksikliğine dair tespit; doğru/yanlış olduğu ayrıca değerlendirilir). Bir dayanak "
"var ama bağımsız teyit edemiyorsan 'dogrulanamaz'. Tereddütte 'dogrulanamaz' (daha az iddialı olan).\n\n"
"ÇIKTI: yalnızca geçerli JSON döndür; markdown, kod bloğu veya önsöz YOK."
)

WP   = os.environ.get("WP_URL", "http://localhost:8091")
USER = os.environ.get("WP_USER", "pipeline-bot")
APP  = os.environ.get("WP_APP_PASS")
API  = os.environ.get("ANTHROPIC_API_KEY")
MODEL= os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
AUTH = base64.b64encode(f"{USER}:{APP}".encode()).decode() if APP else ""

def wp_get(pid):
    req = urllib.request.Request(f"{WP}/wp-json/wp/v2/posts/{pid}?context=edit",
        headers={"Authorization": f"Basic {AUTH}"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def wp_update_meta(pid, meta):
    req = urllib.request.Request(f"{WP}/wp-json/wp/v2/posts/{pid}",
        data=json.dumps({"meta": meta}).encode(),
        headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def claude(baslik, girdi):
    body = json.dumps({"model": MODEL, "max_tokens": 2500, "temperature": 0.2, "system": SISTEM,
        "messages": [{"role": "user", "content": f"BAŞLIK: {baslik}\n\nMEVCUT ÖZET/BAĞLAM:\n{girdi}"}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": API, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    data = json.loads(urllib.request.urlopen(req, timeout=90).read())
    m = re.search(r"\{.*\}", data["content"][0]["text"], re.DOTALL)
    if not m: raise ValueError("JSON yok")
    return json.loads(m.group(0))

def main():
    if not APP or not API:
        print("HATA: WP_APP_PASS ve ANTHROPIC_API_KEY gerekli."); sys.exit(1)
    ids = sys.argv[1:]
    if not ids:
        print("ID verin: python3 yeniden-analiz.py 38 40 ..."); sys.exit(1)
    valid = {"dogru","kismen_dogru","yanlis","dogrulanamaz","mesnetsiz","gorus"}
    for pid in ids:
        try:
            p = wp_get(pid)
            baslik = p.get("title", {}).get("raw") or p.get("title", {}).get("rendered") or ""
            girdi  = p.get("meta", {}).get("haberler_ozet") or baslik
            print(f"\n-> ID {pid}: {baslik[:70]}")
            a = claude(baslik, girdi)
            iddialar = [{"iddia_metni": str(x.get("iddia_metni",""))[:2000],
                         "siniflandirma": x.get("siniflandirma") if x.get("siniflandirma") in valid else "dogrulanamaz",
                         "gerekce": str(x.get("gerekce","")), "dayanak_kaynak_url": x.get("dayanak_kaynak_url","") or ""}
                        for x in a.get("iddialar", [])]
            isim = "hayir" if a.get("isim_verilen_suclama") == "hayir" else "evet"
            wp_update_meta(pid, {
                "haberler_ozet": a.get("ozet",""),
                "haberler_genel_degerlendirme": a.get("genel_degerlendirme",""),
                "haberler_isim_verilen_suclama": isim,
                "haberler_isim_suclama_gerekce": a.get("isim_verilen_suclama_gerekce",""),
                "haberler_iddialar": json.dumps(iddialar, ensure_ascii=False),
            })
            print(f"   güncellendi: {len(iddialar)} iddia, genel_degerlendirme {'VAR' if a.get('genel_degerlendirme') else 'yok'}")
        except Exception as e:
            print(f"   HATA ({e})")

if __name__ == "__main__":
    main()
