#!/usr/bin/env python3
"""
Neural contribution graph.
Fetches the user's contribution calendar from GitHub and renders an animated SVG:
assemble -> scan -> neural links -> dissolve -> loop.

Env: GITHUB_TOKEN (required in Actions), GH_USER (default Ali-shaiikh), OUT (default assets/contrib.svg)
Run with DEMO=1 to render with fake data (no network).
"""
import json, math, os, random, urllib.request
from datetime import date, timedelta

USER = os.getenv("GH_USER", "Ali-shaiikh")
OUT = os.getenv("OUT", "assets/contrib.svg")
FONT = "Inter,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
PALETTE = ["#161b22", "#3b2a6b", "#5b3fb0", "#8b5cf6", "#67e8f9"]
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

# ---------- timeline (seconds within one loop) ----------
LOOP = 15.0
ASSEMBLE = 0.0      # 0 - 2.8
SCAN = 3.0          # 3.0 - 6.2
SCAN_DUR = 3.2
NEURAL = 6.6        # 6.6 - 11
DISSOLVE = 12.0     # 12 - 14.2


def fetch():
    q = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
      totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"], LEVELS[d["contributionLevel"]]) for d in w["contributionDays"]] for w in cal["weeks"]]
    return cal["totalContributions"], weeks


def demo():
    random.seed(3)
    start = date.today() - timedelta(days=364 + date.today().isoweekday() % 7)
    weeks, total = [], 0
    for w in range(53):
        days = []
        for d in range(7):
            day = start + timedelta(days=w * 7 + d)
            if day > date.today():
                break
            c = 0 if random.random() < .35 else int(random.expovariate(1 / 6))
            lvl = 0 if c == 0 else min(4, 1 + c // 4)
            total += c
            days.append((day.isoformat(), c, lvl))
        weeks.append(days)
    return total, weeks


def t(sec):
    return f"clock.begin+{sec:.3f}s"


def render(total, weeks):
    random.seed(11)
    CELL, GAP = 13, 4
    STEP = CELL + GAP
    W = 1000
    gx = (W - len(weeks) * STEP + GAP) / 2
    gy = 106
    H = gy + 7 * STEP + 58
    cx0, cy0 = W / 2, gy + 3.5 * STEP

    cells, active = [], []
    month_labels, last_month = [], None
    for wi, week in enumerate(weeks):
        for di, (ds, count, lvl) in enumerate(week):
            x, y = gx + wi * STEP, gy + di * STEP
            cells.append((wi, di, x, y, ds, count, lvl))
            if lvl >= 2:
                active.append((wi, di, x, y, lvl))
            m = ds[5:7]
            if di == 0 and m != last_month:
                last_month = m
                if wi < len(weeks) - 2:
                    month_labels.append((x, ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][int(m) - 1]))

    out = []
    a = out.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    a(f'''<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#070a12"/><stop offset=".6" stop-color="#0b0f1e"/><stop offset="1" stop-color="#08141f"/></linearGradient>
  <linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="#67e8f9" stop-opacity="0"/><stop offset=".85" stop-color="#67e8f9" stop-opacity=".35"/><stop offset="1" stop-color="#ffffff" stop-opacity=".95"/></linearGradient>
  <radialGradient id="blobA"><stop offset="0" stop-color="#6d28d9" stop-opacity=".3"/><stop offset="1" stop-color="#6d28d9" stop-opacity="0"/></radialGradient>
  <radialGradient id="blobB"><stop offset="0" stop-color="#0891b2" stop-opacity=".25"/><stop offset="1" stop-color="#0891b2" stop-opacity="0"/></radialGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <clipPath id="clip"><rect width="{W}" height="{H}" rx="16"/></clipPath>
</defs>''')
    # master clock
    a(f'<rect width="0" height="0"><animate id="clock" attributeName="x" from="0" to="0" dur="{LOOP}s" begin="0s;clock.end"/></rect>')
    a('<g clip-path="url(#clip)">')
    a(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    a(f'<circle cx="{W*.2}" cy="{H*.3}" r="220" fill="url(#blobA)"><animate attributeName="cx" values="{W*.2};{W*.35};{W*.2}" dur="18s" repeatCount="indefinite"/></circle>')
    a(f'<circle cx="{W*.82}" cy="{H*.7}" r="230" fill="url(#blobB)"><animate attributeName="cx" values="{W*.82};{W*.65};{W*.82}" dur="15s" repeatCount="indefinite"/></circle>')

    # header
    a(f'<text x="{gx}" y="44" font-family="{FONT}" font-size="22" font-weight="700" fill="#f0f6fc">{total:,} contributions</text>')
    a(f'<text x="{gx}" y="66" font-family="{MONO}" font-size="12" letter-spacing="1.5" fill="#8b949e">IN THE LAST YEAR  ·  @{USER}</text>')
    # phase label (top right)
    phases = [("ASSEMBLING", ASSEMBLE, SCAN), ("SCANNING", SCAN, NEURAL), ("NEURAL MODE", NEURAL, DISSOLVE), ("RESETTING", DISSOLVE, LOOP)]
    for label, s, e in phases:
        a(f'<text x="{W-gx}" y="44" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="2" fill="#67e8f9" opacity="0">{label}'
          f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.08;.9;1" dur="{e-s}s" begin="{t(s)}"/></text>')
    a(f'<circle cx="{W-gx+10}" cy="40" r="3.5" fill="#67e8f9"><animate attributeName="opacity" values="1;.2;1" dur="1.2s" repeatCount="indefinite"/></circle>')

    for x, name in month_labels:
        a(f'<text x="{x}" y="{gy-10}" font-family="{FONT}" font-size="11" fill="#6e7681">{name}</text>')

    # ---------- cells ----------
    a('<g>')
    for wi, di, x, y, ds, count, lvl in cells:
        col = PALETTE[lvl]
        ang = random.uniform(0, 2 * math.pi)
        rad = random.uniform(160, 420)
        sx = cx0 + math.cos(ang) * rad - x
        sy = cy0 + math.sin(ang) * rad * .45 - y
        delay = wi * .028 + random.uniform(0, .5)
        fly = 1.1
        T1 = delay + fly
        k = delay / T1
        h = CELL / 2
        a(f'<g transform="translate({x+h:.1f},{y+h:.1f})"><g opacity="0">')
        # assemble: hold scattered, then fly in
        a(f'<animateTransform attributeName="transform" type="translate" values="{sx:.0f} {sy:.0f};{sx:.0f} {sy:.0f};0 0" keyTimes="0;{k:.3f};1" '
          f'calcMode="spline" keySplines="0 0 1 1;.2 .8 .2 1" dur="{T1:.2f}s" begin="{t(ASSEMBLE)}" fill="freeze"/>')
        a(f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{k:.3f};1" dur="{T1:.2f}s" begin="{t(ASSEMBLE)}" fill="freeze"/>')
        # dissolve: float up and fade
        dd = DISSOLVE + wi * .025 + random.uniform(0, .4)
        a(f'<animateTransform attributeName="transform" type="translate" values="0 0;{random.uniform(-6,6):.0f} {-random.uniform(25,60):.0f}" '
          f'dur="1.4s" begin="{t(dd)}" fill="freeze" calcMode="spline" keySplines=".5 0 .8 .4"/>')
        a(f'<animate attributeName="opacity" values="1;0" dur="1.4s" begin="{t(dd)}" fill="freeze"/>')
        a(f'<rect x="{-h}" y="{-h}" width="{CELL}" height="{CELL}" rx="3" fill="{col}">')
        a(f'<title>{ds}: {count} contributions</title>')
        if lvl > 0:
            ts = SCAN + (x - gx) / (len(weeks) * STEP) * SCAN_DUR
            a(f'<animate attributeName="fill" values="{col};#ffffff;{col}" dur=".7s" begin="{t(ts)}"/>')
            a(f'<animateTransform attributeName="transform" type="scale" values="1;1.55;1" dur=".6s" begin="{t(ts)}"/>')
        a('</rect>')
        if lvl >= 3:
            ts = SCAN + (x - gx) / (len(weeks) * STEP) * SCAN_DUR
            a(f'<circle r="2" fill="none" stroke="{PALETTE[4]}" stroke-width="1.2" opacity="0">'
              f'<animate attributeName="r" values="2;22" dur="1s" begin="{t(ts)}"/>'
              f'<animate attributeName="opacity" values=".9;0" dur="1s" begin="{t(ts)}"/></circle>')
        a('</g></g>')
    a('</g>')

    # ---------- scan beam ----------
    a(f'<rect x="{gx-60}" y="{gy-6}" width="60" height="{7*STEP+8}" fill="url(#beam)" opacity="0">'
      f'<animate attributeName="x" values="{gx-60};{gx+len(weeks)*STEP-50}" dur="{SCAN_DUR}s" begin="{t(SCAN)}"/>'
      f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.05;.92;1" dur="{SCAN_DUR}s" begin="{t(SCAN)}"/></rect>')

    # ---------- neural links ----------
    random.seed(5)
    links, used = [], set()
    pool = active[:]
    random.shuffle(pool)
    for p in pool:
        near = [q for q in active if q is not p and 1 <= abs(q[0] - p[0]) <= 5 and (p, q) not in used]
        if not near:
            continue
        q = random.choice(near)
        used.add((q, p))
        links.append((p, q))
        if len(links) >= 42:
            break
    a('<g filter="url(#glow)">')
    for i, (p, q) in enumerate(links):
        x1, y1 = p[2] + CELL / 2, p[3] + CELL / 2
        x2, y2 = q[2] + CELL / 2, q[3] + CELL / 2
        mx, my = (x1 + x2) / 2, min(y1, y2) - random.uniform(12, 34)
        d = f"M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}"
        L = math.dist((x1, y1), (mx, my)) + math.dist((mx, my), (x2, y2))
        st = NEURAL + i * .06
        span = DISSOLVE - st
        color = PALETTE[4] if i % 3 else PALETTE[3]
        a(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.1" stroke-linecap="round" stroke-dasharray="{L:.0f}" stroke-dashoffset="{L:.0f}" opacity="0">'
          f'<animate attributeName="stroke-dashoffset" values="{L:.0f};0;0" keyTimes="0;{.6/span:.3f};1" dur="{span:.2f}s" begin="{t(st)}"/>'
          f'<animate attributeName="opacity" values="0;.85;.85;0" keyTimes="0;.05;.85;1" dur="{span:.2f}s" begin="{t(st)}"/></path>')
        # signal pulse
        bs = ";".join(t(st + .8 + k * 1.6) for k in range(3) if st + .8 + k * 1.6 + 1.1 < DISSOLVE - .3)
        if bs:
            a(f'<circle r="2.2" fill="#ffffff" opacity="0">'
              f'<animateMotion path="{d}" dur="1.1s" begin="{bs}"/>'
              f'<animate attributeName="opacity" values="0;1;1;0" dur="1.1s" begin="{bs}"/></circle>')
    a('</g>')
    # glow on linked nodes during neural phase
    nodes = {(p[0], p[1]): p for pair in links for p in pair}
    for wi, di, x, y, lvl in nodes.values():
        a(f'<rect x="{x-2}" y="{y-2}" width="{CELL+4}" height="{CELL+4}" rx="4" fill="none" stroke="#67e8f9" stroke-width="1" opacity="0">'
          f'<animate attributeName="opacity" values="0;.9;.4;.9;0" dur="{DISSOLVE-NEURAL:.1f}s" begin="{t(NEURAL)}"/></rect>')

    # legend
    ly = gy + 7 * STEP + 26
    lx = W - gx - 5 * (CELL + 4) - 70
    a(f'<text x="{lx-8}" y="{ly+10}" text-anchor="end" font-family="{FONT}" font-size="11" fill="#6e7681">Less</text>')
    for i, c in enumerate(PALETTE):
        a(f'<rect x="{lx + i*(CELL+4)}" y="{ly}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>')
    a(f'<text x="{lx + 5*(CELL+4) + 4}" y="{ly+10}" font-family="{FONT}" font-size="11" fill="#6e7681">More</text>')
    a(f'<text x="{gx}" y="{ly+10}" font-family="{MONO}" font-size="11" fill="#6e7681">neural contribution graph · updated {date.today():%d %b %Y}</text>')

    a('</g>')
    a(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="#a78bfa" stroke-opacity=".25"/>')
    a('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    total, weeks = demo() if os.getenv("DEMO") == "1" else fetch()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    open(OUT, "w").write(render(total, weeks))
    print(f"wrote {OUT}: {total} contributions, {sum(len(w) for w in weeks)} days")
