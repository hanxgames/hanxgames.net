"""Builds the site: injects shared partials into the English pages, then
generates every other language under /<code>/ from them.

Run from the repo root after editing any page, partial or translation:
    python tools/sync.py             # English + all languages
    python tools/sync.py --lang de   # English + only German (handy while translating)

English pages are the source. Never edit files under tr/, es/, pt/, de/ or fr/
by hand: they are overwritten on every run. Translations live in
tools/i18n/<code>.py; a language is built only when its file exists.

Markers inside English pages:
    <!-- @head --><!-- /@head -->       hreflang links (+ browser-language redirect)
    <!-- @schema --><!-- /@schema -->   JSON-LD built from the (translated) page
    <!-- @nav --><!-- /@nav -->
    <!-- @footer --><!-- /@footer -->
    <!-- @stores gp="com.package" apple="123456" --><!-- /@stores -->
    <!-- @more --><!-- /@more -->       links to the other game pages
    <!-- @404i18n --><!-- /@404i18n --> (404.html only) per-language 404 text
The nav partial contains <!-- @lang --><!-- /@lang --> for the language menu.
"""
import html as htmllib, importlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://hanxgames.net'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'i18n'))

# Display order of the language menu. Codes without tools/i18n/<code>.py are skipped.
LANG_INFO = {
    'en': ('English', 'en_US'),
    'tr': ('Türkçe', 'tr_TR'),
    'es': ('Español', 'es_ES'),
    'pt': ('Português', 'pt_BR'),
    'de': ('Deutsch', 'de_DE'),
    'fr': ('Français', 'fr_FR'),
}
ONLY = sys.argv[sys.argv.index('--lang') + 1] if '--lang' in sys.argv else None
MODULES = {}
for _c in LANG_INFO:
    if _c == 'en' or not os.path.exists(os.path.join(ROOT, 'tools', 'i18n', _c + '.py')):
        continue
    try:
        MODULES[_c] = importlib.import_module(_c)
    except Exception as _e:  # a half-written translation must not block building the others
        if _c == ONLY or ONLY is None:
            raise
        print(f'  (skipping {_c}: {type(_e).__name__}: {_e})')
LANGS = ['en'] + [c for c in LANG_INFO if c in MODULES]
OTHER = [c for c in LANGS if c != 'en']

read = lambda p: open(os.path.join(ROOT, p), encoding='utf-8').read()
NAV, FOOTER = read('partials/nav.html').strip(), read('partials/footer.html').strip()

GP_SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
          '<path fill="#FBBC04" d="M22.018 13.298l-3.919 2.218-3.515-3.493 3.543-3.521 3.891 2.202a1.49 1.49 0 0 1 0 2.594z"/>'
          '<path fill="#4285F4" d="M1.337.924a1.486 1.486 0 0 0-.112.568v21.017c0 .217.045.419.124.6l11.155-11.087L1.337.924z"/>'
          '<path fill="#34A853" d="M13.544 10.989l3.258-3.238L3.45.195a1.466 1.466 0 0 0-.946-.179l11.04 10.973z"/>'
          '<path fill="#EA4335" d="M13.544 13.056l-11 10.933c.298.036.612-.016.906-.183l13.324-7.54-3.23-3.21z"/></svg>')
APPLE_SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#fff" d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 '
             '1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 '
             '1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857'
             '-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 '
             '1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/></svg>')
GLOBE_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">'
             '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.2 3 14.8 0 18M12 3c-3 3.2-3 14.8 0 18"/></svg>')

EN_TEXT = dict(badges=(('Get it on', 'Google Play'), ('Download on the', 'App Store')), lang_label='Language')

# Facts used for the VideoGame structured data (descriptions come from each page).
GAMES = {
    '/rebirth/': dict(name='ReBirth: Rebuild & Resist', slug='rebirth', genre=['Strategy', 'Simulation'], gp='com.hantro.business', price='0', community='https://www.reddit.com/r/ReBirthSocial/'),
    '/poker/': dict(name='Hantro: Poker Roguelike', slug='poker', genre=['Card', 'Roguelike'], gp='com.ilhantro.hantro', price='0'),
    '/blackjack/': dict(name='Hantro: BlackJack Roguelike', slug='blackjack', genre=['Card', 'Strategy', 'Roguelike'], gp='com.hantro.blackjack', apple='6761393761', price='0'),
    '/911-idle-dispatch/': dict(name='911: Idle Dispatch', slug='idle-dispatch', genre=['Simulation', 'Strategy', 'Idle'], gp='com.hantro.wwiii', apple='6813881867', price='0'),
    '/darkway/': dict(name='DarkWay: Kingdom Choices', slug='darkway', genre=['Role Playing', 'Strategy', 'Card'], gp='com.hantro.darkway.rpg', apple='6801437989', price='0.49'),
    '/moba-manager/': dict(name='Moba Manager: Esports Coach', slug='moba-manager', genre=['Strategy', 'Sports', 'Simulation'], gp='com.hantro.blockblastmaster', price='0'),
    '/ember-keep/': dict(name='Hantro: Ember Keep', slug='ember-keep', genre=['Strategy', 'Tower Defense', 'Roguelike'], gp='hantro.tower.roguelike', apple='6803483619', price='0'),
}
GP_URL = 'https://play.google.com/store/apps/details?id='
APPLE_URL = 'https://apps.apple.com/app/id'
DEV_LINKS = ['https://play.google.com/store/apps/dev?id=4858435727768538175', 'https://apps.apple.com/developer/id1885639647']


def text_for(lang):
    return EN_TEXT if lang == 'en' else dict(badges=MODULES[lang].BADGES, lang_label=MODULES[lang].LANG_LABEL)


def lang_url(here, lang):
    return here if lang == 'en' else '/' + lang + here


def stores(attrs, lang='en'):
    a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
    (gs, gb), (as_, ab) = text_for(lang)['badges']
    out = []
    if a.get('gp'):
        url = a['gp'] if a['gp'].startswith('http') else GP_URL + a['gp']
        out.append(f'<a class="store" href="{url}" target="_blank" rel="noopener">{GP_SVG}<span><small>{gs}</small><b>{gb}</b></span></a>')
    if a.get('apple'):
        url = a['apple'] if a['apple'].startswith('http') else APPLE_URL + a['apple']
        out.append(f'<a class="store" href="{url}" target="_blank" rel="noopener">{APPLE_SVG}<span><small>{as_}</small><b>{ab}</b></span></a>')
    return '\n'.join(out)


NAV_GAMES = re.findall(r'<a href="(/[^"]+/)"><img src="([^"]+)"[^>]*>([^<]+)</a>', NAV)


def more(here):
    items = [f'<a href="{h}"><img src="{i}" alt="" loading="lazy">{n}</a>' for h, i, n in NAV_GAMES if h != here]
    return '<div class="more-games">\n' + '\n'.join(items) + '\n</div>'


def lang_menu(here, active):
    label = text_for(active)['lang_label']
    links = ''.join(
        f'<a href="{lang_url(here, c)}" hreflang="{c}" lang="{c}"{" aria-current=\"true\"" if c == active else ""}>{LANG_INFO[c][0]}</a>'
        for c in LANGS)
    return (f'<details class="lang"><summary aria-label="{label}: {LANG_INFO[active][0]}">{GLOBE_SVG}<span>{active.upper()}</span></summary>'
            f'<div class="lang__menu">{links}</div></details>')


def head_block(here, lang):
    out = [f'<link rel="alternate" hreflang="{c}" href="{SITE}{lang_url(here, c)}">' for c in LANGS]
    out.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{here}">')
    out.append(f'<meta property="og:locale" content="{LANG_INFO[lang][1]}">')
    out += [f'<meta property="og:locale:alternate" content="{LANG_INFO[c][1]}">' for c in LANGS if c != lang]
    if lang == 'en' and OTHER:
        # First visit: follow the browser's language. The language menu stores an explicit choice.
        codes = json.dumps(OTHER).replace('"', "'")
        out.append("<script>try{if(!localStorage.getItem('hx-lang')){var L=%s,n=navigator.languages||[navigator.language||''];"
                   "for(var i=0;i<n.length;i++){var c=(n[i]||'').slice(0,2).toLowerCase();if(c==='en')break;"
                   "if(L.indexOf(c)>-1){location.replace('/'+c+location.pathname+location.hash);break}}}}catch(e){}</script>" % codes)
    return '\n  '.join(out)


def plain(s):
    return htmllib.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def meta(html, attr, key):
    m = re.search(r'<meta %s="%s" content="([^"]*)"' % (attr, re.escape(key)), html)
    return htmllib.unescape(m.group(1)) if m else ''


def ld(obj):
    return ('<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
            + '</script>')


def schema(html, here, lang):
    url = SITE + lang_url(here, lang)
    home = SITE + lang_url('/', lang)
    org = {'@type': 'Organization', '@id': SITE + '/#org', 'name': 'HanX Games', 'url': SITE + '/',
           'logo': SITE + '/assets/brand/logo.webp', 'email': 'hanxdestek@gmail.com', 'sameAs': DEV_LINKS}
    graph = []
    if here == '/':
        graph += [org,
                  {'@type': 'WebSite', 'name': 'HanX Games', 'url': home, 'inLanguage': lang, 'publisher': {'@id': SITE + '/#org'}},
                  {'@type': 'ItemList', 'itemListElement': [
                      {'@type': 'ListItem', 'position': i + 1, 'url': SITE + lang_url(h, lang), 'name': g['name']}
                      for i, (h, g) in enumerate(GAMES.items())]}]
    elif here in GAMES:
        g = GAMES[here]
        stores_ = [GP_URL + g['gp']] + ([APPLE_URL + g['apple']] if g.get('apple') else [])
        shots = sorted(set(re.findall(r'src="(/assets/games/%s/shot-\d+\.webp)"' % g['slug'], html)))
        graph.append({
            '@type': ['VideoGame', 'MobileApplication'], 'name': g['name'], 'url': url, 'inLanguage': lang,
            'description': meta(html, 'name', 'description'),
            'image': meta(html, 'property', 'og:image'),
            'screenshot': [SITE + s for s in shots],
            'genre': g['genre'], 'applicationCategory': 'GameApplication',
            'operatingSystem': 'Android, iOS' if g.get('apple') else 'Android',
            'gamePlatform': ['Android', 'iOS'] if g.get('apple') else ['Android'],
            'playMode': 'SinglePlayer',
            'offers': {'@type': 'Offer', 'price': g['price'], 'priceCurrency': 'USD'},
            'author': {'@id': SITE + '/#org'}, 'publisher': {'@id': SITE + '/#org'},
            'installUrl': stores_[0], 'sameAs': stores_ + ([g['community']] if g.get('community') else []),
        })
        graph.append(org)
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'HanX Games', 'item': home},
            {'@type': 'ListItem', 'position': 2, 'name': g['name'], 'item': url}]})
        faq = re.findall(r'<summary>(.*?)</summary><div class="faq__a">(.*?)</div>', html, flags=re.S)
        if faq:
            graph.append({'@type': 'FAQPage', 'mainEntity': [
                {'@type': 'Question', 'name': plain(q), 'acceptedAnswer': {'@type': 'Answer', 'text': plain(a)}} for q, a in faq]})
    return ld({'@context': 'https://schema.org', '@graph': graph}) if graph else ''


def not_found_script():
    data = {c: list(MODULES[c].NOT_FOUND) for c in OTHER}
    codes = '|'.join(OTHER) or 'xx'
    return ('<script>\n  /* One 404 page serves every path; switch language under /<code>/. */\n'
            '  (function () {\n'
            '    var T = %s;\n'
            '    var m = location.pathname.match(/^\\/(%s)(\\/|$)/); if (!m) return;\n'
            '    var c = m[1], t = T[c]; document.documentElement.lang = c; document.title = t[0];\n'
            "    document.querySelector('.lost p').textContent = t[1];\n"
            "    var b = document.querySelector('.lost .btn'); b.textContent = t[2]; b.href = '/' + c + '/';\n"
            "    document.querySelectorAll('.nav a[href^=\"/\"], .footer a[href^=\"/\"]').forEach(function (a) {\n"
            "      var h = a.getAttribute('href'); if (!/^\\/(%s|assets)\\//.test(h)) a.setAttribute('href', '/' + c + h);\n"
            '    });\n  })();\n</script>') % (json.dumps(data, ensure_ascii=False), codes, codes)


def block(html, name, content):
    return re.sub(r'<!-- @%s -->.*?<!-- /@%s -->' % (name, name),
                  lambda m: '<!-- @%s -->\n%s\n<!-- /@%s -->' % (name, content, name), html, flags=re.S)


def page_path(rel):
    d = os.path.dirname(rel).replace(os.sep, '/')
    return '/' if d in ('', '.') else '/' + d + '/'


def write_if_changed(path, html):
    old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
    if html != old:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w', encoding='utf-8', newline='\n').write(html)
        print('updated', os.path.relpath(path, ROOT))


INTERNAL = re.compile(r'href="/(?!assets/|(?:%s)/|favicon|apple-touch-icon)' % '|'.join(LANG_INFO))


def translate(html, rel, here, lang):
    """English page (already synced) -> page in `lang`."""
    mod = MODULES[lang]
    missing = []
    for en, tx in mod.PAGES.get(rel.replace(os.sep, '/'), []):
        if en not in html:
            missing.append(en)
        html = html.replace(en, tx)
    for en, tx in mod.COMMON:  # shared strings; not every page has all of them
        html = html.replace(en, tx)
    html = html.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    html = re.sub(r'<!-- @stores([^>]*?)-->.*?<!-- /@stores -->',
                  lambda m: '<!-- @stores' + m.group(1) + '-->\n' + stores(m.group(1), lang) + '\n<!-- /@stores -->', html, flags=re.S)
    html = INTERNAL.sub(f'href="/{lang}/', html)  # internal links -> same language; assets are shared
    html = re.sub(r'(rel="canonical" href="%s/)' % re.escape(SITE), rf'\g<1>{lang}/', html)
    html = re.sub(r'(property="og:url" content="%s/)' % re.escape(SITE), rf'\g<1>{lang}/', html)
    html = block(html, 'lang', lang_menu(here, lang))
    html = block(html, 'head', head_block(here, lang))
    html = block(html, 'schema', schema(html, here, lang))
    return html, missing


def sitemap(paths):
    rows = []
    for here in sorted(paths, key=lambda p: (p != '/', p)):
        alts = ''.join(f'<xhtml:link rel="alternate" hreflang="{c}" href="{SITE}{lang_url(here, c)}"/>' for c in LANGS)
        for c in LANGS:
            rows.append(f'  <url><loc>{SITE}{lang_url(here, c)}</loc>{alts}</url>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + '\n'.join(rows) + '\n</urlset>\n')


def main():
    build = [ONLY] if ONLY else OTHER
    problems, paths = 0, []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in ('.git', 'partials', 'tools', 'assets', 'node_modules') and d not in LANG_INFO]
        for f in fn:
            if not f.endswith('.html'):
                continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT)
            html = open(p, encoding='utf-8').read()
            here = page_path(rel)
            nav = NAV.replace(f'<a href="{here}">', f'<a href="{here}" aria-current="page">') if here != '/' else NAV
            html = block(html, 'nav', nav)
            html = block(html, 'lang', lang_menu(here, 'en'))
            html = block(html, 'footer', FOOTER)
            html = block(html, 'head', head_block(here, 'en'))
            html = re.sub(r'<!-- @stores([^>]*?)-->.*?<!-- /@stores -->',
                          lambda m: '<!-- @stores' + m.group(1) + '-->\n' + stores(m.group(1)) + '\n<!-- /@stores -->', html, flags=re.S)
            html = block(html, 'more', more(here))
            html = block(html, 'schema', schema(html, here, 'en'))
            html = block(html, '404i18n', not_found_script())
            write_if_changed(p, html)
            if f == '404.html':
                continue  # GitHub Pages serves one 404 for every path; it localises itself in JS.
            paths.append(here)
            for lang in build:
                out, missing = translate(html, rel, here, lang)
                for m in missing:
                    problems += 1
                    print(f'  ! [{lang}] {rel}: no match for {m[:70]!r}')
                write_if_changed(os.path.join(ROOT, lang, rel), out)
    write_if_changed(os.path.join(ROOT, 'sitemap.xml'), sitemap(paths))
    if problems:
        print(f'{problems} translation string(s) did not match; fix tools/i18n/*.py')
        sys.exit(1)


if __name__ == '__main__':
    main()
