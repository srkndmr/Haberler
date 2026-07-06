#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""İki taslağı (ör. RAG'lı vs RAG'sız) WordPress'ten çekip yan yana özetler.
Kullanım:  . scheduler/.env && python3 karsilastir_taslak.py 336 340
"""
import os, sys, json, base64, urllib.request

WP = os.environ.get("WP_URL", "http://localhost:8091")
USER = os.environ.get("WP_USER", "pipeline-bot")
APP = os.environ.get("WP_APP_PASS")


def getpost(pid):
    auth = base64.b64encode(f"{USER}:{APP}".encode()).decode()
    req = urllib.request.Request(f"{WP}/wp-json/wp/v2/posts/{pid}?context=edit",
                                 headers={"Authorization": f"Basic {auth}"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def ozetle(pid):
    p = getpost(pid)
    m = p.get("meta", {}) or {}
    t = p.get("title", {})
    baslik = t.get("raw") or t.get("rendered") or ""
    iddialar = json.loads(m.get("haberler_iddialar", "[]") or "[]")
    print(f"\n{'='*70}\n===== TASLAK {pid} — {baslik}\n{'='*70}")
    print("Medya kategori :", m.get("haberler_medya_kategori"))
    print("Haber sorunu   :", m.get("haberler_haber_sorunu"))
    print("Halk tabiri    :", m.get("haberler_halk_tabiri"))
    print("İhlal haklar   :", m.get("haberler_ihlal_haklar"))
    print("Kanun maddeleri:", m.get("haberler_kanun_maddeleri"))
    gd = m.get("haberler_genel_degerlendirme", "") or ""
    print(f"\n-- Genel değerlendirme ({len(gd)} karakter) --\n{gd}")
    print(f"\n-- İddialar ({len(iddialar)}) --")
    for i, x in enumerate(iddialar, 1):
        url = x.get("dayanak_kaynak_url", "")
        print(f"  {i}. [{x.get('siniflandirma')}] {x.get('iddia_metni','')[:110]}"
              + (f"  → {url}" if url else ""))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Kullanım: python3 karsilastir_taslak.py <ID1> <ID2> ...")
    for pid in sys.argv[1:]:
        try:
            ozetle(pid)
        except Exception as e:
            print(f"\n✗ Taslak {pid} okunamadı: {e}")
