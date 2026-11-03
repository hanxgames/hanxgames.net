"""Draws assets/games/frontaxis/topo.svg, the contour lines behind the Frontaxis hero, from a real
Frontaxis battle map (10 m height grid of the game's Trabzon front, Maçka valley).

    python tools/frontaxis_topo.py C:/gd/frontline/data/maps/r_tr_trabzon/height.bin

The SVG draws itself in (CSS inside the file) and works as a plain <img>.
"""
import struct, sys, zlib, os
import numpy as np
from skimage import measure

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'games', 'frontaxis', 'topo.svg')
W, H = 1600, 1000           # viewBox
STEP = 50                   # metres between contours; every 5th is an index contour
CROP = (0.08, 0.10, 0.80)   # left, top, width of the map window (fractions)


def load(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'FLGR', 'not a Frontaxis grid'
    _, w, h, dx, bpp = struct.unpack('<IIIfI', b[4:24])
    a = np.frombuffer(zlib.decompress(b[24:]), dtype=np.uint16 if bpp == 2 else np.uint8).reshape(h, w)
    return a.astype(np.float32) / 10.0          # stored in decimetres


def main():
    h = load(sys.argv[1])
    gh, gw = h.shape
    x0, y0 = int(gw * CROP[0]), int(gh * CROP[1])
    cw = int(gw * CROP[2]); ch = int(cw * H / W)
    win = h[y0:y0 + ch, x0:x0 + cw]
    lo, hi = np.percentile(win, 1), np.percentile(win, 99.5)
    k = W / cw
    paths, labels = [], []
    first = int(np.ceil(lo / STEP)) * STEP
    for i, lev in enumerate(np.arange(first, hi, STEP)):
        index = (int(lev) // STEP) % 5 == 0
        for c in measure.find_contours(win, lev):
            c = measure.approximate_polygon(c, tolerance=1.6)
            if len(c) < 6:
                continue
            pts = c[:, ::-1] * k
            span = np.ptp(pts, axis=0).max()
            if span < 60:
                continue
            d = 'M' + ' '.join('%.0f %.0f' % (x, y) for x, y in pts)
            cls = 'i' if index else ('a', 'b', 'c')[i % 3]
            paths.append('<path class="%s" pathLength="1" d="%s"/>' % (cls, d))
            if index and span > 360 and len(labels) < 7:
                x, y = pts[len(pts) // 2]
                if 80 < x < W - 80 and 80 < y < H - 80:
                    labels.append('<text x="%.0f" y="%.0f">%d</text>' % (x, y, int(lev)))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid slice">'
           '<style>'
           'path{fill:none;stroke:#f5b342;stroke-opacity:.1;stroke-width:1.1;stroke-linejoin:round;'
           'stroke-dasharray:1;stroke-dashoffset:1;animation:d 4.2s cubic-bezier(.2,.8,.2,1) forwards}'
           '.i{stroke-opacity:.24;stroke-width:1.8;animation-duration:5s}'
           '.b{animation-delay:.35s}.c{animation-delay:.7s}.i{animation-delay:.2s}'
           'text{font:600 15px Barlow,Inter,sans-serif;fill:#f5b342;fill-opacity:0;letter-spacing:.06em;animation:t 1.2s 3.2s forwards}'
           '@keyframes d{to{stroke-dashoffset:0}}@keyframes t{to{fill-opacity:.5}}'
           '@media (prefers-reduced-motion:reduce){path{animation:none;stroke-dashoffset:0}text{animation:none;fill-opacity:.5}}'
           '</style>%s%s</svg>') % (W, H, ''.join(paths), ''.join(labels))
    open(OUT, 'w', encoding='utf-8', newline='\n').write(svg)
    print('%s: %d contours, %d labels, %d KB' % (os.path.relpath(OUT, ROOT), len(paths), len(labels), len(svg) // 1024))


if __name__ == '__main__':
    main()
