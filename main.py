import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

API_ID = 37935809
API_HASH = "1d3dd003e3fed2f81a2eeb1a1436567a"
BOT_TOKEN = "8170529805:AAH2bZOEdP7VWmKaHLAl4JYTi5A1maCERjw"

bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_states = {}

main_menu = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔑 استخراج جلسة (Session)", callback_data="cmd_session")],
    [InlineKeyboardButton("🎥 بث فيديو من حسابك الشخصي", callback_data="cmd_broadcast")]
])

control_markup = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("⏸ إيقاف مؤقت", callback_data="pause_vid"),
        InlineKeyboardButton("▶️️ استئناف", callback_data="resume_vid"),
    ],
    [
        InlineKeyboardButton("⏹ إنهاء البث", callback_data="stop_vid"),
    ]
])

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    user_states.pop(message.from_user.id, None)
    await message.reply(
        "👋 **أهلاً بك في بوت البث المباشر عبر الحساب الشخصي!**\n\n"
        "هذا البوت يتيح لك ربط حسابك وبث الفيديوهات مباشرة في قنواتك ومجموعاتك.\n"
        "اختر ما ترغب به:",
        reply_markup=main_menu
    )

@bot.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "cmd_session":
        user_states[user_id] = {"step": "waiting_phone"}
        await callback_query.message.edit_text(
            "📱 **استخراج جلسة حسابك (Session String):**\n\n"
            "يرجى إرسال **رقم هاتفك** مع رمز الدولة (مثال: `+9647701234567`):"
        )
    elif data == "cmd_broadcast":
        user_states[user_id] = {"step": "waiting_session_for_broadcast"}
        await callback_query.message.edit_text(
            "🔑 **إعداد البث عبر حسابك:**\n\n"
            "للبدء، أرسل أولاً **كود الجلسة (Session String)** الخاص بحسابك المساعد:"
        )
    elif data == "stop_vid":
        await callback_query.answer("تم إنهاء البث.", show_alert=True)
        await callback_query.message.edit_text("⏹ **تم إيقاف البث بنجاح.**")

@bot.on_message(filters.private & ~filters.command(""))
async def handle_all_steps(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state_data = user_states[user_id]
    step = state_data.get("step")
    text = message.text.strip() if message.text else ""

    # --- خطوات استخراج الجلسة العادية ---
    if step == "waiting_phone":
        status_msg = await message.reply("🔄 جاري الاتصال بتيليجرام وإرسال رمز التحقق...")
        try:
            temp_client = Client(f"temp_user_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await temp_client.connect()
            sent_code = await temp_client.send_code(text)
            state_data["client"] = temp_client
            state_data["phone"] = text
            state_data["phone_code_hash"] = sent_code.phone_code_hash
            state_data["step"] = "waiting_code"
            await status_msg.edit_text("📩 **تم إرسال كود التحقق إلى حسابك.** أرسل الكود هنا:")
        except Exception as e:
            await status_msg.edit_text(f"❌ حدث خطأ: `{e}`\n\nأرسل `/start` للعودة.")
            user_states.pop(user_id, None)

    elif step == "waiting_code":
        status_msg = await message.reply("🔄 جاري التحقق من الكود...")
        temp_client = state_data.get("client")
        try:
            await temp_client.sign_in(state_data.get("phone"), state_data.get("phone_code_hash"), text)
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()
            await status_msg.edit_text(f"✅ **تم استخراج جلستك بنجاح:**\n\n`{session_string}`")
            user_states.pop(user_id, None)
        except SessionPasswordNeeded:
            state_data["step"] = "waiting_password"
            await status_msg.edit_text("🔒 **الحساب محمي بكلمة مرور (تحقق بخطوتين).** أرسل كلمة المرور:")
        except Exception as e:
            await status_msg.edit_text(f"❌ خطأ: `{e}`\n\nأرسل `/start` للعودة.")
            user_states.pop(user_id, None)

    elif step == "waiting_password":
        status_msg = await message.reply("🔄 جاري التحقق من كلمة المرور...")
        temp_client = state_data.get("client")
        try:
            await temp_client.check_password(text)
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()
            await status_msg.edit_text(f"✅ **تم استخراج جلستك بنجاح:**\n\n`{session_string}`")
            user_states.pop(user_id, None)
        except Exception as e:
            await status_msg.edit_text(f"❌ كلمة المرور خاطئة: `{e}`\n\nأرسل `/start` للعودة.")
            user_states.pop(user_id, None)

    # --- خطوات إعداد وبدء البث عبر حساب المستخدم ---
    elif step == "waiting_session_for_broadcast":
        state_data["session_string"] = text
        state_data["step"] = "waiting_chat_id"
        await message.reply(
            "✅ تم حفظ الجلسة.\n\n"
            "📍 **الآن أرسل معرف القناة أو المجموعة** التي تريد البث فيها (مثال: `@YourChannel` أو الرابط):"
        )

    elif step == "waiting_chat_id":
        state_data["chat_id"] = text
        state_data["step"] = "waiting_video_for_broadcast"
        await message.reply(
            f"✅ تم حفظ القناة: `{text}`\n\n"
            "📥 **الخطوة الأخيرة: أرسل الآن ملف الفيديو (Video) الذي تريد بثه من حسابك:**"
        )

    elif step == "waiting_video_for_broadcast":
        if not message.video and not message.document:
            await message.reply("⚠️️ يرجى إرسال ملف فيديو صحيح.")
            return

        status_msg = await message.reply("🔄 جاري تسجيل الدخول بحسابك، فتح المكالمة، وبدء البث...")
        session_str = state_data.get("session_string")
        chat_id = state_data.get("chat_id")

        try:
            # تحميل الفيديو المؤقت
            video_path = await message.download()

            # تشغيل عميل المستخدم الحقيقي والبث من خلاله
            user_client = Client(
                f"broadcaster_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_str,
                in_memory=True
            )
            await user_client.start()

            # تهيئة عميل الاتصال الصوتي والمرئي (PyTgCalls) لحسابك
            call_client = PyTgCalls(user_client)
            await call_client.start()

            # الانضمام للمكالمة وبث الفيديو باستخدام جلسة حسابك
            await call_client.join(
                chat_id,
                MediaStream(video_path)
            )

            await status_msg.edit_text(
                f"🎬 **تم بدء البث المباشر بنجاح من حسابك في القناة/المجموعة:**\n`{chat_id}`\n\n"
                "• البث يعمل الآن عبر حسابك الشخصي.",
                reply_markup=control_markup
            )
            
            # الاحتفاظ بالعملاء للتحكم لاحقاً إذا لزم الأمر
            state_data["call_client"] = call_client
            state_data["user_client"] = user_client

        except Exception as e:
            await status_msg.edit_text(f"❌ حدث خطأ أثناء بدء البث من حسابك: `{e}`\n\nتأكد أن حسابك مشرف ولديه صلاحية المكالمات.")
            user_states.pop(user_id, None)

async def main():
    await bot.start()
    print("-----------------------------------------")
    print("✨ بوت البث بالحسابات الشخصية يعمل بنجاح! ✨")
    print("-----------------------------------------")
    await asyncio.gather(asyncio.Event().wait())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
