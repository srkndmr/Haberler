#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Claude (depoda kayıtlı) vs Gemini grounded — aynı haberlerde yan yana karşılaştırma.
Girdi: /tmp/items.json  [{id, title, claude:[siniflar]}]
"""
import os, json, time, html, importlib.util

spec = importlib.util.spec_from_file_location("gem", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini-analiz.py"))
gem = importlib.util.module_from_spec(spec); spec.loader.exec_module(gem)

key = os.environ["GEMINI_API_KEY"]; model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
items = json.load(open("/tmp/items.json", encoding="utf-8"))

def ozet_siniflar(sl):
    from collections import Counter
    c = Counter(sl)
    return ", ".join(f"{n}× {s}" for s, n in c.items()) if sl else "(iddia yok)"

print(f"{'='*100}\nAYNI HABERLER: CLAUDE (aramasız)  vs  GEMINI (Google Search grounding)\n{'='*100}")
for idx, it in enumerate(items):
    baslik = html.unescape(it["title"])
    print(f"\n■ [{it['id']}] {baslik[:75]}")
    print(f"   CLAUDE : {ozet_siniflar(it.get('claude', []))}")
    try:
        a, sources, queries = gem.gemini_grounded(baslik, "", key, model)
        gsin = [x.get("siniflandirma", "?") for x in a.get("iddialar", [])]
        doms = ", ".join(sorted({t for t, u in sources})[:4])
        print(f"   GEMINI : {ozet_siniflar(gsin) if gsin else '(JSON ayrıştırılamadı)'}")
        print(f"            kaynaklar: {doms or '(yok)'}")
    except Exception as e:
        print(f"   GEMINI : HATA ({e})")
    if idx < len(items) - 1:
        time.sleep(20)  # ücretsiz katman RPM limitini aşmamak için
