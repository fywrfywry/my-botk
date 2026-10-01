import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import VideoPiped, HighQualityVideo

API_ID = int(os.getenv("API_ID", "38935531"))
API_HASH = os.getenv("API_HASH", "cec4e40653eb3ddf07d541a30cde781e")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8822269103:AAE3yUcxj4uWPEarNhh29aPLnWh5olMjypc")

# قراءة جلسة المستخدم من المتغيرات إن وجدت
SESSION_STRING = os.getenv("SESSION_STRING", "")

bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# متغير عام لحفظ العميل المساعد إذا تم إدخاله تفاعلياً
user = None
call_py = None

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
    global user, call_py
    if not user or not user.is_connected:
        await message.reply("⚠️ **تنبيه:** الحساب المساعد (UserBot) غير متصل حالياً لأنه لم يتم إعداد `SESSION_STRING`.\nيرجى إرسال أمر `/set_session [الكود]` بالخاص أو التأكد من إضافته في Railway.")
    else:
        await message.reply("👋 **مرحباً بك! البوت يعمل الآن بكفاءة تامة ومع المتصل المساعد.**\nأرسل `/play` بالرد على فيديو لبثه في المكالمة.")

# أمر جديد لتحديث الجلسة تفاعلياً من داخل تيليجرام
@bot.on_message(filters.command("set_session") & filters.private)
async def set_session_cmd(client, message):
    global user, call_py
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ يرجى إرسال الأمر مع كود الجلسة هكذا:\n`/set_session AgJSG...`")
        return
    
    new_session = args[1].strip()
    status_msg = await message.reply("🔄 جاري التحقق من كود الجلسة وربط الحساب المساعد...")
    
    try:
        # إنشاء وتشغيل جلسة المستخدم المؤقتة للتحقق
        temp_user = Client(
            "user_session_dynamic",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=new_session,
            in_memory=True
        )
        await temp_user.start()
        
        # إذا نجح الاتصال، نعتمده
        user = temp_user
        call_py = PyTgCalls(user)
        await call_py.start()
        
        await status_msg.edit_text("✅ **تم ربط الحساب المساعد وتفعيل المكالمات بنجاح تام!**")
    except Exception as e:
        await status_msg.edit_text(f"❌ كود الجلسة غير صالح أو حدث خطأ:\n`{e}`")

@bot.on_message(filters.command("play") & filters.group)
async def play_video(client, message):
    global call_py
    if not call_py:
        await message.reply("⚠️ الحساب المساعد لم يتم ربطه بعد! يرجى إرسال كود الجلسة للبوت أولاً.")
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
    global user, call_py
    await bot.start()
    
    # محاولة التشغيل التلقائي لو وُجد المتغير مسبقاً
    if SESSION_STRING:
        try:
            user = Client(
                "user_session",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=SESSION_STRING
            )
            await user.start()
            call_py = PyTgCalls(user)
            await call_py.start()
            print("✨ تم تشغيل الحساب المساعد تلقائياً من المتغيرات.")
        except Exception as e:
            print(f"⚠️ فشل التشغيل التلقائي للجلسة: {e}")

    print("-----------------------------------------")
    print("✨ يعمل البوت الأساسي وجاهز لتلقي الأوامر! ✨")
    print("-----------------------------------------")
    
    await asyncio.gather(
        asyncio.Event().wait()
    )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
