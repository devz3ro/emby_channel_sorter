#!/usr/bin/env python3
import requests, math, time, sys
from urllib.parse import urlencode

# ─── CONFIG ───────────────────────────────────────────────────────────────
SERVER      = "http://localhost:8096/emby"   # "http://host:8096/emby" or "https://host:8920/emby"
API_KEY     = "YOUR_ADMIN_API_KEY"           # Dashboard ▸ Advanced ▸ API Keys
PAUSE_MS    = 25          # delay between POSTs (ms) – raise on slow servers
MAX_PASSES  = 15          # stop after this many attempts even if not perfect
# ───────────────────────────────────────────────────────────────────────────

HDRS = {"X-Emby-Token": API_KEY}

def fetch_manage():
    """Return full /Manage Channels list (Id, ManagementId, SortIndexNumber…)."""
    out, start = [], 0
    while True:
        qs = urlencode({
            "IncludeItemTypes": "ChannelManagementInfo",
            "StartIndex": start, "Limit": 30,
            "SortBy": "DefaultChannelOrder", "SortOrder": "Ascending",
            "Recursive": "true"
        })
        resp = requests.get(f"{SERVER}/LiveTv/Manage/Channels?{qs}", headers=HDRS)
        resp.raise_for_status()
        items = resp.json()["Items"]
        if not items:
            break
        out.extend(items)
        start += len(items)
    return out

def id_to_number():
    """Map {Id: Number} from /LiveTv/Channels."""
    resp = requests.get(f"{SERVER}/LiveTv/Channels", headers=HDRS)
    resp.raise_for_status()
    return {c["Id"]: c.get("Number") for c in resp.json()["Items"]}

def numeric(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return math.inf

def reorder_once(pause_ms=PAUSE_MS):
    """One bottom→top pass setting NewIndex for every channel."""
    manage = fetch_manage()
    nmap   = id_to_number()
    for ch in manage:
        ch["Number"] = nmap.get(ch["Id"])

    manage.sort(key=lambda c: numeric(c["Number"]))
    for idx, ch in reversed(list(enumerate(manage))):
        if ch.get("SortIndexNumber") == idx:
            continue
        qs  = urlencode({"ManagementId": ch["ManagementId"], "NewIndex": idx})
        url = f"{SERVER}/LiveTv/Manage/Channels/{ch['Id']}/SortIndex?{qs}"
        r   = requests.post(url, headers=HDRS)
        if r.status_code >= 400:
            sys.exit(f"SortIndex POST failed ({r.status_code})")
        time.sleep(pause_ms / 1000)

def fully_sorted():
    """Return (bool OK, full ordered Number list)."""
    manage = fetch_manage()
    nmap   = id_to_number()
    manage.sort(key=lambda c: c["SortIndexNumber"])
    nums = [nmap.get(c["Id"]) for c in manage]
    ok   = all(numeric(nums[i]) <= numeric(nums[i + 1]) for i in range(len(nums) - 1))
    return ok, nums

def trigger_guide_refresh():
    """Start the built-in 'Refresh Guide' scheduled task."""
    tasks = requests.get(f"{SERVER}/ScheduledTasks", headers=HDRS).json()
    task  = next((t for t in tasks if "guide" in t["Name"].lower()), None)
    if not task:
        print("⚠  No task containing 'guide' found in ScheduledTasks")
        return
    r = requests.post(f"{SERVER}/ScheduledTasks/Running/{task['Id']}", headers=HDRS)
    if r.status_code == 204:
        print("↻  Guide refresh started.")
    else:
        print(f"⚠  Guide refresh returned HTTP {r.status_code}")

for attempt in range(1, MAX_PASSES + 1):
    reorder_once()
    sorted_ok, numbers = fully_sorted()
    if sorted_ok:
        print(f"✔ Sorted after {attempt} pass{'es' if attempt > 1 else ''} "
              f"(total {len(numbers)} channels).")
        trigger_guide_refresh()
        break
    else:
        print(f"pass {attempt}: list still not perfect — retrying…")

else:
    print("Reached MAX_PASSES but list still not fully ordered; try increasing MAX_PASSES or PAUSE_MS.")
