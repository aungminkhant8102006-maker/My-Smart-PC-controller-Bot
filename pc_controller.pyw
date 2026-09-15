import ctypes
import os
import subprocess
import threading
import time
import cv2
import psutil
import pyautogui
import pyperclip
import telebot
import shutil
import requests
import sounddevice as sd
import subprocess
import re
from scipy.io.wavfile import write
from google import genai
import shutil
from datetime import datetime
from gtts import gTTS
import pygame
import time
time.sleep(20)

GROQ_API_KEY = "your_token_here"


BOT_TOKEN = "your_token_here"
ALLOWED_USER_ID = "your_user_id_here"

bot = telebot.TeleBot(BOT_TOKEN)

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

motion_detection_active = False
study_mode_active = False


def background_battery_monitor():
  battery_warned_low = False
  battery_warned_full = False

  while True:
    try:
      battery = psutil.sensors_battery()
      if battery:
        percent = battery.percent
        plugged = battery.power_plugged

        if plugged and percent >= 98 and not battery_warned_full:
          bot.send_message(
              ALLOWED_USER_ID,
              f"⚡ ဘက်ထရီ {percent}% ပြည့်ပါပြီ။ အားသွင်းကြိုး ဖြုတ်နိုင်ပါပြီ။",
          )
          battery_warned_full = True

        if not plugged:
          battery_warned_full = False

        if not plugged and percent <= 20 and not battery_warned_low:
          bot.send_message(
              ALLOWED_USER_ID,
              f"🪫 ဘက်ထရီ {percent}% သာ ကျန်ပါတော့သည်။ အားသွင်းကြိုး ချိတ်ဆက်ပါ။",
          )
          battery_warned_low = True

        if plugged:
          battery_warned_low = False
    except Exception:
      pass
    time.sleep(60)

def motion_detector_thread():
  global motion_detection_active
  cap = cv2.VideoCapture(0)
  time.sleep(2)
  first_frame = None

  while motion_detection_active:
    ret, frame = cap.read()
    if not ret:
      break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if first_frame is None:
      first_frame = gray
      continue

    frame_delta = cv2.absdiff(first_frame, gray)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    for c in contours:
      if cv2.contourArea(c) > 5000:
        photo_path = "motion_alert.jpg"
        cv2.imwrite(photo_path, frame)
        with open(photo_path, "rb") as photo:
          bot.send_photo(
              ALLOWED_USER_ID,
              photo,
              caption="🚨 သတိပေးချက်: Laptop အနီးတွင် လှုပ်ရှားမှု တွေ့ရှိရပါသည်!",
          )
        if os.path.exists(photo_path):
          os.remove(photo_path)
        first_frame = gray
        time.sleep(5)
        break

    time.sleep(0.5)

  cap.release()



@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id == ALLOWED_USER_ID:
        welcome_text = """
🤖 <b>Laptop Controller Bot (အဆင့်မြင့် စနစ်)</b>

📌 <b>အခြေခံ ထိန်းချုပ်မှုများ:</b>
/status - ဘက်ထရီနှင့် စနစ်အခြေအနေ
/screenshot - မျက်နှာပြင် မှတ်တမ်းယူခြင်း
/cam - ကင်မရာ ဓာတ်ပုံရိုက်ခြင်း
/lock - Screen Lock ချခြင်း
/volup, /voldown, /mute - အသံ ထိန်းချုပ်ခြင်း
/say [text] - PC မှ အသံထွက်ဖတ်ပြခြင်း

📚 <b>စာလုပ်ရန် (Study & Productivity):</b>
/studyon - Study Mode ဖွင့်ခြင်း (Games များကို ပိတ်မည်)
/studyoff - Study Mode ပိတ်ခြင်း
/timer [minutes] - စာလုပ်ချိန် Timer မှတ်ခြင်း
/blockweb - Facebook, YouTube တို့ကို ပိတ်ခြင်း (Admin လိုအပ်သည်)
/unblockweb - Website များ ပြန်ဖွင့်ခြင်း

📁 <b>ဖိုင်နှင့် Clipboard:</b>
/getfile [filepath] - ဖိုင်/Folder လှမ်းယူခြင်း
/getclip - Copy စာသား ရယူခြင်း
/setclip [text] - Laptop သို့ စာသား Copy ကူးပေးခြင်း

⚙️ <b>စနစ်နှင့် ကွန်ရက် ထိန်းချုပ်မှု:</b>
/open [url or text] - Edge ဖြင့် ဝက်ဘ်ဆိုက် ဖွင့်ရန် (ဥပမာ- /open gemini.google.com)
/tasks - RAM အသုံးများဆုံး App ၅ ခု ကြည့်ခြင်း
/kill [processname] - App ပိတ်ချခြင်း 
/playpause - Media Play/Pause လုပ်ခြင်း
/cmd [command] - CMD ခိုင်းစေခြင်း
/scan_network - Wi-Fi ထဲရှိ Device များကို ရှာဖွေခြင်း
/sleep - PC ကို Sleep Mode သွင်းခြင်း
/restart - PC ကို Restart ချခြင်း
/shutdown - PC ကို ပိတ် (Shutdown) ခြင်း

🛡️ <b>လုံခြုံရေးနှင့် စောင့်ကြည့်မှု:</b>
/listen - အခန်းတွင်း အသံကို ၁၀ စက္ကန့် ဖမ်းယူခြင်း
/location သို့မဟုတ် /wifi - WiFi နှင့် တည်နေရာ စစ်ဆေးခြင်း
/motionon - လူစောင့်ကြည့်စနစ် ဖွင့်ခြင်း
/motionoff - လူစောင့်ကြည့်စနစ် ပိတ်ခြင်း
/windows - ဖွင့်ထားသော App များ ကြည့်ရန်

💬 <b>Smart Assistant (AI Agent):</b>
Command ရိုက်စရာမလိုဘဲ မည်သည့်မေးခွန်းကိုမဆို မေးမြန်းနိုင်ပါသည်။ 
"စက်ကို Lock ချပေး"၊ "စောင့်ကြည့်စနစ် ဖွင့်ပေး" သို့မဟုတ် "စာလုပ်တော့မယ်" ဟု AI ထံသို့ တိုက်ရိုက် မြန်မာလို အမိန့်ပေး ခိုင်းစေနိုင်ပါပြီ။
"""
        try:
            bot.reply_to(message, welcome_text, parse_mode="HTML")
        except Exception as e:
            bot.reply_to(message, f"❌ Welcome Message Error: {e}")

@bot.message_handler(commands=["getclip"])
def get_clipboard(message):
  if message.chat.id == ALLOWED_USER_ID:
    try:
      text = pyperclip.paste()
      bot.reply_to(message, f"📋 Laptop Clipboard စာသား:\n\n`{text}`")
    except Exception as e:
      bot.reply_to(message, f"❌ Error: {e}")


@bot.message_handler(commands=["setclip"])
def set_clipboard(message):
  if message.chat.id == ALLOWED_USER_ID:
    text = message.text.replace("/setclip", "").strip()
    if text:
      pyperclip.copy(text)
      bot.reply_to(message, "✅ Laptop ၏ Clipboard ထဲသို့ စာသား ကူးထည့်လိုက်ပါပြီ။")
    else:
      bot.reply_to(message, "စာသား ထည့်သွင်းပေးပါ (ဥပမာ - /setclip စာသား)")

@bot.message_handler(commands=["motion_on"])
def start_motion(message):
  global motion_detection_active
  if message.chat.id == ALLOWED_USER_ID:
    if not motion_detection_active:
      motion_detection_active = True
      threading.Thread(target=motion_detector_thread, daemon=True).start()
      bot.reply_to(
          message, "🚨 Motion Detection (သူစိမ်း စောင့်ကြည့်စနစ်) ဖွင့်လိုက်ပါပြီ။"
      )
    else:
      bot.reply_to(message, "⚠️ Motion Detection သည် ပွင့်လျက်သား ရှိနေပါသည်။")


@bot.message_handler(commands=['motion_off'])
def stop_motion(message):
    global motion_detection_active
    if message.chat.id == ALLOWED_USER_ID:
        motion_detection_active = False
        bot.reply_to(message, "🔴 Motion Detection (လူစောင့်ကြည့်စနစ်) ပိတ်လိုက်ပါပြီ။")


@bot.message_handler(commands=["studyon"])
def start_study_mode(message):
    global study_mode_active
    if message.chat.id == ALLOWED_USER_ID:
        if not study_mode_active:
            study_mode_active = True
            threading.Thread(target=study_monitor_thread, daemon=True).start()
            bot.reply_to(message, "📚 Study Mode ဖွင့်လိုက်ပါပြီ။ (Steam နှင့် Discord တို့ကို ပိတ်ထားပါမည်)")
        else:
            bot.reply_to(message, "⚠️ Study Mode ပွင့်နေပြီးသား ဖြစ်ပါသည်။")

@bot.message_handler(commands=["studyoff"])
def stop_study_mode(message):
    global study_mode_active
    if message.chat.id == ALLOWED_USER_ID:
        study_mode_active = False
        bot.reply_to(message, "🟢 Study Mode ပိတ်လိုက်ပါပြီ။ ဂိမ်းနှင့် အခြား App များ ပြန်သုံးနိုင်ပါပြီ။")
def study_monitor_thread():
    global study_mode_active
    banned_apps = ["steam.exe", "discord.exe"]
    while study_mode_active:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() in banned_apps:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        time.sleep(3)

@bot.message_handler(commands=["cmd"])
def run_command(message):
  if message.chat.id == ALLOWED_USER_ID:
    cmd = message.text.replace("/cmd", "").strip()
    if not cmd:
      bot.reply_to(message, "Command ရိုက်ထည့်ပေးပါ (ဥပမာ - /cmd ipconfig)")
      return
    try:
      result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
      output = result.decode("utf-8", errors="ignore")
      if len(output) > 4000:
        output = output[:4000] + "\n...(truncated)"
      bot.reply_to(message, f"💻 Terminal Output:\n```\n{output}\n```")
    except subprocess.CalledProcessError as e:
      bot.reply_to(
          message,
          f"❌ Command Error:\n```\n{e.output.decode('utf-8', errors='ignore')}\n```",
      )
    except Exception as e:
      bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['getfile'])
def send_pc_file(message):
    if message.chat.id == ALLOWED_USER_ID:
        filepath = message.text.replace("/getfile", "").strip().strip('"').strip("'")
        
        if not os.path.exists(filepath):
            bot.reply_to(message, "❌ ဖိုင် သို့မဟုတ် Folder လမ်းကြောင်း မမှန်ကန်ပါ။")
            return

        try:
            if os.path.isdir(filepath):
                bot.reply_to(message, "📦 Folder ဖြစ်နေသဖြင့် Zip ဖိုင်အဖြစ် ပြောင်းလဲနေပါသည်...")
                folder_name = os.path.basename(os.path.normpath(filepath))
                zip_path = f"{folder_name}.zip"
                
                shutil.make_archive(folder_name, 'zip', filepath)
                
                with open(zip_path, 'rb') as doc:
                    bot.send_document(message.chat.id, doc, caption=f"📁 {folder_name} (Zip Archive)")
                
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            else:
                with open(filepath, 'rb') as doc:
                    bot.send_document(message.chat.id, doc)
        except Exception as e:
            bot.reply_to(message, f"❌ ပေးပို့၍မရပါ: {e}")

@bot.message_handler(content_types=["document", "photo"])
def handle_incoming_file(message):
  if message.chat.id == ALLOWED_USER_ID:
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    try:
      if message.content_type == "document":
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name
      else:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_name = f"photo_{int(time.time())}.jpg"

      downloaded_file = bot.download_file(file_info.file_path)
      save_dest = os.path.join(desktop_path, file_name)

      with open(save_dest, "wb") as new_file:
        new_file.write(downloaded_file)

      bot.reply_to(
          message, f"📥 ဖိုင်ကို လက်ခံရရှိပြီး Desktop ပေါ်သို့ သိမ်းဆည်းလိုက်ပါပြီ:\n`{file_name}`"
      )
    except Exception as e:
      bot.reply_to(message, f"❌ ဖိုင်သိမ်းဆည်းရာတွင် အခက်အခဲရှိပါသည်: {e}")

@bot.message_handler(commands=["status"])
def check_status(message):
  if message.chat.id == ALLOWED_USER_ID:
    battery = psutil.sensors_battery()
    bat_text = (
        f"{battery.percent}% ({'အားသွင်းနေသည်' if battery.power_plugged else 'အားမသွင်းပါ'})"
        if battery
        else "မသိရှိပါ"
    )
    bot.reply_to(
        message,
        f"📊 စနစ်အခြေအနေ:\n🔋 ဘက်ထရီ: {bat_text}\n💻 CPU အသုံးပြုမှု:"
        f" {psutil.cpu_percent()}%\n🧠 RAM အသုံးပြုမှု: {psutil.virtual_memory().percent}%",
    )

@bot.message_handler(commands=["screenshot"])
def take_screenshot(message):
  if message.chat.id == ALLOWED_USER_ID:
    path = "screenshot.png"
    pyautogui.screenshot(path)
    with open(path, "rb") as photo:
      bot.send_photo(message.chat.id, photo)
    if os.path.exists(path):
      os.remove(path)


@bot.message_handler(commands=['scan_network'])
def scan_network(message):
    if message.chat.id == ALLOWED_USER_ID:
        try:
            bot.reply_to(message, "🔍 Wi-Fi အတွင်းရှိ Device များကို ရှာဖွေနေပါသည်...")
            
            result = subprocess.check_output("arp -a", shell=True).decode()
            
            devices = re.findall(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\s+([0-9a-fA-F-]+)\s+", result)
            
            response = "📱 **လက်ရှိ ချိတ်ဆက်ထားသော Devices များ:**\n\n"
            count = 0
            for ip, mac in devices:
                if ip.startswith("192.168.") or ip.startswith("10."):
                    count += 1
                    response += f"{count}. 🌐 IP: `{ip}`\n   🔗 MAC: `{mac}`\n\n"
            
            if count == 0:
                response += "အခြား ချိတ်ဆက်ထားသော Device မတွေ့ပါ။"
                
            bot.reply_to(message, response, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=["cam"])
def take_cam(message):
  if message.chat.id == ALLOWED_USER_ID:
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
      path = "webcam.jpg"
      cv2.imwrite(path, frame)
      with open(path, "rb") as photo:
        bot.send_photo(message.chat.id, photo)
      if os.path.exists(path):
        os.remove(path)
    else:
      bot.reply_to(message, "❌ ကင်မရာ ဖွင့်မရပါ။")
    cap.release()

@bot.message_handler(commands=["lock"])
def lock_pc(message):
  if message.chat.id == ALLOWED_USER_ID:
    os.system("rundll32.exe user32.dll,LockWorkStation")
    bot.reply_to(message, "🔒 Screen Lock ချလိုက်ပါပြီ။")


@bot.message_handler(commands=["mute"])
def toggle_mute(message):
  if message.chat.id == ALLOWED_USER_ID:
    ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
    bot.reply_to(message, "🔇 အသံ အဖွင့်/အပိတ် ပြုလုပ်လိုက်ပါပြီ။")


@bot.message_handler(commands=["volup"])
def volume_up(message):
  if message.chat.id == ALLOWED_USER_ID:
    for _ in range(5):
      ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
      ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
    bot.reply_to(message, "🔊 အသံ တိုးမြှင့်လိုက်ပါပြီ။")


@bot.message_handler(commands=["voldown"])
def volume_down(message):
  if message.chat.id == ALLOWED_USER_ID:
    for _ in range(5):
      ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
      ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
    bot.reply_to(message, "🔉 အသံ လျှော့ချလိုက်ပါပြီ။")

@bot.message_handler(commands=['tasks'])
def list_tasks(message):
    if message.chat.id == ALLOWED_USER_ID:
        # Memory အများဆုံးသုံးနေသော Process ၅ ခုကို ပြသခြင်း
        procs = sorted(psutil.process_iter(['name', 'memory_percent']), key=lambda p: p.info['memory_percent'] or 0, reverse=True)[:5]
        msg = "📊 **လက်ရှိ လုပ်ဆောင်နေသော Processes များ:**\n\n"
        for p in procs:
            msg += f"• `{p.info['name']}` ({p.info['memory_percent']:.1f}% RAM)\n"
        bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['kill'])
def kill_task(message):
    if message.chat.id == ALLOWED_USER_ID:
        target = message.text.replace("/kill", "").strip()
        if not target:
            bot.reply_to(message, "⚠️ ပိတ်လိုသော Process အမည် ထည့်ပါ (ဥပမာ - `/kill Spotify` သို့မဟုတ် `/kill chrome.exe`)")
            return
        if not target.lower().endswith(".exe"):
            target += ".exe"
            
        os.system(f"taskkill /f /im {target}")
        bot.reply_to(message, f"🛑 `{target}` ကို ပိတ်ချလိုက်ပါပြီ။", parse_mode="Markdown")

@bot.message_handler(commands=['playpause'])
def media_toggle(message):
    if message.chat.id == ALLOWED_USER_ID:
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
        bot.reply_to(message, "⏯️ Play / Pause ပြုလုပ်ပြီးပါပြီ။")

@bot.message_handler(commands=['listen'])
def listen_audio(message):
    if message.chat.id == ALLOWED_USER_ID:
        try:
            sec = 10
            bot.reply_to(message, f"🎙️ အသံကို {sec} စက္ကန့်ကြာ ဖမ်းယူနေပါသည်...")
            fs = 44100
            recording = sd.rec(int(sec * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            audio_file = "surveillance.wav"
            write(audio_file, fs, recording)
            
            with open(audio_file, 'rb') as audio:
                bot.send_voice(message.chat.id, audio)
            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception as e:
            bot.reply_to(message, f"❌ အသံဖမ်းမရပါ: {e}")

@bot.message_handler(commands=['location', 'wifi'])
def get_location_wifi(message):
    if message.chat.id == ALLOWED_USER_ID:
        try:

            wifi_cmd = subprocess.check_output("netsh wlan show interfaces", shell=True).decode(errors='ignore')
            ssid = "Unknown / LAN"
            for line in wifi_cmd.split('\n'):
                if "SSID" in line and "BSSID" not in line:
                    ssid = line.split(":")[1].strip()
                    break
        
            res = requests.get("http://ip-api.com/json/").json()
            loc_msg = (
                f"📡 **Network & Location Status**\n"
                f"• WiFi SSID: `{ssid}`\n"
                f"• IP Address: `{res.get('query')}`\n"
                f"• City/Region: {res.get('city')}, {res.get('regionName')}\n"
                f"• ISP: {res.get('isp')}\n"
                f"• Google Maps: https://maps.google.com/?q={res.get('lat')},{res.get('lon')}"
            )
            bot.reply_to(message, loc_msg, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ အချက်အလက် ဆွဲမရပါ: {e}")

@bot.message_handler(commands=["sleep"])
def pc_sleep(message):
    if message.chat.id == ALLOWED_USER_ID:
        bot.reply_to(message, "🌙 PC ကို Sleep Mode သွင်းလိုက်ပါပြီ။")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

@bot.message_handler(commands=["shutdown"])
def pc_shutdown(message):
    if message.chat.id == ALLOWED_USER_ID:
        bot.reply_to(message, "🛑 PC ကို ပိတ် (Shutdown) လိုက်ပါပြီ။")
        os.system("shutdown /s /t 5")

@bot.message_handler(commands=["restart"])
def pc_restart(message):
    if message.chat.id == ALLOWED_USER_ID:
        bot.reply_to(message, "🔄 PC ကို Restart ချလိုက်ပါပြီ။")
        os.system("shutdown /r /t 5")

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"
blocked_sites = ["www.facebook.com", "facebook.com", "www.youtube.com", "youtube.com"]

@bot.message_handler(commands=["blockweb"])
def block_websites(message):
    if message.chat.id == ALLOWED_USER_ID:
        try:
            with open(HOSTS_PATH, "r+") as file:
                content = file.read()
                for site in blocked_sites:
                    if site not in content:
                        file.write(f"{REDIRECT_IP} {site}\n")
            bot.reply_to(message, "🚫 Facebook နှင့် YouTube တို့ကို ယာယီ ပိတ်လိုက်ပါပြီ။")
        except PermissionError:
            bot.reply_to(message, "⚠️ Error: VS Code ကို 'Run as Administrator' ဖြင့် ဖွင့်မှသာ Website များကို ပိတ်နိုင်ပါမည်။")

@bot.message_handler(commands=["unblockweb"])
def unblock_websites(message):
    if message.chat.id == ALLOWED_USER_ID:
        try:
            with open(HOSTS_PATH, "r+") as file:
                lines = file.readlines()
                file.seek(0)
                for line in lines:
                    if not any(site in line for site in blocked_sites):
                        file.write(line)
                file.truncate()
            bot.reply_to(message, "🌐 Website များ ပြန်လည် ဖွင့်ပေးလိုက်ပါပြီ။")
        except PermissionError:
            bot.reply_to(message, "⚠️ Error: Admin Permission လိုအပ်ပါသည်။")

def timer_thread(chat_id, minutes):
    time.sleep(minutes * 60)
    bot.send_message(chat_id, f"⏰ အချိန်ပြည့်ပါပြီ! မိနစ် ({minutes}) ကြာ စာလုပ်ပြီးပြီဖြစ်၍ ခဏနားပါ။")

@bot.message_handler(commands=["timer"])
def start_timer(message):
    if message.chat.id == ALLOWED_USER_ID:
        try:
            cmd_parts = message.text.split()
            if len(cmd_parts) > 1:
                minutes = int(cmd_parts[1])
                threading.Thread(target=timer_thread, args=(message.chat.id, minutes), daemon=True).start()
                bot.reply_to(message, f"⏳ မိနစ် {minutes} အတွက် Timer စတင်လိုက်ပါပြီ။ အချိန်ပြည့်လျှင် သတိပေးပါမည်။")
            else:
                bot.reply_to(message, "⚠️ မိနစ်ကို ထည့်သွင်းပါ (ဥပမာ - /timer 25)")
        except ValueError:
            bot.reply_to(message, "⚠️ ဂဏန်းသာ ထည့်ပါ (ဥပမာ - /timer 25)")

@bot.message_handler(commands=["say"])
def speak_natural(message):
    if message.chat.id == ALLOWED_USER_ID:
        text = message.text.replace("/say", "").strip()
        if text:
            bot.reply_to(message, "🗣️ အသံထွက် ဖတ်ပြနေပါသည်...")
            try:
                tts = gTTS(text=text, lang='en', tld='com') 
                filename = "voice_temp.mp3"
                tts.save(filename)

                pygame.mixer.init()
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy(): 
                    time.sleep(1)

                pygame.mixer.music.unload()
                pygame.mixer.quit()
                os.remove(filename)
                
            except Exception as e:
                bot.reply_to(message, f"⚠️ Error: {e}")
        else:
            bot.reply_to(message, "⚠️ ပြောစေလိုသော စာသားကို ထည့်ပါ (ဥပမာ - /say Hello)")

@bot.message_handler(commands=["windows"])
def show_open_windows(message):
    if message.chat.id == ALLOWED_USER_ID:
        bot.reply_to(message, "🔍 ဖွင့်ထားသော App များနှင့် Window များကို ရှာဖွေနေပါသည်...")
        try:

            ps_cmd = 'Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object -ExpandProperty MainWindowTitle'
            result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, encoding='utf-8')
            

            windows = result.stdout.strip().split('\n')
            clean_windows = [w.strip() for w in windows if w.strip()]
            
            if clean_windows:

                response = "🖥️ လက်ရှိ ဖွင့်ထားသော App များနှင့် Website များ:\n\n"
                for idx, w in enumerate(clean_windows, 1):
                    response += f"{idx}. {w}\n"
            else:
                response = "🤷‍♂️ ဖွင့်ထားသော App/Window မတွေ့ပါ။"
                
            bot.reply_to(message, response)
        except Exception as e:
            bot.reply_to(message, f"⚠️ Error: {e}")

@bot.message_handler(commands=["open"])
def open_custom_website(message):
    if message.chat.id == ALLOWED_USER_ID:

        target = message.text.replace("/open", "").strip()
        
        if target:
            bot.reply_to(message, f"🚀 Microsoft Edge တွင် '{target}' ကို ဖွင့်ပေးနေပါသည်... ပြန်ပိတ်ရန် - /closetab - ဟုရိုက်ပါ [လက်ရှိ Tab တစ်ခုတည်းကို ပိတ်ရန်]" )
            try:
                os.system(f"start msedge {target}")
            except Exception as e:
                bot.reply_to(message, f"⚠️ Error: {e}")
        else:
            bot.reply_to(message, "⚠️ ဖွင့်လိုသော Website ကို ထည့်ပါ (ဥပမာ - /open gemini.google.com)")

@bot.message_handler(commands=["closetab"])
def close_current_tab(message):
    if message.chat.id == ALLOWED_USER_ID:
        bot.reply_to(message, "❌ လက်ရှိ မျက်နှာပြင်တွင် ဖွင့်ထားသော Tab / Window ကို ပိတ်လိုက်ပါပြီ။")
        try:

            os.system('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys(\'^w\')"')
        except Exception as e:
            bot.reply_to(message, f"⚠️ Error: {e}")

@bot.message_handler(func=lambda msg: not msg.text.startswith('/'))
def groq_chat(message):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_instruction = """
        You are a PC controller AI. Reply in Burmese. 
        If the user asks to lock the PC, include the exact word [CMD_LOCK] in your reply.
        If they ask to turn on motion detection, include [CMD_MOTIONON] in your reply.
        If they ask to turn off motion detection, include [CMD_MOTIONOFF] in your reply.
        If they ask to sleep/shutdown, include [CMD_SLEEP].
        """
        
        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": message.text}
            ],
            "temperature": 0.7
        }

        res = requests.post(url, headers=headers, json=payload, timeout=25).json()
        
        if "error" in res:
            bot.reply_to(message, f"❌ Groq Error: {res['error'].get('message', res['error'])}")
            return

        reply_text = res['choices'][0]['message']['content']

        if "[CMD_LOCK]" in reply_text:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            reply_text = reply_text.replace("[CMD_LOCK]", "🔒 (Screen Lock ချလိုက်ပါပြီ)")

        if "[CMD_MOTIONON]" in reply_text:
            try:
                start_motion(message)
                reply_text = reply_text.replace("[CMD_MOTIONON]", "👁️ (လူစောင့်ကြည့်စနစ်ကို စတင်လိုက်ပါပြီ။)")
            except Exception as e:
                reply_text = reply_text.replace("[CMD_MOTIONON]", f"⚠️ (Motion Error: {e})")

        if "[CMD_MOTIONOFF]" in reply_text:
            try:
                stop_motion(message)
                reply_text = reply_text.replace("[CMD_MOTIONOFF]", "🔴 (လူစောင့်ကြည့်စနစ်ကို ပိတ်လိုက်ပါပြီ။)")
            except Exception as e:
                reply_text = reply_text.replace("[CMD_MOTIONOFF]", f"⚠️ (Stop Motion Error: {e})")

        bot.reply_to(message, reply_text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ AI Error: {e}")
        
if __name__ == "__main__":
  try:
    bot.send_message(
        ALLOWED_USER_ID, "🟢 Laptop စတင် အလုပ်လုပ်ပါပြီ။ Bot အဆင်သင့်ရှိပါသည်။ bla bla bla..."
    )
  except Exception:
    pass

  threading.Thread(target=background_battery_monitor, daemon=True).start()

  bot.infinity_polling()