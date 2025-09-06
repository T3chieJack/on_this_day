import os, sys, random, requests
from datetime import datetime
from zoneinfo import ZoneInfo  # built-in on Python 3.9+

WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK:
    print("Missing DISCORD_WEBHOOK_URL", file=sys.stderr); sys.exit(1)

# Use London date so it feels local to you
today_london = datetime.now(ZoneInfo("Europe/London"))
month = today_london.month
day = today_london.day

API = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"

def pick_event():
    r = requests.get(API, timeout=15, headers={"User-Agent": "punchline-otd/1.0"})
    r.raise_for_status()
    data = r.json()
    events = data.get("events", [])
    if not events:
        return None

    ev = random.choice(events)

    year = ev.get("year")
    text = ev.get("text", "").strip()

    # Try to pull a nice link + thumbnail from the first related page
    url = None
    thumb = None
    pages = ev.get("pages") or []
    if pages:
        p = pages[0]
        url = ((p.get("content_urls") or {}).get("desktop") or {}).get("page")
        thumb = (p.get("thumbnail") or {}).get("source")

    return {
        "year": year,
        "text": text,
        "url": url,
        "thumb": thumb,
        "month": month,
        "day": day
    }

def post_discord(ev):
    title = f"On this day — {today_london.strftime('%-d %B')}"
    description = f"**{ev['year']}** — {ev['text']}"
    embed = {
        "title": title,
        "description": description[:4000],
        "url": ev["url"] if ev["url"] else None,
    }
    if ev.get("thumb"):
        embed["thumbnail"] = {"url": ev["thumb"]}

    payload = {
        "username": "Punchline • This Day in History",
        "embeds": [embed]
    }

    resp = requests.post(WEBHOOK, json=payload, timeout=15)
    if resp.status_code not in (200, 204):
        print(f"Discord post failed: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

def main():
    ev = pick_event()
    if not ev:
        # Fallback message if Wikipedia returns nothing
        requests.post(WEBHOOK, json={"content": "📜 On this day: no events found."}, timeout=10)
        return
    post_discord(ev)

if __name__ == "__main__":
    main()
