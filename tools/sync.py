"""Builds the site: injects shared partials into the English pages, then
generates the Turkish pages under /tr/ from them.

Run from the repo root after editing any page, partial or translation:
    python tools/sync.py

English pages are the source. Never edit files under tr/ by hand: they are
overwritten on every run. Turkish text lives in tools/tr.py.

Markers inside English pages:
    <!-- @head --><!-- /@head -->       hreflang links (+ Turkish auto-redirect)
    <!-- @nav --><!-- /@nav -->
    <!-- @footer --><!-- /@footer -->
    <!-- @stores gp="com.package" apple="123456" --><!-- /@stores -->
    <!-- @more --><!-- /@more -->       links to the other game pages
The nav partial contains <!-- @lang --><!-- /@lang --> for the EN | TR switch.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://hanxgames.net'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tr as TR  # noqa: E402

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
BADGE_TEXT = {'en': (('Get it on', 'Google Play'), ('Download on the', 'App Store')),
              'tr': (('Hemen indir', 'Google Play'), ('Hemen indir', 'App Store'))}


def stores(attrs, lang='en'):
    a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
    (gs, gb), (as_, ab) = BADGE_TEXT[lang]
    out = []
    if a.get('gp'):
        url = a['gp'] if a['gp'].startswith('http') else 'https://play.google.com/store/apps/details?id=' + a['gp']
        out.append(f'<a class="store" href="{url}" target="_blank" rel="noopener">{GP_SVG}<span><small>{gs}</small><b>{gb}</b></span></a>')
    if a.get('apple'):
        url = a['apple'] if a['apple'].startswith('http') else 'https://apps.apple.com/app/id' + a['apple']
        out.append(f'<a class="store" href="{url}" target="_blank" rel="noopener">{APPLE_SVG}<span><small>{as_}</small><b>{ab}</b></span></a>')
    return '\n'.join(out)


GAMES = re.findall(r'<a href="(/[^"]+/)"><img src="([^"]+)"[^>]*>([^<]+)</a>', NAV)


def more(here):
    items = [f'<a href="{h}"><img src="{i}" alt="" loading="lazy">{n}</a>' for h, i, n in GAMES if h != here]
    return '<div class="more-games">\n' + '\n'.join(items) + '\n</div>'


def lang_switch(here, active):
    tr_path = '/tr' + here
    cur = lambda l: ' aria-current="true"' if l == active else ''
    return (f'<div class="lang" role="group" aria-label="{"Dil" if active == "tr" else "Language"}">'
            f'<a href="{here}" hreflang="en" lang="en"{cur("en")}>EN</a>'
            f'<a href="{tr_path}" hreflang="tr" lang="tr"{cur("tr")}>TR</a></div>')


def head_block(here, lang):
    out = [f'<link rel="alternate" hreflang="en" href="{SITE}{here}">',
           f'<link rel="alternate" hreflang="tr" href="{SITE}/tr{here}">',
           f'<link rel="alternate" hreflang="x-default" href="{SITE}{here}">',
           f'<meta property="og:locale" content="{"tr_TR" if lang == "tr" else "en_US"}">']
    if lang == 'en':
        # First visit from a Turkish browser goes to the Turkish page; the EN | TR switch stores a preference.
        out.append("<script>try{if(!localStorage.getItem('hx-lang')&&/^tr\\b/i.test(navigator.language||''))"
                   "location.replace('/tr'+location.pathname+location.hash)}catch(e){}</script>")
    return '\n  '.join(out)


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


def to_turkish(html, rel, here):
    """English page (already synced) -> Turkish page."""
    missing = []
    for en, tr in TR.PAGES.get(rel.replace(os.sep, '/'), []):
        if en not in html:
            missing.append(en)
        html = html.replace(en, tr)
    for en, tr in TR.COMMON:  # shared strings; not every page has all of them
        html = html.replace(en, tr)
    html = html.replace('<html lang="en">', '<html lang="tr">', 1)
    html = re.sub(r'<!-- @stores([^>]*?)-->.*?<!-- /@stores -->',
                  lambda m: '<!-- @stores' + m.group(1) + '-->\n' + stores(m.group(1), 'tr') + '\n<!-- /@stores -->', html, flags=re.S)
    # Internal links point at the Turkish copies; assets are shared.
    html = re.sub(r'href="/(?!assets/|tr/|favicon|apple-touch-icon)', 'href="/tr/', html)
    html = re.sub(r'(rel="canonical" href="%s/)' % re.escape(SITE), r'\1tr/', html)
    html = re.sub(r'(property="og:url" content="%s/)' % re.escape(SITE), r'\1tr/', html)
    html = block(html, 'lang', lang_switch(here, 'tr'))
    html = block(html, 'head', head_block(here, 'tr'))
    return html, missing


def sitemap(paths):
    rows = []
    for here in sorted(paths, key=lambda p: (p != '/', p)):
        for loc in (here, '/tr' + here):
            rows.append(f'  <url><loc>{SITE}{loc}</loc>'
                        f'<xhtml:link rel="alternate" hreflang="en" href="{SITE}{here}"/>'
                        f'<xhtml:link rel="alternate" hreflang="tr" href="{SITE}/tr{here}"/></url>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + '\n'.join(rows) + '\n</urlset>\n')


def main():
    problems = 0
    paths = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in ('.git', 'partials', 'tools', 'assets', 'node_modules', 'tr')]
        for f in fn:
            if not f.endswith('.html'):
                continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT)
            html = open(p, encoding='utf-8').read()
            here = page_path(rel)
            nav = NAV.replace(f'<a href="{here}">', f'<a href="{here}" aria-current="page">') if here != '/' else NAV
            html = block(html, 'nav', nav)
            html = block(html, 'lang', lang_switch(here, 'en'))
            html = block(html, 'footer', FOOTER)
            html = block(html, 'head', head_block(here, 'en'))
            html = re.sub(r'<!-- @stores([^>]*?)-->.*?<!-- /@stores -->',
                          lambda m: '<!-- @stores' + m.group(1) + '-->\n' + stores(m.group(1)) + '\n<!-- /@stores -->', html, flags=re.S)
            html = block(html, 'more', more(here))
            write_if_changed(p, html)
            if f == '404.html':
                continue  # GitHub Pages serves one 404 for every path; it localises itself in JS.
            paths.append(here)
            tr_html, missing = to_turkish(html, rel, here)
            for m in missing:
                problems += 1
                print(f'  ! {rel}: no match for {m[:70]!r}')
            write_if_changed(os.path.join(ROOT, 'tr', rel), tr_html)
    write_if_changed(os.path.join(ROOT, 'sitemap.xml'), sitemap(paths))
    if problems:
        print(f'{problems} translation string(s) did not match; fix tools/tr.py')
        sys.exit(1)


if __name__ == '__main__':
    main()
