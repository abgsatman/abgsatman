import os
import math
import requests

USERNAME = os.environ.get('GH_USERNAME', 'abgsatman')
TOKEN    = os.environ.get('GH_TOKEN', '')
HEADERS  = {'Authorization': f'token {TOKEN}'} if TOKEN else {}

LANG_COLORS = {
    'JavaScript':      '#f1e05a',
    'TypeScript':      '#3178c6',
    'Python':          '#3572A5',
    'Java':            '#b07219',
    'C#':              '#178600',
    'C++':             '#f34b7d',
    'C':               '#555555',
    'Go':              '#00ADD8',
    'Rust':            '#dea584',
    'Ruby':            '#701516',
    'PHP':             '#4F5D95',
    'Swift':           '#F05138',
    'Kotlin':          '#A97BFF',
    'Dart':            '#00B4AB',
    'Shell':           '#89e051',
    'HTML':            '#e34c26',
    'CSS':             '#563d7c',
    'Vue':             '#41b883',
    'Svelte':          '#ff3e00',
    'Scala':           '#c22d40',
    'R':               '#198CE7',
    'Haskell':         '#5e5086',
    'Lua':             '#000080',
    'Elixir':          '#6e4a7e',
    'MATLAB':          '#e16737',
    'Jupyter Notebook':'#DA5B0B',
    'Makefile':        '#427819',
    'Dockerfile':      '#384d54',
}

def get_color(lang, index):
    if lang in LANG_COLORS:
        return LANG_COLORS[lang]
    h = (index * 137.508) % 360
    s, l = 60, 55
    s /= 100; l /= 100
    a = s * min(l, 1 - l)
    k = lambda n: (n + h / 30) % 12
    f = lambda n: l - a * max(-1, min(k(n) - 3, min(9 - k(n), 1)))
    r, g, b = int(255*f(0)), int(255*f(8)), int(255*f(4))
    return f'#{r:02x}{g:02x}{b:02x}'

def fmt_bytes(b):
    if b >= 1_000_000: return f'{b/1_000_000:.1f} MB'
    if b >= 1_000:     return f'{b/1_000:.1f} KB'
    return f'{b} B'

def fetch_all_repos():
    repos, page = [], 1
    while True:
        r = requests.get(
            f'https://api.github.com/users/{USERNAME}/repos'
            f'?per_page=100&page={page}&type=all',
            headers=HEADERS
        )
        data = r.json()
        if not isinstance(data, list) or not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos

def fetch_langs(owner, repo):
    r = requests.get(
        f'https://api.github.com/repos/{owner}/{repo}/languages',
        headers=HEADERS
    )
    return r.json() if r.ok else {}

def donut_path(cx, cy, r_out, r_in, a_start, a_end):
    large = 1 if (a_end - a_start) > math.pi else 0
    x1  = cx + r_out * math.cos(a_start)
    y1  = cy + r_out * math.sin(a_start)
    x2  = cx + r_out * math.cos(a_end)
    y2  = cy + r_out * math.sin(a_end)
    ix1 = cx + r_in  * math.cos(a_end)
    iy1 = cy + r_in  * math.sin(a_end)
    ix2 = cx + r_in  * math.cos(a_start)
    iy2 = cy + r_in  * math.sin(a_start)
    return (f'M {x1:.2f} {y1:.2f} '
            f'A {r_out} {r_out} 0 {large} 1 {x2:.2f} {y2:.2f} '
            f'L {ix1:.2f} {iy1:.2f} '
            f'A {r_in} {r_in} 0 {large} 0 {ix2:.2f} {iy2:.2f} Z')

def generate_svg(sorted_langs, total):
    TOP = 8
    top = list(sorted_langs[:TOP])
    rest = sorted_langs[TOP:]
    colors = [get_color(lang, i) for i, (lang, _) in enumerate(top)]
    if rest:
        top.append(('Other', sum(b for _, b in rest)))
        colors.append('#8b949e')

    W, H = 495, 220
    cx, cy = 105, 115
    r_out, r_in = 82, 52

    # --- donut segments ---
    segments = []
    angle = -math.pi / 2
    for i, (_, b) in enumerate(top):
        sweep = 2 * math.pi * b / total
        d = donut_path(cx, cy, r_out, r_in, angle, angle + sweep)
        segments.append(
            f'<path d="{d}" fill="{colors[i]}" '
            f'stroke="#161b22" stroke-width="2.5"/>'
        )
        angle += sweep

    # centre text
    centre = (
        f'<text x="{cx}" y="{cy - 6}" text-anchor="middle" '
        f'font-family="system-ui,sans-serif" font-size="12" fill="#8b949e">total</text>'
        f'<text x="{cx}" y="{cy + 12}" text-anchor="middle" '
        f'font-family="system-ui,sans-serif" font-size="13" '
        f'font-weight="600" fill="#e6edf3">{fmt_bytes(total)}</text>'
    )

    # --- legend (2 columns, up to 5 rows) ---
    lx, ly0 = 215, 30
    col_w   = 140
    row_h   = 36
    items   = []
    for i, (lang, b) in enumerate(top):
        col = i // 5
        row = i % 5
        x   = lx + col * col_w
        y   = ly0 + row * row_h
        pct = b / total * 100
        items.append(
            f'<circle cx="{x+6}" cy="{y+6}" r="6" fill="{colors[i]}"/>'
            f'<text x="{x+18}" y="{y+9}" '
            f'font-family="system-ui,sans-serif" font-size="13" fill="#e6edf3">'
            f'{lang}</text>'
            f'<text x="{x+18}" y="{y+24}" '
            f'font-family="system-ui,sans-serif" font-size="11" fill="#8b949e">'
            f'{pct:.1f}%  ·  {fmt_bytes(b)}</text>'
        )

    title = (
        f'<text x="{W//2}" y="17" text-anchor="middle" '
        f'font-family="system-ui,sans-serif" font-size="14" '
        f'font-weight="600" fill="#58a6ff">Most Used Languages</text>'
    )

    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{W}" height="{H}" rx="10" '
        f'fill="#161b22" stroke="#30363d" stroke-width="1"/>'
        f'{title}'
        f'{"".join(segments)}'
        f'{centre}'
        f'{"".join(items)}'
        f'</svg>'
    )

def main():
    print(f'Fetching repos for {USERNAME}...')
    repos = fetch_all_repos()
    print(f'  {len(repos)} repos found')

    totals = {}
    for i, repo in enumerate(repos):
        name = repo['name']
        print(f'  [{i+1}/{len(repos)}] {name}')
        for lang, b in fetch_langs(repo['owner']['login'], name).items():
            totals[lang] = totals.get(lang, 0) + b

    sorted_langs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    total = sum(b for _, b in sorted_langs)

    print(f'\n{len(sorted_langs)} languages, {fmt_bytes(total)} total')
    for lang, b in sorted_langs[:10]:
        print(f'  {lang:20s} {b/total*100:5.1f}%')

    os.makedirs('assets', exist_ok=True)
    svg = generate_svg(sorted_langs, total)
    with open('assets/langs.svg', 'w', encoding='utf-8') as f:
        f.write(svg)
    print('\nSaved → assets/langs.svg')

if __name__ == '__main__':
    main()
