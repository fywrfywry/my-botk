import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pytgcalls import PyTgCalls
from pytgcalls.types import VideoPiped, HighQualityVideo

API_ID = int(os.getenv("API_ID", "38935531"))
API_HASH = os.getenv("API_HASH", "cec4e40653eb3ddf07d541a30cde781e")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8822269103:AAE3yUcxj4uWPEarNhh29aPLnWh5olMjypc")

# تشغيل البوت الأساسي فقط في البداية دون أي أخطاء أو جلسات مسبقة
bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user = None
call_py = None
waiting_for_session = set()

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
        
    waiting_for_session.add(message.from_user.id)
    await message.reply(
        "👋 **أهلاً بك يا غالي!**\n\n"
        "للبدء، يرجى إرسال **كود الجلسة (Session String)** الخاص بك هنا في المحادثة الآن:"
    )

@bot.on_message(filters.private & ~filters.command(""))
async def get_session_input(client, message: Message):
    global user, call_py
    user_id = message.from_user.id
    
    if user_id in waiting_for_session:
        session_text = message.text.strip()
        waiting_for_session.remove(user_id)
        
        status_msg = await message.reply("🔄 جاري التحقق من كود الجلسة وربط الحساب المساعد...")
        
        try:
            temp_user = Client(
                "user_session_dynamic",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_text,
                in_memory=True
            )
            await temp_user.start()
            
            user = temp_user
            call_py = PyTgCalls(user)
            await call_py.start()
            
            await status_msg.edit_text("✅ **تم ربط الحساب المساعد بنجاح تام!**\nالآن يمكنك استخدام البوت في المجموعات وبث الفيديوهات بالأمر `/play`.")
        except Exception as e:
            await status_msg.edit_text(f"❌ كود الجلسة غير صالح أو حدث خطأ:\n`{e}`\n\nأرسل `/start` لإعادة المحاولة.")

@bot.on_message(filters.command("play") & filters.group)
async def play_video(client, message):
    global call_py
    if not call_py or not user or not user.is_connected:
        await message.reply("⚠️ الحساب المساعد غير متصل! يرجى الذهاب إلى محادثة البوت الخاصة وإرسال أمر `/start` لتزويده بكود الجلسة.")
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
    print("✨ البوت الأساسي اشتغل بنجاح ولن يحدث خطأ حظر بعد الآن! ✨")
    print("-----------------------------------------")
    await asyncio.gather(
        asyncio.Event().wait()
    )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
