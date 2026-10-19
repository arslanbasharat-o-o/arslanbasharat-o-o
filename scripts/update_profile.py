#!/usr/bin/env python3
"""Generate self-contained SVGs from GitHub's public calendar; stdlib only."""
import argparse
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "arslanbasharat-o-o"
THEMES = {
    "dark": dict(bg="#0d1117", border="#303d48", text="#f0f4f8", muted="#9eafbf", accent="#78dbad",
                 ramp=["#1b2732", "#214d40", "#317658", "#4aa77a", "#78dbad"]),
    "light": dict(bg="#f6f8fa", border="#ccd5de", text="#172a3a", muted="#526579", accent="#14734b",
                  ramp=["#e5ebf0", "#c5e4d1", "#86c7a3", "#43a372", "#14734b"]),
}


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.tips = {}, {}
        self.tip_id, self.tip_text = None, []
        self.in_total, self.total_text = False, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and "data-date" in a:
            self.cells[a["id"]] = {"date": a["data-date"], "level": int(a["data-level"])}
        if tag == "tool-tip" and a.get("for", "").startswith("contribution-day-"):
            self.tip_id, self.tip_text = a["for"], []
        if tag == "h2" and a.get("id") == "js-contribution-activity-description":
            self.in_total = True

    def handle_data(self, text):
        if self.tip_id:
            self.tip_text.append(text)
        if self.in_total:
            self.total_text.append(text)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tip_id:
            self.tips[self.tip_id] = "".join(self.tip_text).strip()
            self.tip_id = None
        if tag == "h2":
            self.in_total = False

    def calendar(self):
        days = []
        for cell_id, cell in self.cells.items():
            match = re.match(r"(No|[\d,]+) contributions? on ", self.tips.get(cell_id, ""))
            if not match:
                raise ValueError(f"Missing or invalid contribution count for {cell['date']}")
            count = 0 if match[1] == "No" else int(match[1].replace(",", ""))
            date.fromisoformat(cell["date"])
            if cell["level"] not in range(5) or (count == 0) != (cell["level"] == 0):
                raise ValueError("Invalid contribution intensity")
            days.append({**cell, "count": count})
        days.sort(key=lambda d: d["date"])
        if not 365 <= len(days) <= 371:
            raise ValueError(f"Expected a full contribution year, got {len(days)} days")
        for previous, current in zip(days, days[1:]):
            if date.fromisoformat(current["date"]) - date.fromisoformat(previous["date"]) != timedelta(days=1):
                raise ValueError("Contribution dates are duplicated or incomplete")
        match = re.search(r"([\d,]+)\s+contributions?", " ".join(self.total_text))
        if not match:
            raise ValueError("Missing yearly contribution total")
        return {"username": USERNAME, "as_of": days[-1]["date"], "total": int(match[1].replace(",", "")),
                "daily_total": sum(d["count"] for d in days), "days": days}


def fetch_calendar():
    req = Request(f"https://github.com/users/{USERNAME}/contributions",
                  headers={"User-Agent": f"{USERNAME}-profile/1.0", "Accept-Language": "en-US"})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=30) as response:
                html = response.read().decode("utf-8")
            parser = CalendarParser()
            parser.feed(html)
            result = parser.calendar()
            age = (datetime.now(timezone.utc).date() - date.fromisoformat(result["as_of"])).days
            if not 0 <= age <= 1:
                raise ValueError("GitHub returned a stale contribution calendar")
            return result
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def text(x, y, value, size=14, fill="text", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{fill}" {extra}>{escape(str(value))}</text>'


def frame(w, h, title, desc, p, content):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace}}
.text{{fill:{p['text']}}}.muted{{fill:{p['muted']}}}.accent{{fill:{p['accent']}}}
.cursor{{animation:blink 1.2s steps(2,jump-none) infinite}}
.ink{{animation:ink 6s cubic-bezier(.77,0,.175,1) infinite}}
.scan{{animation:scan 6s linear infinite}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:.15}}}}
@keyframes ink{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
@keyframes scan{{from{{transform:translateX(0)}}to{{transform:translateX({w+80}px)}}}}
@media(prefers-reduced-motion:reduce){{.cursor,.ink,.scan{{animation:none}}.scan{{display:none}}}}
</style>
<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="14" fill="{p['bg']}" stroke="{p['border']}"/>
{content}
<rect class="scan" x="-80" y="{h-3}" width="80" height="2" rx="1" fill="{p['accent']}" opacity=".7"/>
</svg>\n'''


def intro(p, mobile=False):
    w, h = (480, 420) if mobile else (900, 334)
    bits = [text(28, 33, "arslan@github ~ $ whoami", 12, "muted"),
            f'<rect class="cursor" x="201" y="23" width="7" height="12" fill="{p["accent"]}"/>',
            f'<path d="M 0 52 H {w}" stroke="{p["border"]}"/>']
    art = ["    /\\     |====\\ ", "   /  \\    |     |", "  / /\\ \\   |====/ ",
           " / /==\\ \\  |     |", "/_/    \\_\\ |====/ "]
    if not mobile:
        bits.append('<g class="ink">')
        for i, row in enumerate(art):
            bits.append(text(30, 130+i*22, row, 19, "accent", 'xml:space="preserve"'))
        bits += [text(30, 278, "BUILD / AUTOMATE / SHIP", 11, "muted"), '</g>',
                 f'<path d="M 300 84 V 282" stroke="{p["border"]}"/>']
    x, y = (28, 99) if mobile else (334, 99)
    bits.append('<g>')
    bits += [text(x, y, "ARSLAN BASHARAT", 13, "accent", 'letter-spacing="2"'),
             text(x, y+49, "Turning daily operations", 27 if mobile else 29, extra='font-weight="700"'),
             text(x, y+86, "into reliable software.", 27 if mobile else 29, extra='font-weight="700"')]
    for i, (key, value) in enumerate([("role", "Automation & full-stack developer"), ("at", "TXParts Enterprise LLC"),
                                     ("focus", "Repair ops / supplier data / APIs")]):
        bits += [text(x, y+130+i*29, key, 14 if mobile else 12, "muted"),
                 text(x+64, y+130+i*29, value, 15 if mobile else 12)]
    bits.append('</g>')
    if mobile:
        bits += [f'<path d="M 28 342 H 452" stroke="{p["border"]}"/>',
                 text(28, 380, "AB  /  BUILD · AUTOMATE · SHIP", 12, "accent")]
    return frame(w, h, "Arslan Basharat | Automation & full-stack development",
                 "Turning daily operations into reliable software. TXParts Enterprise LLC. Repair operations, supplier data, and APIs.", p, "\n".join(bits))


def activity(data, p, mobile=False):
    days = data["days"]
    longest = streak = 0
    for day in days:
        streak = streak+1 if day["count"] else 0
        longest = max(longest, streak)
    active = sum(d["count"] > 0 for d in days)
    start = date.fromisoformat(days[0]["date"])
    start -= timedelta(days=(start.weekday()+1) % 7)
    if mobile:
        end = date.fromisoformat(days[-1]["date"])
        last_sunday = end - timedelta(days=(end.weekday()+1) % 7)
        start = last_sunday - timedelta(weeks=15)
        days = [d for d in days if date.fromisoformat(d["date"]) >= start]
    w, h = (480, 345) if mobile else (900, 290)
    size, gap, left, top = (19, 6, 54, 91) if mobile else (11, 4, 54, 91)
    step = size+gap
    bits = [text(28, 33, "arslan@github ~ $ activity --year", 12, "muted"),
            f'<rect class="cursor" x="265" y="23" width="7" height="12" fill="{p["accent"]}"/>',
            text(w-28, 33, "LAST 16 WEEKS" if mobile else "PAST YEAR", 10, "muted", 'text-anchor="end"')]
    last_month = None
    for day in days:
        dt = date.fromisoformat(day["date"])
        col, row = divmod((dt-start).days, 7)
        x, y = left+col*step, top+row*step
        if dt.month != last_month and row == 0:
            bits.append(text(x, top-12, dt.strftime("%b"), 14 if mobile else 11, "muted"))
            last_month = dt.month
        bits.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="2" fill="{p["ramp"][day["level"]]}"><title>{day["date"]}: {day["count"]} contributions</title></rect>')
    for row, label in [(1, "M"), (3, "W"), (5, "F")]:
        bits.append(text(28, top+row*step+size-1, label, 10, "muted"))
    divider = 284 if mobile else 222
    bits.append(f'<path d="M 28 {divider} H {w-28}" stroke="{p["border"]}"/>')
    for i, (value, label) in enumerate([(f'{data["total"]:,}', "contributions"), (str(active), "active days"), (f"{longest}d", "longest streak")]):
        x = 28+i*((w-56)//3)
        bits += [text(x, divider+27, value, 24 if mobile else 19, "accent", 'font-weight="700"'),
                 text(x, divider+46, label, 14 if mobile else 10, "muted")]
    if not mobile:
        bits.append(text(w-28, 202, f'Updated {data["as_of"]} · GitHub public profile', 10, "muted", 'text-anchor="end"'))
        bits.append(text(54, 202, "Less", 10, "muted"))
        for i, color in enumerate(p["ramp"]):
            bits.append(f'<rect x="{88+i*15}" y="192" width="11" height="11" rx="2" fill="{color}"/>')
        bits.append(text(170, 202, "More", 10, "muted"))
    return frame(w, h, "GitHub contribution activity",
                 f'{data["total"]:,} contributions in the past year; {active} active days; longest streak {longest} days. As of {data["as_of"]}. Mobile grid shows the last 16 weeks.', p, "\n".join(bits))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", type=Path, help="Read a saved public calendar for offline verification")
    args = parser.parse_args()
    if args.html:
        calendar_parser = CalendarParser()
        calendar_parser.feed(args.html.read_text())
        data = calendar_parser.calendar()
    else:
        data = fetch_calendar()
    outputs = {ROOT / "data/contributions.json": json.dumps(data, indent=2)+"\n"}
    for theme, palette in THEMES.items():
        for mobile in [False, True]:
            suffix = f'{theme}{"-mobile" if mobile else ""}.svg'
            outputs[ROOT / f"assets/intro-{suffix}"] = intro(palette, mobile)
            outputs[ROOT / f"assets/activity-{suffix}"] = activity(data, palette, mobile)
    for path, content in outputs.items():
        if path.suffix == ".svg":
            ElementTree.fromstring(content)
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix+".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
    print(f'Generated 8 SVGs: {data["total"]} contributions, through {data["as_of"]}')


if __name__ == "__main__":
    main()
