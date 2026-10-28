/* HanX Games siteleri (rebirthgame.tr, hanxgames.net) — çerezsiz ziyaret sayacı.
   Çerez, kimlik, parmak izi ya da tarayıcıda kayıt yok; yalnız günlük TOPLAM sayılar Firebase Realtime Database'e gider:
   site/<gün>/<site>/{sayfa|giris|kaynak|dil|cihaz|tik}/<anahtar> += 1 (sunucu artırımı). IP adresi kaydedilmez.
   giris = siteye dışarıdan gelinen sayfa açılışı (ziyaret), kaynak = gelinen sitenin türü (yalnız alan adından), tik = mağaza
   bağlantısına tıklama. "Do Not Track" / GPC açıksa hiçbir şey gönderilmez. Kurallar: YenidenDogus panel/database.rules.json "site".
   Okuma (yönetici): YenidenDogus/ajanlar/site/ziyaret.py. Aynı dosya hanxgames.net/assets/js/sayac.js. */
(function () {
  "use strict";
  var DB = "https://dead-mans-deck-global-default-rtdb.europe-west1.firebasedatabase.app";
  var host = location.hostname.replace(/^www\./, "");
  var SITE = host === "rebirthgame.tr" ? "rebirthgame" : host === "hanxgames.net" ? "hanxgames" : "";
  if (!SITE) return;   // yerel önizleme ve kopyalar sayılmaz
  if (navigator.doNotTrack === "1" || window.doNotTrack === "1" || navigator.globalPrivacyControl === true) return;

  function anahtar(x) {
    return String(x || "").toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40) || "yok";
  }
  function gonder(yollar) {
    var veri = {};
    yollar.forEach(function (y) { veri[y] = { ".sv": { increment: 1 } }; });
    // POST + yöntem değiştirme = ön uçuşsuz basit istek; sayfa kapanırken de gider (sendBeacon)
    var url = DB + "/site/" + new Date().toISOString().slice(0, 10) + "/" + SITE + ".json?x-http-method-override=PATCH&print=silent";
    var govde = JSON.stringify(veri);
    try { if (navigator.sendBeacon && navigator.sendBeacon(url, new Blob([govde], { type: "text/plain" }))) return; } catch (e) {}
    try { fetch(url, { method: "POST", body: govde, mode: "no-cors", keepalive: true, credentials: "omit" }); } catch (e) {}
  }

  var DILLER = ["tr", "es", "pt", "de", "fr", "id", "ja", "ko", "zh"];
  var parca = location.pathname.split("/").filter(Boolean);
  var dil = "";
  if (SITE === "hanxgames") {   // hanxgames.net: dil yolun başında (/tr/...), yoksa İngilizce
    dil = DILLER.indexOf(parca[0]) >= 0 ? parca.shift() : "en";
  } else {
    dil = (window.RBDil && window.RBDil.sec()) || document.documentElement.lang || "en";
  }
  var sayfa = parca.length ? parca[parca.length - 1].replace(/\.html$/, "") : "";
  if (!sayfa || sayfa === "index") sayfa = parca.length > 1 ? parca[parca.length - 2] : "ana";

  var KAYNAK = [[/^play\.google\.com$/, "play"], [/(^|\.)google\.[a-z.]+$/, "google"], [/(^|\.)bing\.com$/, "bing"],
    [/(^|\.)yandex\.[a-z.]+$/, "yandex"], [/(^|\.)duckduckgo\.com$/, "duckduckgo"], [/(^|\.)reddit\.com$/, "reddit"],
    [/(^|\.)(youtube\.com|youtu\.be)$/, "youtube"], [/(^|\.)itch\.io$/, "itch"], [/(^|\.)(facebook\.com|fb\.com)$/, "facebook"],
    [/(^|\.)instagram\.com$/, "instagram"], [/(^|\.)(t\.co|x\.com|twitter\.com)$/, "x"], [/(^|\.)tiktok\.com$/, "tiktok"],
    [/(^|\.)discord(app)?\.com$/, "discord"], [/(^|\.)(t\.me|telegram\.org)$/, "telegram"], [/(^|\.)whatsapp\.com$/, "whatsapp"],
    [/^hanxgames\.net$/, "hanxgames"], [/^rebirthgame\.tr$/, "rebirthgame"]];
  var ref = "";
  try { ref = document.referrer ? new URL(document.referrer).hostname.replace(/^www\./, "") : ""; } catch (e) {}
  var yollar = ["sayfa/" + anahtar(sayfa)];
  if (ref !== host) {   // dışarıdan gelindi: bir ziyaret
    var kat = ref ? "diger" : "dogrudan";
    for (var i = 0; i < KAYNAK.length; i++) if (KAYNAK[i][0].test(ref)) { kat = KAYNAK[i][1]; break; }
    var mobil = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
    yollar.push("giris/" + anahtar(sayfa), "kaynak/" + kat, "dil/" + anahtar(dil), "cihaz/" + (mobil ? "mobil" : "masaustu"));
  }
  gonder(yollar);

  // mağaza ve topluluk bağlantılarına tıklamalar (yalnız hedefin türü)
  var HEDEF = [[/^play\.google\.com$/, "play"], [/(^|\.)itch\.io$/, "itch"], [/^apps\.apple\.com$/, "appstore"],
    [/(^|\.)reddit\.com$/, "reddit"], [/(^|\.)(youtube\.com|youtu\.be)$/, "youtube"]];
  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    var h = "";
    try { h = new URL(a.href, location.href).hostname.replace(/^www\./, ""); } catch (err) { return; }
    for (var i = 0; i < HEDEF.length; i++) if (HEDEF[i][0].test(h)) { gonder(["tik/" + HEDEF[i][1]]); return; }
  }, true);
})();
