import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid
from pytgcalls import PyTgCalls
from pytgcalls.types import VideoPiped, HighQualityVideo

# بيانات الـ API التي استخرجتها من موقع تيليجرام
API_ID = 37935809
API_HASH = "1d3dd003e3fed2f81a2eeb1a1436567a"

# توكن البوت الجديد الذي أرسلته
BOT_TOKEN = "8170529805:AAH2bZOEdP7VWmKaHLAl4JYTi5A1maCERjw"

bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user = None
call_py = None

# قاموس لتتبع خطوات تسجيل الدخول
user_states = {}

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
    global user
    if user and user.is_connected:
        await message.reply("👋 أهلاً بك! البوت والحساب المساعد متصلان وجاهزان للعمل.")
        return
        
    user_states[message.from_user.id] = {"step": "waiting_phone"}
    await message.reply(
        "👋 **أهلاً بك في بوت بث الفيديوهات!**\n\n"
        "لربط الحساب المساعد، يرجى إرسال **رقم هاتفك** مع رمز الدولة فقط (مثال: `+201234567890`):"
    )

@bot.on_message(filters.private & ~filters.command(""))
async def handle_login_steps(client, message: Message):
    global user, call_py
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return

    state_data = user_states[user_id]
    step = state_data.get("step")
    text = message.text.strip()

    # الخطوة 1: استقبال رقم الهاتف وإرسال كود التحقق
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
            await status_msg.edit_text("❌ رقم الهاتف غير صحيح. يرجى إرسال الأمر `/start` والمحاولة مجدداً.")
            user_states.pop(user_id, None)
        except Exception as e:
            await status_msg.edit_text(f"❌ حدث خطأ: `{e}`\n\nأرسل الأمر `/start` لإعادة المحاولة.")
            user_states.pop(user_id, None)

    # الخطوة 2: استقبال كود التحقق واستخراج الجلسة تلقائياً
    elif step == "waiting_code":
        status_msg = await message.reply("🔄 جاري التحقق من الكود واستخراج الجلسة...")
        temp_client = state_data.get("client")
        phone = state_data.get("phone")
        phone_code_hash = state_data.get("phone_code_hash")
        
        try:
            await temp_client.sign_in(phone, phone_code_hash, text)
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()
            
            await finalize_user_session(message, session_string, status_msg)
            user_states.pop(user_id, None)
            
        except SessionPasswordNeeded:
            state_data["step"] = "waiting_password"
            await status_msg.edit_text(
                "🔒 **الحساب محمي بالتحقق بخطوتين (كلمة المرور).**\n\n"
                "يرجى إرسال كلمة مرور الحساب الخاصة بك الآن:"
            )
        except PhoneCodeInvalid:
            await status_msg.edit_text("❌ كود التحقق غير صحيح. يرجى إرسال الكود الصحيح مجدداً:")
        except Exception as e:
            await status_msg.edit_text(f"❌ حدث خطأ: `{e}`\n\nأرسل الأمر `/start` لإعادة المحاولة.")
            user_states.pop(user_id, None)

    # الخطوة 3: استقبال كلمة المرور إن وجدت
    elif step == "waiting_password":
        status_msg = await message.reply("🔄 جاري التحقق من كلمة المرور واستخراج الجلسة...")
        temp_client = state_data.get("client")
        
        try:
            await temp_client.check_password(text)
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()
            
            await finalize_user_session(message, session_string, status_msg)
            user_states.pop(user_id, None)
            
        except Exception as e:
            await status_msg.edit_text(f"❌ كلمة المرور غير صحيحة أو حدث خطأ: `{e}`\n\nأرسل الأمر `/start` لإعادة المحاولة.")
            user_states.pop(user_id, None)

async def finalize_user_session(message, session_string, status_msg):
    global user, call_py
    try:
        temp_user = Client(
            "user_session_dynamic",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True
        )
        await temp_user.start()
        
        user = temp_user
        call_py = PyTgCalls(user)
        await call_py.start()
        
        # حفظ الجلسة في ملف نصي تلقائياً
        with open("session.txt", "w") as f:
            f.write(session_string)

        await status_msg.edit_text(
            "✅ **تم استخراج الجلسة وربط الحساب المساعد بنجاح تام!**\n\n"
            "• تم حفظ الجلسة في ملف `session.txt`.\n"
            "• الآن يمكنك استخدام البوت في المجموعات وبث الفيديوهات بالأمر `/play`.\n\n"
            f"👇 **كود الجلسة الخاص بك:**\n`{session_string}`"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ فشل تشغيل الجلسة: `{e}`")

@bot.on_message(filters.command("play") & filters.group)
async def play_video(client, message):
    global call_py
    if not call_py or not user or not user.is_connected:
        await message.reply("⚠️ الحساب المساعد غير متصل! يرجى الذهاب إلى محادثة البوت الخاصة وإرسال أمر `/start` لربطه.")
        return

    chat_id = message.chat.id
    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply("⚠️ يجب الرد على ملف فيديو بالأمر `/play`.")
        return

    status_msg = await message.reply("📥 جاري تحميل الفيديو وبثه...")
    video_path = None
    try:
        video_path = await message.reply_to_message.download()
        await call_py.join_group_call(
            chat_id,
            VideoPiped(video_path, video_parameters=HighQualityVideo())
        )
        await status_msg.edit_text("🎬 **تم بدء بث الفيديو بنجاح!**", reply_markup=control_markup)
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ: `{e}`")
    finally:
        if video_path and os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

@bot.on_callback_query()
async def callbacks(client, cq):
    global call_py
    if not call_py:
        await cq.answer("المساعد غير متصل!", show_alert=True)
        return
        
    chat_id = cq.message.chat.id
    try:
        if cq.data == "pause_vid":
            await call_py.pause_stream(chat_id)
            await cq.answer("تم الإيقاف المؤقت ⏸", show_alert=True)
        elif cq.data == "resume_vid":
            await call_py.resume_stream(chat_id)
            await cq.answer("تم الاستئناف ▶️", show_alert=True)
        elif cq.data == "stop_vid":
            await call_py.leave_group_call(chat_id)
            await cq.message.edit_text("⏹ تم إنهاء البث وإغلاق المكالمة.")
    except Exception as e:
        await cq.answer(f"خطأ: {e}", show_alert=True)

async def main():
    await bot.start()
    print("-----------------------------------------")
    print("✨ البوت يعمل الآن بالتوكن والبيانات الجديدة وجاهز! ✨")
    print("-----------------------------------------")
    await asyncio.gather(
        asyncio.Event().wait()
    )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
