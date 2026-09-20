import os
import re
import logging
import time
from telethon import TelegramClient, events

# إعداد التسجيل للمتابعة
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# بيانات التطبيق الخاصة بك
API_ID = 37935809          
API_HASH = '1d3dd003e3fed2f81a2eeb1a1436567a'

# جلب توكن البوت مباشرة من متغيرات البيئة في Railway (أو وضعه احتياطياً هنا)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8740693156:AAFX0oVCj5hAWjx1DdQ-5SfCx-_ZssP1Pv8')

# إنشاء العميل باستخدام Bot Token ليعمل تلقائياً على السيرفر
client = TelegramClient('bot_session', API_ID, API_HASH)

def is_luhn_valid(card_number: str) -> bool:
    """التحقق من صحة رقم البطاقة رياضياً عبر خوارزمية Luhn"""
    digits = [int(d) for d in card_number]
    checksum = 0
    reverse_digits = digits[::-1]

    for idx, digit in enumerate(reverse_digits):
        if idx % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit

    return checksum % 10 == 0

async def process_ulp_file_with_dashboard(input_path: str, output_path: str, status_msg) -> int:
    """معالجة الملف خطوة بخطوة مع تحديث اللوحة بدون توقف"""
    card_full_pattern = re.compile(
        r'\b((?:\d[ -]*?){13,19})'                 
        r'[\s|:/,-]+'                              
        r'((?:0[1-9]|1[0-2])[\s|:/,-]+(?:20)?\d{2})' 
        r'[\s|:/,-]+'                              
        r'(\d{3,4})\b'                             
    )

    found_entries = set()
    
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as infile:
        for line_no, line in enumerate(infile, 1):
            if line_no % 250000 == 0:
                try:
                    await status_msg.edit(
                        f"📊 **لوحة العمليات التفاعلية**\n"
                        f"----------------------------------\n"
                        f"🔄 **الحالة:** جاري فحص الأسطر والبحث...\n"
                        f"📝 **الأسطر المفحوصة:** {line_no:,}\n"
                        f"💳 **البطاقات الصالحة المكتشفة:** {len(found_entries):,}\n"
                        f"----------------------------------"
                    )
                except Exception:
                    pass

            matches = card_full_pattern.findall(line)
            for match in matches:
                raw_card, raw_exp, cvv = match
                clean_card = re.sub(r'\D', '', raw_card)
                
                exp_digits = re.findall(r'\d+', raw_exp)
                if len(exp_digits) == 2:
                    month, year = exp_digits[0], exp_digits[1]
                    formatted_exp = f"{month.zfill(2)}|{year}"
                else:
                    continue

                if 13 <= len(clean_card) <= 19 and is_luhn_valid(clean_card):
                    full_entry = f"{clean_card}|{formatted_exp}|{cvv}"
                    found_entries.add(full_entry)

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for entry in sorted(found_entries):
            outfile.write(entry + '\n')

    return len(found_entries)

@client.on(events.NewMessage)
async def handle_all_messages(event):
    if not event.text or 't.me/' in event.text:
        return

    text = event.text.strip()
    match = re.search(r't\.me/(?:c/)?([^/]+)/(\d+)', text)
    if not match:
        return

    target_chat = match.group(1)
    message_id = int(match.group(2))
    
    if target_chat.isdigit():
        target_chat = int(f"-100{target_chat}")

    # رسالة لوحة التفاعل الأولية
    msg = await event.respond(
        "📊 **لوحة العمليات التفاعلية**\n"
        "----------------------------------\n"
        "⏳ **الحالة:** جارٍ الاتصال بالمنشور...\n"
        "----------------------------------"
    )
    
    input_path = "download_tele_file.txt"
    output_path = "extracted_cards.txt"

    try:
        target_msg = await client.get_messages(target_chat, ids=message_id)
        
        if not target_msg or not target_msg.media:
            await msg.edit("❌ الرابط لا يحتوي على ملف أو وسائط صالحة.")
            return

        # دالة لتعقب نسبة التنزيل وتحديث اللوحة لحظياً
        last_update_time = 0
        async def download_progress_callback(current, total):
            nonlocal last_update_time
            current_time = time.time()
            if current_time - last_update_time > 1:
                last_update_time = current_time
                percent = int((current / total) * 100) if total > 0 else 0
                mb_current = current / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                try:
                    await msg.edit(
                        f"📊 **لوحة العمليات التفاعلية (التنزيل)**\n"
                        f"----------------------------------\n"
                        f"📥 **جارٍ التنزيل:** {percent}%\n"
                        f"📦 **المجتاز:** {mb_current:.1f} MB من {mb_total:.1f} MB\n"
                        f"----------------------------------"
                    )
                except Exception:
                    pass

        # تنزيل الملف مع تفعيل العداد التفاعلي
        await client.download_media(target_msg, file=input_path, progress_callback=download_progress_callback)

        await msg.edit(
            "📊 **لوحة العمليات التفاعلية**\n"
            "----------------------------------\n"
            "🔍 **الحالة:** اكتمل التنزيل! بدأ فحص الأسطر واستخراج البطاقات...\n"
            "----------------------------------"
        )

        # تشغيل المعالجة والفلترة
        cards_count = await process_ulp_file_with_dashboard(input_path, output_path, msg)

        if cards_count > 0:
            await msg.edit(
                f"✅ **تمت العملية بنجاح!**\n"
                f"----------------------------------\n"
                f"📄 **إجمالي البطاقات المستخرجة:** {cards_count:,}\n"
                f"🚀 جارٍ إرسال الملف النهائي..."
            )
            
            await client.send_file(
                event.chat_id,
                output_path,
                caption=f"📄 تم استخراج {cards_count:,} بطاقة بنجاح."
            )
        else:
            await msg.edit("❌ لم يتم العثور على أي بطاقات مطابقة للمواصفات داخل الملف.")

    except Exception as e:
        await msg.edit(f"⚠️ حدث خطأ أثناء المعالجة: {e}")

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

if __name__ == '__main__':
    print("السكريبت يعمل الآن عبر البوت...")
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()
