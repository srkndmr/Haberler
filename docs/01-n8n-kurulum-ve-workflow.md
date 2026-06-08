# 01 — n8n Kurulumu + Pipeline Workflow

> n8n: self-hosted, görsel otomasyon. WordPress paylaşımlı hostinge **kurulamaz**
> (Docker/Node gerektirir). İki seçenek var; biri yeterli.

## 0. n8n'i ayağa kaldır (iki seçenek)

### Seçenek A — Ayrı bir VPS'te Docker ile (önerilen, tam kontrol)
1. Bir VPS al (Hetzner CX22 ~4€/ay veya DigitalOcean 2GB). Ubuntu 22.04 seç.
2. SSH ile bağlan, Docker kur:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
3. n8n'i kalıcı veriyle başlat (alan adını ve şifreyi değiştir):
   ```bash
   docker volume create n8n_data
   docker run -d --name n8n --restart unless-stopped \
     -p 5678:5678 \
     -e N8N_HOST="n8n.alanadi.org" \
     -e N8N_PROTOCOL="https" \
     -e WEBHOOK_URL="https://n8n.alanadi.org/" \
     -e GENERIC_TIMEZONE="Europe/Istanbul" \
     -e N8N_BASIC_AUTH_ACTIVE=true \
     -e N8N_BASIC_AUTH_USER="yonetici" \
     -e N8N_BASIC_AUTH_PASSWORD="GÜÇLÜ_PAROLA" \
     -v n8n_data:/home/node/.n8n \
     docker.n8n.io/n8nio/n8n
   ```
4. Bir reverse proxy (Caddy/Nginx) ile `https://n8n.alanadi.org` üzerinden SSL aç.
   (Caddy en kolayı: tek satır `n8n.alanadi.org { reverse_proxy localhost:5678 }`.)

### Seçenek B — n8n Cloud (kurulum yok, aylık ücret)
1. https://n8n.io → Cloud planı → e-posta ile hesap aç. Hazır gelir.

> Hangisini seçersen seç, sonraki adımlar (credentials + workflow import) aynıdır.

---

## 1. Credentials (kimlik bilgileri) — UI'da bir kez tanımla

> **Asla** API anahtarlarını node parametrelerine düz yazma. n8n **Credentials**'ta sakla.

### 1.1 — WordPress (pipeline-bot)
- **Credentials → New → "Header Auth"** (Application Password için Basic Auth header):
  - Name: `WP pipeline-bot`
  - **Header Name:** `Authorization`
  - **Header Value:** `Basic <BASE64>` — şu şekilde üret:
    `pipeline-bot:uygulama_parolası` (parola boşlukları dahil) metnini Base64'le.
    Örn. terminalde: `echo -n 'pipeline-bot:abcd EFGH ijkl mnop qrst uvwx' | base64`
  - (Alternatif: n8n'in hazır **"WordPress API"** credential tipini de kullanabilirsin;
    username = `pipeline-bot`, password = Application Password.)

### 1.2 — Anthropic (Claude)
- **Credentials → New → "Anthropic API"**:
  - Name: `Anthropic Claude`
  - API Key: Anthropic konsolundan aldığın anahtar (`sk-ant-...`).

---

## 2. Workflow'u içe aktar

1. n8n → sağ üst **⋯ → Import from File** → `n8n/haberler-pipeline.workflow.json` seç.
2. Açılan node'larda **kırmızı uyarı** olanlara tıkla, yukarıda tanımladığın
   credential'ları (WP + Anthropic) seç.
3. **Set: Kaynak Listesi** node'unu aç, izlenecek kaynakları gözden geçir (aşağıda).

---

## 3. Akış — Node Node Açıklama

> İçe aktarılan iskeletteki node'lar ve görevleri. Akış tek yönlü soldan sağa.

| # | Node (tip) | Görev |
|---|---|---|
| 1 | **Schedule Trigger** | Günlük tetikleyici (örn. her gün 07:00). |
| 2 | **Set — Kaynak Listesi** | İzlenecek kaynakların yapılandırılabilir listesi (JSON). |
| 3 | **Split Out (kaynaklar)** | Her kaynağı tek tek akışa böler. |
| 4a | **RSS Read** | `yöntem: rss` olan kaynaklar için RSS okur. |
| 4b | **HTTP Request + HTML Extract** | `yöntem: scrape` olan kaynaklar için sayfa çeker, başlık/özet/link ayıklar. |
| 5 | **Merge** | RSS + scrape sonuçlarını tek listede birleştirir. |
| 6 | **Code — Anahtar Kelime Filtresi** | Konuyla (FETÖ vb.) ilgisiz haberleri eler. |
| 7 | **Code — URL Tekrar Kontrolü** | Daha önce işlenen URL'leri atlar (WP'de arama ile). |
| 8 | **Code — Story Clustering** | Aynı iddiayı/olayı anlatan farklı mecra haberlerini tek dosyada gruplar. |
| 9 | **HTTP Request — Arşivle** | Her URL için web.archive.org snapshot tetikler. |
| 10 | **Anthropic (Claude) — Analiz** | İddiaları ayıklar, sınıflandırır, KATI JSON döndürür. |
| 11 | **Code — JSON Parse + ACF Payload** | AI çıktısını doğrular, WP REST payload'una çevirir. |
| 12 | **HTTP Request — WP REST (draft)** | `status: draft` olarak gönderir. **Asla publish değil.** |
| 13 | **Error Trigger / Continue On Fail** | Bir kaynak düşerse akış durmaz, hatayı loglar. |

### 3.1 — Node 2: Kaynak Listesi (yapılandırılabilir)

`Set` node'unda `kaynaklar` adlı bir JSON alanı tut. Her kaynak:
`{ ad, ana_url, rss_url (varsa), yontem: "rss" | "scrape" }`.

```json
{
  "kaynaklar": [
    { "ad": "Sözcü",       "ana_url": "https://www.sozcu.com.tr",     "rss_url": "https://www.sozcu.com.tr/feeds-rss-category-sozcu", "yontem": "rss" },
    { "ad": "Hürriyet",    "ana_url": "https://www.hurriyet.com.tr",  "rss_url": "https://www.hurriyet.com.tr/rss/anasayfa",          "yontem": "rss" },
    { "ad": "Milliyet",    "ana_url": "https://www.milliyet.com.tr",  "rss_url": "https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml", "yontem": "rss" },
    { "ad": "Habertürk",   "ana_url": "https://www.haberturk.com",    "rss_url": "https://www.haberturk.com/rss",                     "yontem": "rss" },
    { "ad": "Sabah",       "ana_url": "https://www.sabah.com.tr",     "rss_url": "https://www.sabah.com.tr/rss/anasayfa.xml",         "yontem": "rss" },
    { "ad": "Cumhuriyet",  "ana_url": "https://www.cumhuriyet.com.tr","rss_url": "https://www.cumhuriyet.com.tr/rss",                 "yontem": "rss" },
    { "ad": "Yeni Şafak",  "ana_url": "https://www.yenisafak.com",    "rss_url": "https://www.yenisafak.com/rss?xml=anasayfa",        "yontem": "rss" },
    { "ad": "Star",        "ana_url": "https://www.star.com.tr",      "rss_url": "https://www.star.com.tr/rss/rss.asp",               "yontem": "rss" },
    { "ad": "NTV",         "ana_url": "https://www.ntv.com.tr",       "rss_url": "https://www.ntv.com.tr/gundem.rss",                 "yontem": "rss" },

    { "ad": "Haberler.com","ana_url": "https://www.haberler.com",     "rss_url": "",                                                  "yontem": "scrape" },
    { "ad": "Ensonhaber",  "ana_url": "https://www.ensonhaber.com",   "rss_url": "",                                                  "yontem": "scrape" },
    { "ad": "Mynet",       "ana_url": "https://www.mynet.com",        "rss_url": "",                                                  "yontem": "scrape" }
  ]
}
```

> RSS URL'leri zamanla değişebilir; çalışmayanı `yontem: "scrape"`a çevir.
> Portal/agregatörler (Haberler.com, Ensonhaber, Mynet) genelde orijinal kaynağa yönlendirir —
> mümkünse `orijinal_url` olarak yönlendirdiği asıl mecranın linkini kaydet.

### 3.2 — Node 6: Anahtar kelime filtresi (FETÖ konusu)

Bir `Code` node'unda, başlık+özet metnini küçük harfe çevirip anahtar kelime ara.
Konu listesi **yapılandırılabilir** olsun (kelime listesini dosyanın başında tut):

```js
// Konuyla ilgili anahtar kelimeler (genişletilebilir)
const ANAHTAR = [
  "fetö", "feto", "fethullahçı", "fetullahçı", "gülen", "gulen",
  "bylock", "15 temmuz", "darbe girişimi", "paralel yapı", "fetö/pdy"
];
const HARIC = []; // istenmeyen bağlamları elemek için (opsiyonel)

return items.filter(({ json }) => {
  const metin = `${json.baslik || ""} ${json.ozet || ""} ${json.icerik || ""}`.toLowerCase();
  const eslesme = ANAHTAR.some(k => metin.includes(k));
  const haricEslesme = HARIC.some(k => metin.includes(k));
  return eslesme && !haricEslesme;
});
```

### 3.3 — Node 7: URL bazında tam tekrar kontrolü

Aynı URL daha önce işlendiyse atla. Her gelen URL için WP'de arama yap
(`GET /wp-json/wp/v2/posts?search=<url>&status=any` veya ACF meta sorgusu),
sonuç varsa item'ı düşür. Basit yaklaşım: bir `Code` node'unda n8n statik veri
(`$getWorkflowStaticData('global')`) içinde işlenen URL'lerin bir kümesini tut:

```js
const store = $getWorkflowStaticData('global');
store.gorulenUrller = store.gorulenUrller || {};
const yeni = [];
for (const item of items) {
  const u = (item.json.orijinal_url || "").trim();
  if (!u) continue;
  if (store.gorulenUrller[u]) continue;   // daha önce işlendi → atla
  store.gorulenUrller[u] = Date.now();
  yeni.push(item);
}
return yeni;
```
> Kalıcı/güvenilir tekrar kontrolü için WP'ye `orijinal_url` ACF sorgusu daha sağlamdır;
> statik veri hızlı başlangıç içindir.

### 3.4 — Node 8: Story clustering (çoklu mecra → tek dosya)

Farklı mecralarda çıkan **aynı** iddiayı/olayı tek dosyada grupla. Başlık + ilk
paragraf benzerliğine bak. Hafif bir yaklaşım (harici embedding gerekmez):
başlıkları normalize edip Jaccard/token benzerliği ile eşle. Daha isabetli istersen
Anthropic embeddings yerine basit kosinüs-TF benzerliği yeterli.

```js
// Basit benzerlik tabanlı kümeleme
function tokens(s){return (s||"").toLowerCase().replace(/[^a-z0-9çğıöşü ]/g," ").split(/\s+/).filter(w=>w.length>3);}
function jaccard(a,b){const A=new Set(a),B=new Set(b);const k=[...A].filter(x=>B.has(x)).length;return k/((A.size+B.size-k)||1);}

const ESIK = 0.45; // 0.45+ aynı haber sayılır (ayarla)
const kumeler = [];
for (const it of items) {
  const t = tokens(`${it.json.baslik} ${it.json.ilk_paragraf || it.json.ozet}`);
  let yerlesti = false;
  for (const k of kumeler) {
    if (jaccard(t, k.tokens) >= ESIK) {
      k.kaynaklar.push({ kaynak_adi: it.json.kaynak_adi, orijinal_url: it.json.orijinal_url, yayin_tarihi: it.json.yayin_tarihi });
      yerlesti = true; break;
    }
  }
  if (!yerlesti) kumeler.push({ tokens: t, baslik: it.json.baslik, metin: it.json.icerik, kaynaklar: [
    { kaynak_adi: it.json.kaynak_adi, orijinal_url: it.json.orijinal_url, yayin_tarihi: it.json.yayin_tarihi }
  ]});
}
// Her küme = bir dosya. Tekrarları SİLMİYORUZ; kaynak listesine ekliyoruz.
return kumeler.map(k => ({ json: { baslik: k.baslik, icerik: k.metin, kaynaklar: k.kaynaklar } }));
```

> **Neden silmiyoruz:** Bir iddianın çok sayıda mecrada eşzamanlı çıkması, sistematik/koordineli
> yayını gösteren bir **kanıttır**. Bu yüzden tekrarları atmak yerine tek dosyada toplayıp
> `kaynaklar` repeater'ında yan yana sergiliyoruz.

### 3.5 — Node 9: Arşivleme

Her `orijinal_url` için web.archive.org snapshot tetikle:
- **HTTP Request:** `GET https://web.archive.org/save/{{ $json.orijinal_url }}`
- Dönen `Content-Location` / `Location` başlığından snapshot yolunu al,
  `https://web.archive.org` ile birleştirip `arsiv_url` olarak sakla.
- Ekran görüntüsü için (opsiyonel) bir screenshot servisi (örn. `https://image.thum.io/get/{{url}}`)
  ya da kendi headless tarayıcı node'un. Sonucu `ekran_goruntusu` olarak taşı.
- Bu node'da **Continue On Fail = ON** (arşiv başarısız olsa da akış devam etsin; alanı boş bırak).

### 3.6 — Node 10: Anthropic (Claude) analiz

- **Anthropic node** (veya HTTP Request → `https://api.anthropic.com/v1/messages`).
- Model: `claude-3-5-haiku-latest` (ucuz, hızlı) ya da daha titiz analiz için
  `claude-sonnet-4-5` / güncel Sonnet.
- **System prompt:** `prompts/ai-analiz-sistem-promptu.md` içeriğini yapıştır.
- **User mesajı:** kümelenmiş haberin başlığı + tam metni + kaynak listesi.
- **Çıktı:** katı JSON (markdown/önsöz yok). `temperature: 0`, `max_tokens: 2000`.

### 3.7 — Node 11: JSON parse + ACF payload

AI çıktısını **doğrula** (JSON.parse + şema kontrolü) ve WP REST payload'una çevir.
`isim_verilen_suclama` AI tarafından `"evet"/"hayir"` olarak set edilir; geçersizse `"evet"` (güvenli taraf).

```js
const out = [];
for (const it of items) {
  let analiz;
  try { analiz = JSON.parse(it.json.ai_text); }
  catch (e) { analiz = null; }

  // Güvenli varsayılanlar
  const gecerliSinif = new Set(["dogru","kismen_dogru","yanlis","dogrulanamaz","gorus"]);
  const iddialar = (analiz?.iddialar || []).map(x => ({
    iddia_metni: String(x.iddia_metni || "").slice(0, 2000),
    siniflandirma: gecerliSinif.has(x.siniflandirma) ? x.siniflandirma : "dogrulanamaz",
    gerekce: String(x.gerekce || ""),
    dayanak_kaynak_url: x.dayanak_kaynak_url || ""
  }));
  const isimSuclama = analiz?.isim_verilen_suclama === "evet" ? "evet"
                    : analiz?.isim_verilen_suclama === "hayir" ? "hayir"
                    : "evet"; // emin değilsek hukuk kapısını AÇ

  // ÜCRETSİZ meta yolu (wp/mu-plugins/haberler-veri.php). kaynaklar/iddialar JSON string.
  out.push({ json: {
    title: it.json.baslik || "Başlıksız dosya",
    status: "draft",                       // SABİT — asla publish
    meta: {
      haberler_ozet: analiz?.ozet || "",
      haberler_isim_verilen_suclama: isimSuclama,
      haberler_isim_suclama_gerekce: analiz?.isim_verilen_suclama_gerekce || "",
      haberler_kaynaklar: JSON.stringify(it.json.kaynaklar || []),
      haberler_iddialar: JSON.stringify(iddialar)
    }
  }});
  // (ACF PRO kullanıyorsanız meta yerine acf:{ozet, isim_verilen_suclama, kaynaklar:[...], iddialar:[...]} gönderin.)
}
return out;
```

### 3.8 — Node 12: WP REST gönderimi (draft)

- **HTTP Request:**
  - Method: `POST`
  - URL: `https://ALANADI/wp-json/wp/v2/posts`
  - Authentication: **WP pipeline-bot** credential (Header Auth)
  - Body (JSON): Node 11 çıktısı — `title`, `status: "draft"`, `acf: {...}`.
- Yazı oluştuktan sonra PublishPress özel durumunu (`otomatik-taslak`) set etmek için
  ikinci bir küçük istek ya da WP tarafında bir hook kullan. (Detay: `04-rest-api-payload.md`.)
- ⚠️ **`status` ALANI HER ZAMAN `draft`.** Workflow içinde `publish` kelimesi hiç geçmemeli.

### 3.9 — Hata yönetimi

- Tek tek kaynaklarda **Continue On Fail = ON**: bir RSS/scrape düşerse o item atlanır, akış sürer.
- Workflow'a bir **Error Trigger** workflow'u bağla: hata olursa yöneticiye e-posta/Slack at.
- Anthropic 429/5xx için node'da **Retry On Fail** (3 deneme, artan bekleme) aç.

---

## 4. `isim_verilen_suclama` nasıl set edilir? (özet)

AI, bir metinde **belirli bir kişi/kurum ismi + suçlayıcı ağır niteleme** (örn. "X kişisi
örgüt üyesidir", "Y yalan haber yaptı", "Z iftira attı") birlikte geçiyorsa `"evet"` döndürür.
Sadece genel/anonim ifade varsa `"hayir"`. **Emin değilse `"evet"`** (Node 11 bunu zorlar) —
böylece şüpheli her dosya hukuk kapısına yönlenir, masumiyet karinesi korunur.

## 5. Güvenlik notları

- API kimlik bilgileri **yalnızca** n8n Credentials'ta. Node parametrelerinde, kodda veya
  bu repoda anahtar **yok**.
- `pipeline-bot` Contributor; teknik olarak yayınlayamaz. Yayın tek elde (Yönetici).
- n8n paneline Basic Auth + HTTPS zorunlu.
