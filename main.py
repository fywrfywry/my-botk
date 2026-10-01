import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import VideoPiped, HighQualityVideo

# ==================== إعدادات الحساب والبوت ====================
# قراءة البيانات من متغيرات البيئة في Railway (أو وضعها مباشرة هنا)
API_ID = int(os.getenv("API_ID", "38935531"))
API_HASH = os.getenv("API_HASH", "cec4e40653eb3ddf07d541a30cde781e")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8822269103:AAE3yUcxj4uWPEarNhh29aPLnWh5olMjypc")

# جلسة الحساب المساعد (ضع كود الجلسة هنا أو كمتغير بيئي SESSION_STRING)
SESSION_STRING = os.getenv("SESSION_STRING", "your_session_string")

# 1. تشغيل البوت الأساسي (للأوامر والأزرار)
bot = Client(
    "MainTelegramBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 2. تشغيل الحساب المساعد (للدخول للمكالمة)
user = Client(
    "AssistantUserBot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

call_py = PyTgCalls(user)

# ==================== أزرار التحكم بالشاشة ====================
control_markup = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("⏸ إيقاف مؤقت", callback_data="pause_vid"),
            InlineKeyboardButton("▶️ استئناف", callback_data="resume_vid"),
        ],
        [
            InlineKeyboardButton("⏹ إنهاء البث والخروج", callback_data="stop_vid"),
        ]
    ]
)

# ==================== الأوامر والمميزات ====================

@bot.on_message(filters.command("start") & filters.group)
async def start_cmd(client, message):
    await message.reply(
        "👋 **مرحباً بك في سورس مكالمات وفيديو تليجرام المتطور!**\n\n"
        "📌 **طريقة الاستخدام:**\n"
        "• قم بالرد على أي رسالة فيديو بالأمر `/play` لبثه في مكالمة المجموعة أو القناة.\n"
        "• استخدم الأزرار التي تظهر للتحكم الكامل بالبث (إيقاف، استئناف، إنهاء)."
    )

@bot.on_message(filters.command("play") & filters.group)
async def play_custom_video(client, message):
    chat_id = message.chat.id
    
    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply("⚠️ **عذراً!** يجب عليك الرد على ملف فيديو (Video) بداخل المجموعة واستخدام الأمر `/play`.")
        return

    status_msg = await message.reply("📥 **جاري تحميل الفيديو المعالج... يرجى الانتظار**")
    
    video_path = None
    try:
        video_path = await message.reply_to_message.download()
        
        await status_msg.edit_text("🚀 **جاري فتح المكالمة وبث الفيديو بجودة عالية...**")
        
        await call_py.join_group_call(
            chat_id,
            VideoPiped(
                video_path,
                width=1280,
                height=720,
                framerate=30,
                video_parameters=HighQualityVideo()
            )
        )
        
        await status_msg.edit_text(
            "🎬 **تم بدء بث الفيديو في المكالمة بنجاح!**\nاستخدم الأزرار أدناه للتحكم الكامل:",
            reply_markup=control_markup
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ **حدث خطأ أثناء تشغيل الفيديو:**\n`{str(e)}`")
    finally:
        # تنظيف الملف المحلي بعد التحميل لتوفير مساحة السيرفر
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass

@bot.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    try:
        if data == "pause_vid":
            await call_py.pause_stream(chat_id)
            await callback_query.answer("تم إيقاف الفيديو مؤقتاً ⏸", show_alert=True)
            
        elif data == "resume_vid":
            await call_py.resume_stream(chat_id)
            await callback_query.answer("تم استئناف البث ▶️", show_alert=True)
            
        elif data == "stop_vid":
            await call_py.leave_group_call(chat_id)
            await callback_query.message.edit_text("⏹ **تم إنهاء المكالمة وإغلاق البث بنجاح.**")
    except Exception as e:
        await callback_query.answer(f"خطأ: {str(e)}", show_alert=True)

async def main():
    await bot.start()
    await user.start()
    await call_py.start()
    
    print("-----------------------------------------")
    print("✨ تم تشغيل سورس بوت المكالمات والفيديو بنجاح! ✨")
    print("-----------------------------------------")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
