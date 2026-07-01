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
CKEY = os.environ.get("ANTHROPIC_API_KEY"); CMODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
# Redaksiyon (dil düzeltme) ucuz model — analizden ayrı tutulur
PMODEL = os.environ.get("ANTHROPIC_PROOFREAD_MODEL", "claude-haiku-4-5-20251001")
WP = os.environ.get("WP_URL", "http://localhost:8091"); USER = os.environ.get("WP_USER", "pipeline-bot"); APP = os.environ.get("WP_APP_PASS")

EVIDENCE_SYS = (
"Sen bir araştırma asistanısın. Verilen haber başlığı/iddiaları hakkında web'de KANIT topla. "
"SINIFLANDIRMA veya HÜKÜM VERME; yalnızca olgu ve kaynak getir. "
"AİHM/AYM/Yargıtay İÇTİHADI ARAMA — içtihat değerlendirmesi sonraki (Claude) aşamaya aittir, orada hazır referans var. "
"Senin işin: haberin OLGULARINI ve bunları yayımlayan/doğrulayan mecra kaynaklarını bulmak; isnadın haberdeki "
"HUKUKİ STATÜSÜNÜ (iddia / soruşturma / iddianame / yerel mahkeme kararı / kesinleşmiş mahkûmiyet) saptamak. "
"Düz metin döndür: (1) haberin/iddiaların kısa özeti, (2) her iddia için olgusal kanıt ve kaynak (mecra + varsa link), "
"(3) isnadın hukuki statüsü. AYRICA her iddia için PRİMER kaynağı izlemeye çalış: iddia birincil bir belgeye/"
"resmi kayda mı dayanıyor, yoksa yalnızca başka medya haberlerine / 'belirtiliyor-konuşuluyor' gibi anonim "
"aktarımlara mı? Vefat etmiş kişilere ya da üçüncü ağıza atfedilen alıntıların doğrulanıp doğrulanamadığını not et. "
"Tarafsız ol; uydurma yok.")

CLAUDE_SYS = (
"Sen kıdemli bir doğruluk denetimi analisti ve insan hakları/medya hukuku editörüsün. Sana bir haber başlığı "
"ve bir ARAŞTIRMA BRİFİ (web + AİHM/AYM/Yargıtay bulguları) verilecek. Bu kanıtı kullanarak AKICI, ölçülü, "
"hukuk-gazetecilik dilinde TARAFSIZ bir TASLAK rapor üret.\n"
"ÜSLUP — İNSANİ VE EDEBİ: Bir köşe yazarı-hukukçu titizliğiyle, AKICI ve EDEBÎ bir Türkçeyle yaz. Mekanik, "
"maddeleyen, 'rapor dili' kuruluğundan kaçın; gelişmiş paragraflar kur, geçişleri yumuşat, gerektiğinde ölçülü "
"bir imge veya ironi kullan — ama abartıya, süslemeye ve duygu sömürüsüne kaçma. Metin, deneyimli bir insan "
"hakları avukatının elinden çıkmış gibi okunmalı: insani, sakin, vicdanlı ama daima kanıta ve hukuka bağlı. "
"Klişe/şablon kalıplardan, her dosyada aynı cümleleri/atıfları tekrarlamaktan kaçın (özellikle 'AİHM'nin X "
"kararında...' kalıbı yapay durur). genel_degerlendirme KISA DEĞİL: hukuki statüyü, kanıt durumunu, çerçeve "
"sorunlarını ve insani boyutu birbirine bağlayan GELİŞMİŞ, ÇOK PARAGRAFLI bir değerlendirme olmalı; ilkeyi "
"somut olguya uygulayarak, neden-sonuç zinciriyle anlat (yüzeysel tek cümle YASAK).\n"
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
"bir kez, doğru biçimde an (içtihat kaynağın aşağıdaki küratörlü liste; Gemini bunu getirmez). "
"DOĞRULANMIŞ İÇTİHAT (yalnızca bunları, içeriğini UYDURMADAN kullan; ayrıntı docs/HUKUKI-CERCEVE.md): "
"Yalçınkaya/Türkiye [BD] 15669/20, 26.09.2023 = ByLock kullanımını 'bilerek örgüte katılma' saymak özel kast "
"şartını yok sayar, m.7 ihlali (ayrıca m.6/1, m.11); sistemik sorun. "
"Yasak/Türkiye [BD] 05.05.2026 = eğitim ağındaki geçmiş, örgütün niteliğini bilme/kast'ı tek başına kanıtlamaz; "
"m.7 ve m.3 ihlali (2024 daire kararını bozdu). "
"Akgün/Türkiye 19699/18, 20.07.2021 = salt 'ByLock kullanıcısı' belgesi makul şüphe için yetmez (m.5). "
"Pişkin/Türkiye 33399/18, 15.12.2020 = KHK ihracında mahkeme tam denetim yapmadı (m.6/1, m.8). "
"Şahin Alpay/Mehmet Hasan Altan 20.03.2018 = gazeteci tutukluluğu, makul şüphe yok (m.5/1, m.10). "
"Kavala/Türkiye 10.12.2019 ve Demirtaş No.2 [BD] 22.12.2020 = gizli/siyasi saikli tutukluluk (m.18, m.5 ile). "
"Salduz/Türkiye [BD] 36391/02, 27.11.2008 = ilk sorgudan itibaren müdafi hakkı (m.6/3-c).\n"
"- Olgu/yorum ayır; nötr dil; uydurma yok; tek tarafın beyanıyla 'doğru/yanlış' İLAN ETME.\n"
"- Bir grubu/topluluğu TOPTAN suçlu/dışlayıcı gösteren ifadeler olgu değildir.\n"
"=== TÜRK BASINI FETÖ/GÜLEN HABERCİLİĞİ — KRİTİK OKUMA (ÇOK ÖNEMLİ) ===\n"
"Bir haber editörü VE insan hakları uzmanı gözüyle oku. Türk basınında 10+ yıldır süren örüntü: önce bir İDDİA "
"ortaya atılır, sonra 'haberleştirmek' için içi doldurulur. İDDİANIN HABER YAPILMASI ONU DOĞRU KILMAZ. Şu "
"teknikleri TEK TEK tespit et ve her birini çürüt:\n"
"(a) ATIF ZİNCİRİNİN ÖZYİNELEMELİ DOĞRULANMASI (EN KRİTİK): Sadece haberin değil, DAYANDIĞI ATFIN, hatta "
"ATFIN ATFININ doğruluğunu ölç. Türk basınında haber çoğu kez daha önce 'haberleşmiş' bir yalana atıf yapar; "
"sorun şudur ki o önceki haber de yalandır, onun atıf yaptığı da. Zinciri geriye doğru sür: bu iddia nereye "
"dayanıyor? O kaynak primer bir belgeye/kayda mı, yoksa başka bir habere/iddiaya/anonim aktarıma mı dayanıyor? "
"Zincirin her halkasını ayrı ayrı tart. ÖNEMLİ KURALLAR: (i) Bir iddianın daha önce haber yapılmış/tekrarlanmış "
"olması onu DOĞRU KILMAZ — tekrar, kanıt değildir. (ii) Kaynak tamamen YORUM/değer yargısı üzerine konuşmuşsa "
"bu olgu değildir (siniflandirma=gorus); olgu gibi sunulmuşsa çarpıtmadır. (iii) Kaynak doğrudan YALAN söylüyor "
"olabilir; beyanın sahibinin kim olduğu ve menfaati sorgulanmalı. (iv) 'belirtiliyor, konuşuluyor, öğrenildi, "
"iddia edildi, biliniyor' gibi pasif/kaynaksız kalıplar primer kaynak DEĞİLDİR → doğrulanamaz/mesnetsiz. "
"gerekçede zinciri açıkça yaz: 'Haber X'e dayanıyor; X de kanıt göstermeyen Y haberine dayanıyor; primer belge "
"yok' gibi.\n"
"(b) ÖLÜ veya ÜÇÜNCÜ-AĞIZ ALINTILARI: Vefat etmiş kişilere (ör. yıllar önce ölmüş siyasiler) ya da 'bir "
"arkadaşına söylediği iddia edilen', 'şu ifadeleri kullandı' biçiminde aktarılan sözler DOĞRULANAMAZ — kişinin "
"gerçekten söyleyip söylemediği teyit edilemez; bunları olgu gibi sunma, attribüsyonu sorgula.\n"
"(c) ESKİ OLAYLAR: 15-45 yıl önceki olaylar (darbeler, kaset kumpasları, eski seçimler, istifalar) hakkında "
"'FETÖ tertibiydi' türü kesin anlatımlar, KESİNLEŞMİŞ mahkeme hükmü olmadıkça doğrulanamaz; zamanın geçmesi "
"iddiayı kanıt yapmaz.\n"
"(d) MAHKEME / TANIK / İTİRAFÇI BEYANI ≠ GERÇEK: Bir beyanın mahkemede, ifadede veya iddianamede yer alması "
"onu DOĞRU KILMAZ. Tanık, 'itirafçı', gizli tanık veya etkin pişmanlık beyanları; menfaat (ceza indirimi, "
"tahliye), baskı, yönlendirme veya husumet nedeniyle GERÇEK DIŞI olabilir. Bu tür beyanlar, bağımsız ve somut "
"delille (belge, kayıt, maddi bulgu) desteklenmedikçe KANIT değil, sınanması gereken birer İDDİADIR. Bir kişi/"
"grup hakkında 'hiç yapmadığı' bir şey, böyle beyanlarla suçlamaya dönüştürülebilir. Haber bu beyanları kesin "
"gerçek gibi sunuyorsa çarpıtma/iftira say; gerekçede 'beyan tek başına kanıt değildir, doğrulayıcı delil "
"sunulmamış' diye belirt.\n"
"(d-2) 'İTİRAF/KABUL ETTİ' İDDİALARI: 'X şunu itiraf etti / kabul etti / açıkça söyledi' biçimindeki her ifade "
"bir OLGU DEĞİL, doğrulanması gereken bir iddiadır. Bu tür bir kabul iddiasını olgu saymadan önce ŞUNU sor ve "
"gerekçeye yaz: Bu kabul TAM OLARAK NEREDE yapılmış (hangi video/röportaj/belge/duruşma), NE ZAMAN, ve içerik "
"BAĞIMSIZ olarak erişilip doğrulanabiliyor mu? Kaynak (birincil kayıt/bağlantı) gösterilmemişse ya da yalnızca "
"başka bir habere/‘brife göre’ türü aktarıma dayanıyorsa, kabulü OLGU sayma → siniflandirma=dogrulanamaz ve "
"'iddia edilen kabulün birincil kaynağı/yeri gösterilmemiş' diye açıkça belirt. Özellikle kişinin özel hayatına "
"(ilişki, ahlak vb.) dair 'kabul etti' iddiaları hem itibar suikastı hem de m.8 (özel hayat) sorunu doğurur; "
"asla 'kabul ettiği için doğrudur' deme.\n"
"(e) YAŞAYAN İSİMLER: Yaşayan kişileri ismen 'örgüt üyesi/bağlantılı/militan/kripto' göstermek, kesinleşmiş "
"mahkûmiyet yoksa İFTİRA ve masumiyet karinesi ihlalidir. Her ismi AYRI iddia yap.\n"
"(f) ANONİM İNSİNÜASYON: 'eşi bağlantılı olan isim', 'kripto isimler', 'bazı milletvekilleri' gibi muğlak "
"hedef göstermeler mesnetsizdir.\n"
"ENUMERASYON: Tek bir haberde ÇOK SAYIDA (çoğu kez 10+) ayrı yalan/iftira/çarpıtma bulunur. BUNLARI BİRLEŞTİRME; "
"her tekniği/iddiayı/alıntıyı/tarihi AYRI bir iddialar[] kalemi yap ve tek tek çürüt. Haberin TAM METNİNİ (sadece "
"başlığı değil) bu gözle tara.\n"
"(g) SUÇLAMANIN ARAÇSALLAŞTIRILMASI (WEAPONIZATION): 'FETÖ/terör örgütü üyeliği' suçlaması Türkiye'de çoğu kez "
"somut bir örgüt bağına değil, hedef kişiyi/grubu siyaseten itibarsızlaştırmaya yarayan AKIŞKAN bir YAFTA olarak "
"kullanılır. Aynı yafta siyasi konjonktüre göre yön değiştirir: bir dönem iktidara yakın gazeteler bir muhalifi "
"(ör. Kılıçdaroğlu) 'FETÖ'cü' ilan ederken başka dönem tersini yapar; dün CHP AKP'yi, bugün tersi suçlar; hatta "
"hiç alakası olmayan kişilere (ör. Rahip Brunson) ya da 13-14 yaşındaki çocuklara bile yöneltilir. Eğer haberde "
"'FETÖ' suçlaması KANITA dayalı bir isnattan çok bu tür ARAÇSALLAŞTIRILMIŞ/silah haline getirilmiş bir yafta "
"olarak kullanılıyorsa, araclastirma alanına 2-4 cümlelik bir not yaz: kime karşı, hangi siyasi amaçla "
"kullanıldığını, varsa yön değiştirme/çifte standart örüntüsünü açıkla. Bunun habercilik değil, haberciliğin "
"insanları hizaya sokma/siyasi rakibi tasfiye etme aracı olarak kullanılması olduğunu vurgula. Araçsallaştırma "
"yoksa araclastirma'yı boş bırak.\n"
"(h) MECRANIN TUTUMU (FAİL mi, İFŞACI mı?): Haberi yayımlayan mecranın konumunu ayırt et. Mecra yaftayı/"
"suçlamayı KENDİSİ mi üretiyor/savunuyor (failin yanında, hedef gösteriyor) — YOKSA bu absürtlüğü/haksızlığı/"
"araçsallaştırmayı ELEŞTİREL biçimde TEŞHİR mi ediyor (bağımsız gazetecilik, mağdurun/kamu yararının yanında, "
"ironi/eleştiri ile)? EĞER mecra weaponization'ı veya haksız suçlamayı ifşa/eleştiri amacıyla aktarıyorsa, sorun "
"O HABERDE DEĞİLDİR: haber_sorunu=[\"sorun_yok\"], medya_kategori=kabul_edilebilir yap; çarpıtmayı/iftirayı "
"yaftayı ÜRETEN faile (iddianame/iktidar yanlısı kaynak) ata ve araclastirma'da bunu açıkla. Yalnızca yaftayı "
"ÜRETEN/SAVUNAN/yayan yayınları sorunlu işaretle. Eleştirel/bağımsız haberciliği cezalandırma.\n"
"(i) SIRADAN/YASAL FİİLİN SUÇLAŞTIRILMASI: İçinden geçtiğimiz dönemin en tipik tekniği — herkes için YASAL "
"olan sıradan bir eylemin, yalnızca faile/gruba atfen 'suç' ya da 'terör delili' gibi sunulması. Örnekler: "
"piknik/çay-bahçesi buluşması, sohbet toplantısı, kermes düzenlemek/katılmak, bağış/himmet/burs, gazete-dergi "
"aboneliği, bir uygulamayı (ByLock vb.) indirmek, bankada (Bank Asya) hesap açmak, dernek/sendika/vakıf üyeliği, "
"belirli okul/dershaneye gitmek; bir KİTABI ya da KUR'AN TEFSİRİNİ / dini eseri okumak-bulundurmak (sırf yazarı "
"yargılanan/itham edilen biri diye); VE ÖZELLİKLE bir suçtan ötürü tutuklanan/yargılanan kişinin EŞİNE veya "
"ÇOCUKLARINA insani yardımda (gıda, burs, barınma) bulunmak. Bu tür yasal/insani fiilleri suç/delil gibi sunan "
"haberi işaretle ve gerekçede ŞUNU vurgula: (1) suçta kanunilik ve öngörülebilirlik (AİHS m.7, Anayasa m.38) "
"gereği herkese açık ve yasal bir fiil, onu yapanın kimliğine bakılarak sonradan suça dönüştürülemez; (2) yasal "
"yayımlanmış bir eseri okumak/bulundurmak ifade ve bilgiye erişim (m.10) ile din özgürlüğü (m.9) kapsamındadır; "
"(3) tutuklu/mağdur ailelerine ve çocuklarına yardım, cezaların ŞAHSİLİĞİ ilkesi (Anayasa m.38: ceza yalnızca "
"fiili işleyene aittir) gereği suç olamaz — aileyi/çocuğu hedef almak KOLEKTİF CEZALANDIRMADIR; (4) örgüt "
"üyeliği kişiselleştirilmiş kast ve somut delil ister, tek başına böyle bir fiil yetmez (krş. Yalçınkaya 2023). "
"Bu örüntüyü, yapay AİHM atfından kaçınarak, kendi cümlelerinle ve somut habere bağlayarak anlat.\n"
"- İHLAL EDİLEN HAKLAR: Haberin veya aktardığı sürecin hangi temel hak ve özgürlükleri ihlal ettiğini/risk "
"altına aldığını belirle ve ihlal_edilen_haklar dizisine ekle. Anahtarlar: ozel_hayat (özel hayatın gizliliği — "
"isim/foto/aile/evlilik gibi mahrem detayların ifşası), din_vicdan (din ve vicdan özgürlüğü), orgutlenme "
"(dernek/vakıf/örgütlenme özgürlüğü), masumiyet (masumiyet karinesi), adil_yargilanma, kanunsuz_ceza, ifade, "
"ayrimcilik, kisi_hurriyeti (kişi hürriyeti ve güvenliği), seref_itibar (şeref ve itibarın korunması). "
"Yalnızca gerçekten zedelenen hakları seç; genel_degerlendirme'de kısaca nasıl zedelendiğini belirt.\n"
"- İLGİLİ KANUN MADDELERİ (YEREL HUKUK): Haberin/sunumun ihlal ettiği ya da kapsamına girdiği SOMUT yerel "
"mevzuat maddelerini kanun_maddeleri dizisine ekle. Sadece uluslararası (AİHS) değil, Türk hukukundaki karşılığını "
"da göster. Bir hukukçu gibi yalnızca GERÇEKTEN uygulanabilir maddeleri, kısa gerekçeyle seç (zorlama yapma; "
"uygun madde yoksa boş dizi []). Tipik adaylar: TCK m.267 (iftira — gerçek dışı somut suç isnadı), TCK m.125 "
"(hakaret/şeref saldırısı), TCK m.216 (halkı kin ve düşmanlığa tahrik veya bir kesimi aşağılama — toptan suçlama/"
"grubu hedef alma), TCK m.285 (soruşturmanın gizliliğini ihlal), TCK m.288 (adil yargılamayı etkilemeye teşebbüs); "
"Anayasa karşılıkları: m.38/4 (masumiyet), m.36 (adil yargılanma), m.26 (ifade), m.20 (özel hayat), m.17 (şeref); "
"ayrıca Basın Kanunu m.3 (doğru haber alma hakkı/basın özgürlüğü sınırı). Her madde için kanun (TCK/Anayasa/"
"Basın Kanunu), madde (örn '267' veya '216/2'), gerekce (bu habere neden uyduğu, 1-2 cümle) ver.\n"
"- ÇOKLU KAYNAK: Haber birden çok mecrada yer aldıysa (sana MECRALAR listesi verilecek), "
"genel_degerlendirme'de bunu belirt (kaç mecra ve başlıcaları) ve aynı iddianın çok sayıda mecrada "
"eşzamanlı yayımının kayda değer bir olgu olduğunu not et; ancak bu tek başına suç/iftira kanıtı değildir.\n"
"SINIFLANDIRMA: dogru|yanlis|dogrulanamaz|mesnetsiz|gorus. 'dogru' SADECE iddia sağlam ve doğrulanabilir "
"kanıtla TAM ve şüphesiz doğrulanıyorsa verilir. Bir kısmı doğru bir kısmı kanıtsız/çarpıtılmışsa 'dogru' DEME → "
"dogrulanamaz veya yanlis kullan ve haber_sorunu'na carpitma ekle. 'kısmen doğru' (kismen_dogru) KULLANMA.\n"
"HABER SORUNU (haber_sorunu dizisi): yalan_haber|iftira|toptan_suclama|carpitma — hiçbiri yoksa [\"sorun_yok\"].\n"
"MEDYA KATEGORİSİ (medya_kategori — TEK anahtar): Haberin uluslararası habercilik/dezenformasyon "
"literatüründeki karşılığını, SORUNLARIN YOĞUNLUĞU VE AĞIRLIĞINA göre ata. Kademeler (ağırdan hafife):\n"
"  • kara_propaganda = Black Propaganda / Character Assassination (Hedef Gösterme): EN AĞIR. Kurgulanmış, "
"sistematik iftira; yaşayan kişileri delilsiz suçlu/örgüt üyesi ilan etme; nefrete tahrik; çok sayıda (≈4+) ayrı "
"yalan/iftira. 'Habercilik' sayılmaz — medya eliyle yargısız infaz. (Genelde yalan_haber+iftira+toptan_suclama "
"birlikte ve TCK 216/267 devrede.)\n"
"  • dezenformasyon = Disinformation / Defamatory Smear: Kasıtlı yalan ve iftira ağırlıklı, zarar niyeti belirgin.\n"
"  • manipulatif = Yellow Journalism / Misleading Spin: Çarpıtma, bağlam saptırma, sansasyon, tek taraflılık.\n"
"  • dogrulanmamis = Misinformation / Unverified: Kaynaksız/doğrulanmamış ama kötü niyet açık değil.\n"
"  • kabul_edilebilir = Acceptable Reporting: Belirgin etik ihlali yok.\n"
"kategori_gerekce: bu kademeyi neden seçtiğini 1-2 cümleyle yaz. Abartma; kanıta dayan ama hak ettiği ağır "
"terimden de KAÇINMA.\n"
"HALK TABİRİ (halk_tabiri): Bu tür bir yayın için Türk halkının/hukukçunun kullanacağı, amiyane ama YERİNDE "
"ve ağır bir tabir yaz — 'en hafif tabirle ...' mantığıyla, kısa (2-4 kelime). Örnekler: 'çamur atma', "
"'kara çalma', 'fişleme/kumpas gazeteciliği', 'talimatlı karalama', 'linç kampanyası'. Küfür/hakaret etme; "
"yalnızca yayının habercilik etiği dışı oluşunu halk diliyle özetleyen tabiri seç. Sorun yoksa boş bırak.\n"
"İNGİLİZCE: Uluslararası (AİHM) okuyucu için ayrıca İngilizce çeviri alanları doldur: baslik_en "
"(başlığın İngilizcesi), ozet_en, genel_degerlendirme_en (aynı içeriğin akıcı İngilizcesi).\n"
"SADECE şu şemada geçerli JSON döndür (markdown YOK):\n"
'{"ozet":"4-6 cümle, bağlamlı paragraf","genel_degerlendirme":"GELİŞMİŞ ÇOK PARAGRAFLI, insani ve edebi; hukuki statü + atıf zinciri değerlendirmesi + çerçeve sorunları + (gerekiyorsa) AİHM/AYM dayanağı",'
'"baslik_en":"English title","ozet_en":"English summary","genel_degerlendirme_en":"English assessment",'
'"medya_kategori":"kara_propaganda|dezenformasyon|manipulatif|dogrulanmamis|kabul_edilebilir","kategori_gerekce":"1-2 cümle","halk_tabiri":"amiyane 2-4 kelime","araclastirma":"2-4 cümle veya boş",'
'"haber_sorunu":["..."],"ihlal_edilen_haklar":["masumiyet","ifade",...],'
'"kanun_maddeleri":[{"kanun":"TCK","madde":"267","gerekce":"neden uyuyor, 1-2 cümle"}],'
'"iddialar":[{"iddia_metni":"","siniflandirma":"","gerekce":"2-3 cümle: kriter + kanıt","dayanak_kaynak_url":"yalnızca tam http(s) URL; yoksa boş, kaynak adı YAZMA"}],'
'"isim_verilen_suclama":"evet|hayir","isim_verilen_suclama_gerekce":""}')

def _ilk_json(t):
    """Metindeki İLK tam JSON nesnesini ayıkla; sonrasındaki fazla içeriği yok say (Extra data hatasına dayanıklı)."""
    i = t.find("{")
    if i < 0: raise ValueError("JSON nesnesi bulunamadı")
    try:
        obj, _ = json.JSONDecoder().raw_decode(t[i:])
        return obj
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.DOTALL)   # son çare: greedy
        if not m: raise ValueError("Geçerli JSON yok")
        return json.loads(m.group(0))

def resolve(u):
    """Yönlendirme linklerini (grounding redirect + Google News RSS) gerçek mecra URL'sine çöz."""
    u = (u or "").split(",")[0].strip()
    if not u: return u
    if "grounding-api-redirect" not in u and "news.google.com" not in u: return u
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=12)
        f = r.geturl(); r.close()
        # Google içi bir sayfaya düştüyse (consent/redirect çözülemedi) orijinali koru
        if f and "google.com" not in (f.split("/", 3)[2] if "://" in f else f): return f
        return u
    except Exception: return u

def claude_analyze(baslik, metin, brief, key, model, mecralar=None):
    mec = ""
    if mecralar:
        mec = f"\n\nMECRALAR ({len(mecralar)} mecrada yer aldı): {', '.join(mecralar)}"
    body = json.dumps({"model": model, "max_tokens": 8000, "system": CLAUDE_SYS,
        "messages": [{"role": "user", "content": f"BAŞLIK: {baslik}\n\nHABER BAĞLAMI: {metin}{mec}\n\n=== ARAŞTIRMA BRİFİ (Gemini) ===\n{brief}"}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    data = json.loads(urllib.request.urlopen(req, timeout=300).read())  # Opus derin yazım uzun sürebilir
    return _ilk_json(data["content"][0]["text"])

PROOF_SYS = (
"Sen titiz bir Türkçe düzeltmen/editörsün. Sana bir doğruluk denetimi raporunun JSON çıktısı verilecek. "
"GÖREVİN YALNIZCA DİL DÜZELTME: yazım/imla hatalarını, bozuk veya eksik kelimeleri, devrik ve düşük cümleleri, "
"noktalama ve akıcılık sorunlarını düzelt; metni anlaşılır, düzgün ve akıcı Türkçeye çevir.\n"
"KESİNLİKLE DEĞİŞTİRME: anlamı, hükmü, sınıflandırmayı; kanun adlarını/madde numaralarını; kişi-kurum adlarını; "
"URL'leri; tarihleri. Yeni olgu/iddia UYDURMA, var olanı çıkarma. Sadece İFADEYİ düzelt.\n"
"Sana verilen JSON şemasını AYNEN, tüm anahtarlarıyla, yalnızca Türkçe metin alanları düzeltilmiş halde döndür. "
"İngilizce (_en) alanlarda yalnızca bariz yazım hatası varsa düzelt. Markdown YOK, sadece geçerli JSON.")

def claude_proofread(analiz, key, model):
    """İkinci geçiş: yalnızca Türkçe dil düzeltme. Yapısal alanlar orijinalden korunur (güvenli merge)."""
    try:
        body = json.dumps({"model": model, "max_tokens": 8000, "system": PROOF_SYS,
            "messages": [{"role": "user", "content": "Şu raporun metinlerini düzelt:\n" + json.dumps(analiz, ensure_ascii=False)}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        data = json.loads(urllib.request.urlopen(req, timeout=180).read())
        d = _ilk_json(data["content"][0]["text"])
    except Exception as e:
        print(f"    (dil düzeltmesi atlandı: {e})"); return analiz
    out = dict(analiz)
    # Düz metin alanları: düzeltilmiş halini al
    for f in ("ozet", "genel_degerlendirme", "baslik_en", "ozet_en", "genel_degerlendirme_en",
              "kategori_gerekce", "halk_tabiri", "araclastirma", "isim_verilen_suclama_gerekce"):
        if isinstance(d.get(f), str) and d[f].strip():
            out[f] = d[f]
    # İddialar: yalnızca metin+gerekçe düzelt; siniflandirma ve URL korunur
    di = d.get("iddialar")
    if isinstance(di, list) and len(di) == len(analiz.get("iddialar", [])):
        for orig, fix in zip(out["iddialar"], di):
            if isinstance(fix, dict):
                if isinstance(fix.get("iddia_metni"), str) and fix["iddia_metni"].strip(): orig["iddia_metni"] = fix["iddia_metni"]
                if isinstance(fix.get("gerekce"), str) and fix["gerekce"].strip(): orig["gerekce"] = fix["gerekce"]
    # Kanun maddeleri: yalnızca gerekçe düzelt; kanun adı + madde no korunur
    dk = d.get("kanun_maddeleri")
    if isinstance(dk, list) and len(dk) == len(analiz.get("kanun_maddeleri", [])):
        for orig, fix in zip(out["kanun_maddeleri"], dk):
            if isinstance(fix, dict) and isinstance(fix.get("gerekce"), str) and fix["gerekce"].strip(): orig["gerekce"] = fix["gerekce"]
    return out

def wp_create(title, analiz, kaynaklar):
    valid = {"dogru","yanlis","dogrulanamaz","mesnetsiz","gorus"}  # kismen_dogru kullanılmıyor
    sorunlar = {"yalan_haber","iftira","toptan_suclama","carpitma","sorun_yok"}
    iddialar = [{"iddia_metni": str(x.get("iddia_metni",""))[:2000],
                 "siniflandirma": x.get("siniflandirma") if x.get("siniflandirma") in valid else "dogrulanamaz",
                 "gerekce": str(x.get("gerekce","")), "dayanak_kaynak_url": resolve(x.get("dayanak_kaynak_url","") or "")}
                for x in analiz.get("iddialar", [])]
    hs = [s for s in (analiz.get("haber_sorunu") or []) if s in sorunlar] or ["sorun_yok"]
    haklar_ok = {"ozel_hayat","din_vicdan","orgutlenme","masumiyet","adil_yargilanma","kanunsuz_ceza","ifade","ayrimcilik","kisi_hurriyeti","seref_itibar"}
    ih = [h for h in (analiz.get("ihlal_edilen_haklar") or []) if h in haklar_ok]
    kanunlar = [{"kanun": str(k.get("kanun",""))[:40], "madde": str(k.get("madde",""))[:20], "gerekce": str(k.get("gerekce",""))[:600]}
                for k in (analiz.get("kanun_maddeleri") or []) if (k.get("kanun") or k.get("madde"))]
    kat_ok = {"kara_propaganda","dezenformasyon","manipulatif","dogrulanmamis","kabul_edilebilir"}
    mk = analiz.get("medya_kategori") if analiz.get("medya_kategori") in kat_ok else ""
    isim = "hayir" if analiz.get("isim_verilen_suclama") == "hayir" else "evet"
    payload = {"title": title[:120], "status": "draft",
        "content": "",  # içerik analiz bölümlerinden (the_content filtresi) gelir; placeholder yok
        "meta": {"haberler_ozet": analiz.get("ozet",""), "haberler_genel_degerlendirme": analiz.get("genel_degerlendirme",""),
                 "haberler_baslik_en": analiz.get("baslik_en",""), "haberler_ozet_en": analiz.get("ozet_en",""),
                 "haberler_genel_degerlendirme_en": analiz.get("genel_degerlendirme_en",""),
                 "haberler_haber_sorunu": json.dumps(hs, ensure_ascii=False),
                 "haberler_medya_kategori": mk,
                 "haberler_kategori_gerekce": analiz.get("kategori_gerekce",""),
                 "haberler_halk_tabiri": str(analiz.get("halk_tabiri",""))[:120],
                 "haberler_araclastirma": str(analiz.get("araclastirma",""))[:1200],
                 "haberler_ihlal_haklar": json.dumps(ih, ensure_ascii=False),
                 "haberler_kanun_maddeleri": json.dumps(kanunlar, ensure_ascii=False),
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
        print("    ⚠ Gemini kanıt yok — yalnızca başlık/çerçeve ile değerlendirilecek (kaynaksız)")
        brief = ("(Bağımsız web araştırması yapılamadı — kota/erişim yok. Değerlendirme YALNIZCA haberin "
                 "başlığı ve çerçevesi üzerinden: somut iddialar bağımsız kanıtla doğrulanamaz kabul edilmeli; "
                 "ancak iftira, çarpıtma, toptan suçlama gibi ÇERÇEVE/SUNUM sorunları metnin kendisinden tespit "
                 "edilebilir. Kaynak listesi boş.)")
        sources = []
    try:
        analiz = claude_analyze(baslik, metin, brief, CKEY, CMODEL, mecralar)
    except Exception as e:
        print(f"    ✗ Claude hata: {e}"); return None
    if not analiz.get("iddialar"):
        print("    ✗ Somut iddia yok — fact-check konusu değil, atlandı"); return None
    # Yalnızca SIKINTILI haberleri kaydet (yalan/iftira/toptan/çarpıtma). Nötr haber atlanır.
    hs_real = [s for s in (analiz.get("haber_sorunu") or []) if s in {"yalan_haber", "iftira", "toptan_suclama", "carpitma"}]
    if os.environ.get("HIBRIT_ONLY_PROBLEM", "1") != "0" and not hs_real:
        print("    ↷ Belirgin sorun yok (nötr haber) — kaydedilmedi"); return None
    # Opsiyonel redaksiyon geçişi — VARSAYILAN KAPALI (Opus edebî üslubu zaten temiz üretir;
    # ucuz model bu üslubu düzleştirebilir). Açmak için HIBRIT_PROOFREAD=1.
    if os.environ.get("HIBRIT_PROOFREAD", "0") == "1":
        analiz = claude_proofread(analiz, CKEY, PMODEL)
        print("    ✎ dil düzeltmesi yapıldı")
    if not kaynaklar:  # clustering yoksa Gemini'nin bulduğu kaynaklar
        kaynaklar = [{"kaynak_adi": t or "kaynak", "orijinal_url": resolve(u), "yayin_tarihi": ""} for t, u in sources[:8]]
    # Kaynak linki güvencesi: en az bir geçerli http(s) link olmalı
    gecerli = [k for k in (kaynaklar or []) if str(k.get("orijinal_url", "")).startswith("http")]
    if not gecerli:
        print("    ⚠ UYARI: orijinal haber linki yok — dosyada 'kaynak eksik' uyarısı görünecek; inceleme şart")
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
            kayn.setdefault(ad, {"kaynak_adi": ad, "orijinal_url": resolve(m.get("orijinal_url", "")), "yayin_tarihi": m.get("yayin_tarihi", "")})
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
