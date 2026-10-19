"""Injects the shared nav/footer partials and store badges into every page.

Run from the repo root after editing partials/ or adding a page:
    python tools/sync.py

Markers inside pages:
    <!-- @nav --><!-- /@nav -->
    <!-- @footer --><!-- /@footer -->
    <!-- @stores gp="com.package" apple="123456" --><!-- /@stores -->
    <!-- @more --><!-- /@more -->   (links to the other game pages)
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

def stores(attrs):
    a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
    out = []
    if a.get('gp'):
        url = a['gp'] if a['gp'].startswith('http') else 'https://play.google.com/store/apps/details?id=' + a['gp']
        out.append(f'<a class="store" href="{url}" target="_blank" rel="noopener">{GP_SVG}<span><small>Get it on</small><b>Google Play</b></span></a>')
    if a.get('apple'):
        url = a['apple'] if a['apple'].startswith('http') else 'https://apps.apple.com/app/id' + a['apple']
        out.append(f'<a class="store" href="{url}" target="_blank" rel="noopener">{APPLE_SVG}<span><small>Download on the</small><b>App Store</b></span></a>')
    return '\n'.join(out)

GAMES = re.findall(r'<a href="(/[^"]+/)"><img src="([^"]+)"[^>]*>([^<]+)</a>', NAV)

def more(here):
    items = [f'<a href="{h}"><img src="{i}" alt="" loading="lazy">{n}</a>' for h, i, n in GAMES if h != here]
    return '<div class="more-games">\n' + '\n'.join(items) + '\n</div>'

def page_path(rel):
    d = os.path.dirname(rel).replace(os.sep, '/')
    return '/' if d in ('', '.') else '/' + d + '/'

for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in ('.git', 'partials', 'tools', 'assets', 'node_modules')]
    for f in fn:
        if not f.endswith('.html'):
            continue
        p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT)
        html = open(p, encoding='utf-8').read(); orig = html
        here = page_path(rel)
        nav = NAV.replace(f'<a href="{here}">', f'<a href="{here}" aria-current="page">') if here != '/' else NAV
        html = re.sub(r'<!-- @nav -->.*?<!-- /@nav -->', lambda m: '<!-- @nav -->\n' + nav + '\n<!-- /@nav -->', html, flags=re.S)
        html = re.sub(r'<!-- @footer -->.*?<!-- /@footer -->', lambda m: '<!-- @footer -->\n' + FOOTER + '\n<!-- /@footer -->', html, flags=re.S)
        html = re.sub(r'<!-- @stores([^>]*?)-->.*?<!-- /@stores -->',
                      lambda m: '<!-- @stores' + m.group(1) + '-->\n' + stores(m.group(1)) + '\n<!-- /@stores -->', html, flags=re.S)
        html = re.sub(r'<!-- @more -->.*?<!-- /@more -->', lambda m: '<!-- @more -->\n' + more(here) + '\n<!-- /@more -->', html, flags=re.S)
        if html != orig:
            open(p, 'w', encoding='utf-8', newline='\n').write(html)
            print('updated', rel)
