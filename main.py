import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import VideoPiped, HighQualityVideo

API_ID = int(os.getenv("API_ID", "38935531"))
API_HASH = os.getenv("API_HASH", "cec4e40653eb3ddf07d541a30cde781e")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8822269103:AAE3yUcxj4uWPEarNhh29aPLnWh5olMjypc")
SESSION_STRING = os.getenv("SESSION_STRING", "your_session_string")

# استخدام MemoryStorage لتجنب مشاكل الملفات المؤقتة على الخوادم السحابية
bot = Client(
    "MainBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

user = Client(
    "UserBot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True
)

call_py = PyTgCalls(user)

control_markup = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("⏸ إيقاف مؤقت", callback_data="pause_vid"),
        InlineKeyboardButton("▶️ استئناف", callback_data="resume_vid"),
    ],
    [
        InlineKeyboardButton("⏹ إنهاء البث", callback_data="stop_vid"),
    ]
])

@bot.on_message(filters.command("start") & filters.group)
async def start_cmd(client, message):
    await message.reply("👋 **مرحباً بك! البوت يعمل الآن بكفاءة تامة.**\nأرسل `/play` بالرد على فيديو لبثه في المكالمة.")

@bot.on_message(filters.command("play") & filters.group)
async def play_video(client, message):
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
    # التأكد من وجود حلقة أحداث فعالة وربطها بشكل صحيح
    loop = asyncio.get_running_loop()
    
    await bot.start()
    await user.start()
    await call_py.start()
    
    print("-----------------------------------------")
    print("✨ تم تشغيل بوت المكالمات بنجاح تام وثابت! ✨")
    print("-----------------------------------------")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("تم إيقاف البوت يدويياً.")
