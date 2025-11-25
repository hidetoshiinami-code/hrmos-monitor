import json
import os
import requests
from playwright.sync_api import sync_playwright

# ▼▼▼ 設定エリア（ここを書き換えてください） ▼▼▼
TARGET_URLS = [
    "https://hrmos.co/agent/corporates/1904709793501646848/jobs",
    "https://hrmos.co/agent/corporates/1770319815756488704/jobs",
"https://hrmos.co/agent/corporates/1436614092130979840/jobs",
  "https://hrmos.co/agent/corporates/1053931721759670272/jobs",
  "https://hrmos.co/agent/corporates/1956886623554834432/jobs",
  "https://hrmos.co/agent/corporates/1405385391128940544/jobs",
  "https://hrmos.co/agent/corporates/1812391728765788160/jobs",
  "https://hrmos.co/agent/corporates/1147069602614968320/jobs",
  "https://hrmos.co/agent/corporates/1666275327663013888/jobs",
  "https://hrmos.co/agent/corporates/1986289420124028928/jobs",
  "https://hrmos.co/agent/corporates/1986962988647747584/jobs",
  "https://hrmos.co/agent/corporates/1770319815756488704/jobs",
  "https://hrmos.co/agent/corporates/1289479246299828224/jobs",
  "https://hrmos.co/agent/corporates/2118962155710185472/jobs",
  "https://hrmos.co/agent/corporates/1770319815756488704/jobs",
  "https://hrmos.co/agent/corporates/1991326154413535232/jobs",
  "https://hrmos.co/agent/corporates/1976872088247259136/jobs",
    
    # カンマ区切りで増やせます
]
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# SlackのURLは後で設定画面に入力するので、ここは書き換えなくてOK
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
DB_FILE = "hrmos_job_db.json"

class HRMOSMonitor:
    def __init__(self):
        self.db = self.load_db()

    def load_db(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_db(self):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)

    def fetch_jobs(self, url):
        jobs = {}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({"User-Agent": "Mozilla/5.0"})
                print(f"Accessing: {url} ...")
                page.goto(url, wait_until="networkidle")

                links = page.query_selector_all("a")
                for link in links:
                    href = link.get_attribute("href")
                    title = link.inner_text().strip()
                    if href and "/jobs/" in href and len(title) > 0:
                        if href.startswith("/"):
                            full_url = f"https://hrmos.co{href}"
                        else:
                            full_url = href
                        if title:
                            jobs[full_url] = title
                browser.close()
                return jobs
        except Exception as e:
            print(f"Error: {e}")
            return {}

    def send_alert(self, company_url, new_jobs):
        if not SLACK_WEBHOOK_URL:
            print("Slack URL未設定のためスキップ")
            return

        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "🚨 HRMOS 新着求人", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*企業:* {company_url}"}}
        ]
        for url, title in new_jobs.items():
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"🆕 *<{url}|{title}>*"}})

        requests.post(SLACK_WEBHOOK_URL, json={"blocks": blocks})

    def run(self):
        for url in TARGET_URLS:
            current = self.fetch_jobs(url)
            if not current: continue
            
            if url not in self.db:
                self.db[url] = current
                self.save_db()
                continue

            old = self.db[url]
            new_urls = set(current.keys()) - set(old.keys())
            
            if new_urls:
                new_data = {u: current[u] for u in new_urls}
                self.send_alert(url, new_data)
                self.db[url] = current
                self.save_db()

if __name__ == "__main__":
    HRMOSMonitor().run()
