import requests
import time
import threading
import os
from bs4 import BeautifulSoup
from datetime import datetime

SERVER_URL = "https://luckyloop.onrender.com"
MW_EMAIL    = os.environ.get("MW_EMAIL", "")
MW_PASSWORD = os.environ.get("MW_PASSWORD", "")
PHPSESSID   = os.environ.get("MW_PHPSESSID", "")

LOGIN_URL  = "https://www.microworkers.com/login.php"
TARGET_URL = "https://www.microworkers.com/jobs.php?Filter=no&Sort=NEWEST&Id_category=09"

JOB_NAMES = [
    {"full": "TTV-Data Entry - PC required. Not for mobile phones. (E766-1470)", "short": "1470"},
    {"full": "TTV-Data Entry from images (E502-1033)",                            "short": "1033"},
    {"full": "TTV-Data Entry from images (E1096-1891)",                           "short": "1891"},
    {"full": "TTV-Data Entry from images (E833-1532)",                            "short": "1532"},
    {"full": "TTV-Data Entry - PC required. Not for mobile phones. (E766-2289)",  "short": "2289"},
    {"full": "TTV-Data Entry (E766-1469sv)",                                      "short": "1469"},
    {"full": "TTV-Data Entry from images (E502-1001)",                            "short": "1001"},
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
})

# প্রথমে পুরানো PHPSESSID দিয়ে চেষ্টা করবে
if PHPSESSID:
    session.cookies.set("PHPSESSID", PHPSESSID, domain="www.microworkers.com")


def do_login():
    """MW_EMAIL ও MW_PASSWORD দিয়ে login করে নতুন session নেয়"""
    if not MW_EMAIL or not MW_PASSWORD:
        print("[Login] MW_EMAIL বা MW_PASSWORD দেওয়া নেই, login করা যাবে না।")
        return False

    try:
        print("[Login] Auto-login চেষ্টা করা হচ্ছে...")

        # প্রথমে login page থেকে token/form নেওয়া
        r = session.get(LOGIN_URL, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        # login form এর hidden field খোঁজা
        form_data = {
            "email":    MW_EMAIL,
            "password": MW_PASSWORD,
            "login":    "Login",
        }

        # কিছু site hidden token রাখে, সেগুলো নেওয়া
        for inp in soup.select("input[type=hidden]"):
            name = inp.get("name")
            val  = inp.get("value", "")
            if name:
                form_data[name] = val

        # login POST করা
        login_resp = session.post(
            LOGIN_URL,
            data=form_data,
            timeout=15,
            allow_redirects=True,
            headers={"Referer": LOGIN_URL}
        )

        # login সফল হয়েছে কিনা যাচাই
        if "logout" in login_resp.text.lower() or "withdraw" in login_resp.text.lower():
            new_sessid = session.cookies.get("PHPSESSID", domain="www.microworkers.com")
            print(f"[Login] ✅ Login সফল! নতুন PHPSESSID: {new_sessid}")
            update_status("ok", f"✅ Auto-login সফল! নতুন session নেওয়া হয়েছে।")
            return True
        else:
            print("[Login] ❌ Login ব্যর্থ! Email/Password ভুল হতে পারে।")
            update_status("error", "❌ Auto-login ব্যর্থ! MW_EMAIL বা MW_PASSWORD চেক করুন।")
            return False

    except Exception as e:
        print(f"[Login] Error: {e}")
        update_status("error", f"❌ Login error: {str(e)[:80]}")
        return False


def calc_available(pos_str):
    try:
        cur, total = pos_str.split("/")
        return str(max(int(total) - int(cur), 0))
    except:
        return "-"


def update_status(status, message):
    try:
        requests.post(f"{SERVER_URL}/api/scraper-status", json={
            "status":  status,
            "message": message
        }, timeout=10)
        print(f"[Status] {status} | {message}")
    except Exception as e:
        print(f"[Status Error] {e}")


def scrape_jobs():
    global session

    try:
        r = session.get(TARGET_URL, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        listings = soup.select(".jobslist")
        count = len(listings)
        print(f"[Scraper] Found {count} listings")

        if count == 0:
            # PHPSESSID expire হয়েছে, auto-login চেষ্টা করো
            print("[Scraper] 0 listings — PHPSESSID expire হয়েছে। Auto-login চেষ্টা করা হচ্ছে...")
            update_status("expired", "⚠️ Session expire! Auto-login চেষ্টা করা হচ্ছে...")

            success = do_login()
            if not success:
                update_status("expired", "⚠️ Auto-login ব্যর্থ! Render এ MW_EMAIL ও MW_PASSWORD চেক করুন।")
            return  # এই cycle বাদ দাও, পরের cycle-এ নতুন session দিয়ে চেষ্টা হবে

        update_status("ok", f"✅ Running | {count} listings found")

        for job in JOB_NAMES:
            for item in listings:
                name_el = item.select_one(".jobname a")
                pos_el  = item.select_one(".jobdone p")
                if not name_el or not pos_el:
                    continue
                if name_el.get_text(strip=True) == job["full"]:
                    position  = pos_el.get_text(strip=True)
                    available = calc_available(position)
                    link      = name_el.get("href", TARGET_URL)
                    push(job["short"], position, available, link)
                    break

    except Exception as e:
        print(f"[Scraper] Error: {e}")
        update_status("error", f"❌ Error: {str(e)[:80]}")


def push(cid, position, available, link):
    try:
        requests.post(f"{SERVER_URL}/save", json={
            "job_name":  cid,
            "position":  position,
            "available": available,
            "link":      link
        }, timeout=10)
        print(f"[Scraper] Pushed {cid} pos={position} avail={available}")
    except Exception as e:
        print(f"[Scraper] Push error: {e}")


def scrape_loop():
    print("[Scraper] Starting — checking at sec 2, 4, 33, 35...")
    time.sleep(5)
    CHECK_SECONDS = {2, 4, 33, 35}
    last_checked_sec = -1

    while True:
        sec = datetime.now().second
        if sec in CHECK_SECONDS and sec != last_checked_sec:
            last_checked_sec = sec
            print(f"[Scraper] Checking at :{sec:02d}")
            scrape_jobs()
        time.sleep(0.5)


def start_scraper():
    t = threading.Thread(target=scrape_loop, daemon=True)
    t.start()
