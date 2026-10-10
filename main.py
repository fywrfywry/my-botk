import asyncio
import json
import uuid
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# بيانات البروكسي السكني الخاص بك
PROXY_URL = "http://name8nvk3l-pool-res.mobile.corp-country-US-state-4736286-mode-query-tier-premium:SLRCvxnaZI5nIr0S@185.185.51.243:443"

# التوكن والأيدي الخاص بك
BOT_TOKEN = "8837027411:AAEj-ZenZmuTNvkwD6ppoWx5mS-rDR9fjuA"
ADMIN_ID = 7352706784  # ايدي حسابك للحماية

# حالات المحادثة
GET_LINK, GET_LOOPS = range(2)


class ZefameAutomatedBot:

  def __init__(self, service_id: str = "232"):
    self.service_id = str(service_id)
    self.session = requests.Session()
    self.session.proxies = {"http": PROXY_URL, "https": PROXY_URL}
    self.session.headers.update({
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Origin": "https://zefame.com",
        "Referer": "https://zefame.com/",
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like"
            " Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"
        ),
        "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
    })

  def check_current_ip(self):
    try:
      res = self.session.get("https://api.ipify.org?format=json", timeout=10)
      return res.json().get("ip")
    except Exception:
      return "تعذر الفحص"

  def run_single_process(self, tiktok_link: str):
    self.device_id = str(uuid.uuid4())
    ip_addr = self.check_current_ip()

    url_check = "https://api.zefame.com/api_free.php?lang=fr"
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    data = {"action": "checkVideoId", "link": tiktok_link}

    try:
      response_check = self.session.post(
          url_check, headers=headers, data=data, timeout=15
      )
      if response_check.status_code != 200:
        return False, ip_addr, "فشل الاتصال بموقع zefame"

      res_json = response_check.json()
      video_id = None
      if isinstance(res_json, dict):
        if "data" in res_json and isinstance(res_json["data"], dict):
          video_id = res_json["data"].get("videoId") or res_json["data"].get(
              "id"
          )
        if not video_id:
          video_id = (
              res_json.get("videoId")
              or res_json.get("id")
              or res_json.get("video_id")
          )

      if not video_id:
        return False, ip_addr, "لم يتم استخراج videoId"

      url_service = "https://api.zefame.com/api_free.php"
      params = {
          "lang": "fr",
          "action": "check",
          "device": self.device_id,
          "service": self.service_id,
          "videoId": str(video_id),
      }

      response_service = self.session.get(url_service, params=params, timeout=15)
      if response_service.status_code == 200:
        try:
          return True, ip_addr, response_service.json()
        except Exception:
          return True, ip_addr, response_service.text
      else:
        return False, ip_addr, f"رمز الحالة: {response_service.status_code}"

    except Exception as e:
      return False, ip_addr, str(e)


# --- دوال محادثة البوت التفاعلية ---


async def start_
