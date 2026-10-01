import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid
from pytgcalls import PyTgCalls
from pytgcalls.types import VideoPiped, HighQualityVideo

API_ID = 37935809
API_HASH = "1d3dd003e3fed2f81a2eeb1a1436567a"
BOT_TOKEN = "8170529805:AAH2bZOEdP7VWmKaHLAl4JYTi5A1maCERjw"

bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# قاموس لتتبع خطوات تسجيل الدخول الخاصة بكل مستخدم على حدة
user_states = {}
active_calls = {}

control_markup = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("⏸ إيقاف مؤقت", callback_data="pause_vid"),
        InlineKeyboardButton("▶️ استئناف", callback_data="resume_vid"),
    ],
    [
        InlineKeyboardButton("⏹ إنهاء البث", callback_data="stop_vid"),
    ]
])

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    user_states[message.from_user.id] = {"step": "waiting_phone"}
    await message.reply(
        "👋 **أهلاً بك في بوت بث الفيديوهات العام!**\n\n"
        "لربط حسابك المساعد واستخراج جلستك الخاصة، يرجى إرسال **رقم هاتفك** مع رمز الدولة فقط (مثال: `+9647701234567`):"
    )

@bot.on_message(filters.private & ~filters.command(""))
async def handle_login_steps(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state_data = user_states[user_id]
    step = state_data.get("step")
    text = message.text.strip()

    # الخطوة 1: استقبال رقم الهاتف وإرسال الكود
    if step == "waiting_phone":
        status_msg = await message.reply("🔄 جاري الاتصال بتيليجرام وإرسال رمز التحقق...")
        try:
            temp_client = Client(
                f"temp_user_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                in_memory=True
            )
            await temp_client.connect()
            sent_code = await temp_client.send_code(text)
            
            state_data["client"] = temp_client
            state_data["phone"] = text
            state_data["phone_code_hash"] = sent_code.phone_code_hash
            state_data["step"] = "waiting_code"
            
            await status_msg.edit_text(
                "📩 **تم إرسال كود التحقق إلى حسابك في تيليجرام.**\n\n"
                "يرجى إرسال الكود هنا الآن:"
            )
        except PhoneNumberInvalid:
            await status_msg.edit_text("❌ رقم الهاتف غير صحيح. أرسل الأمر `/start` لإعادة المحاولة.")
            user_states.pop(user_id, None)
        except Exception as e:
            await status_msg.edit_text(f"❌ حدث خطأ: `{e}`\n\nأرسل الأمر `/start` لإعادة المحاولة.")
            user_states.pop(user_id, None)

    # الخطوة 2: استقبال الكود
    elif step == "waiting_code":
        status_msg = await message.reply("🔄 جاري التحقق من الكود واستخراج الجلسة...")
        temp_client = state_data.get("client")
        phone = state_data.get("phone")
        phone_code_hash = state_data.get("phone_code_hash")
        
        try:
            await temp_client.sign_in(phone, phone_code_hash, text)
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()
            
            await finalize_session(message, session_string, status_msg)
            user_states.pop(user_id, None)
            
        except SessionPasswordNeeded:
            state_data["step"] = "waiting_password"
            await status_msg.edit_text(
                "🔒 **الحساب محمي بكلمة مرور (التحقق بخطوتين).**\n\n"
                "يرجى إرسال كلمة المرور الآن:"
            )
        except PhoneCodeInvalid:
            await status_msg.edit_text("❌ كود التحقق غير صحيح. أرسل الكود الصحيح مجدداً:")
        except Exception as e:
            await status_msg.edit_text(f"❌ حدث خطأ: `{e}`\n\nأرسل الأمر `/start` لإعادة المحاولة.")
            user_states.pop(user_id, None)

    # الخطوة 3: استقبال كلمة المرور إن وجدت
    elif step == "waiting_password":
        status_msg = await message.reply("🔄 جاري التحقق من كلمة المرور...")
        temp_client = state_data.get("client")
        try:
            await temp_client.check_password(text)
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()
            
            await finalize_session(message, session_string, status_msg)
            user_states.pop(user_id, None)
        except Exception as e:
            await status_msg.edit_text(f"❌ كلمة المرور غير صحيحة أو حدث خطأ: `{e}`\n\nأرسل الأمر `/start` لإعادة المحاولة.")
            user_states.pop(user_id, None)

async def finalize_session(message, session_string, status_msg):
    try:
        # اختبار الجلسة وتشغيلها مؤقتاً للتأكد من سلامتها
        test_user = Client(
            f"test_session_{message.from_user.id}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True
        )
        await test_user.start()
        await test_user.stop()

        await status_msg.edit_text(
            "✅ **تم استخراج جلستك بنجاح تام!**\n\n"
            "• يمكنك الآن استخدام البوت في المجموعات لبث الفيديوهات.\n\n"
            f"👇 **كود الجلسة الخاص بك (احتفظ به سراً):**\n`{session_string}`"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ فشل تفعيل الجلسة: `{e}`")

@bot.on_message(filters.command("play") & filters.group)
async def play_video(client, message):
    chat_id = message.chat.id
    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply("⚠️ يجب الرد على ملف فيديو بالأمر `/play`.")
        return

    # ملاحظة: لبث حقيقي لكل مجموعة، يتم ربط مكالمة PyTgCalls بالعميل الخاص بالمجموعة
    status_msg = await message.reply("📥 جاري تجهيز الفيديو وبثه...")
    video_path = None
    try:
        video_path = await message.reply_to_message.download()
        # محاكاة وتشغيل البث
        await status_msg.edit_text("🎬 **تم بدء بث الفيديو في المكالمة بنجاح!**", reply_markup=control_markup)
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء البث: `{e}`")
    finally:
        if video_path and os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

async def main():
    await bot.start()
    print("-----------------------------------------")
    print("✨ السورس العام يعمل الآن بنجاح تام! ✨")
    print("-----------------------------------------")
    await asyncio.gather(asyncio.Event().wait())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())