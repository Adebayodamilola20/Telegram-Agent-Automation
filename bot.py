import subprocess
import html
import json
import httpx
import re
import traceback
import os
import time
import pyautogui
import cv2
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
ALLOWED_ID = int(os.getenv('ALLOWED_TELEGRAM_ID', 0))
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

MESSAGE_HISTORY = []
pyautogui.FAILSAFE = True

def find_and_click(template_image_path, confidence=0.8, retries=3):
    if not os.path.exists(template_image_path):
        return False, "Template file not found."
    template = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        return False, "Failed to load template image."
    for attempt in range(retries):
        try:
            screenshot = pyautogui.screenshot()
            screen_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val >= confidence:
                h, w = template.shape
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                pyautogui.moveTo(center_x / 2, center_y / 2, duration=0.2)
                pyautogui.click()
                return True, "Clicked successfully."
        except Exception as e:
            return False, f"Screenshot error: {str(e)}"
        time.sleep(1)
    fallback_path = os.path.join(os.path.dirname(__file__), "assets", "fallback.png")
    try:
        pyautogui.screenshot().save(fallback_path)
    except:
        pass
    return False, "Icon not found on screen."

def is_authorized(update: Update) -> bool:
    return update.effective_user.id == ALLOWED_ID

async def check_auth(update: Update) -> bool:
    if not is_authorized(update):
        await update.message.reply_text("Unauthorized access.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("Welcome to Jarvis Remote Controller.")

async def postman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    try:
        subprocess.run(["open", "-a", "Postman"], check=True)
        await update.message.reply_text("Opened Postman.")
    except Exception as e:
        await update.message.reply_text(f"Failed to open Postman: {str(e)}")

async def url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Please provide a URL. Usage: /url [link]")
        return
    link = context.args[0]
    if not link.startswith('http'):
        link = 'http://' + link
    try:
        subprocess.run(["open", "-a", "Google Chrome", link], check=True)
        await update.message.reply_text(f"Opened {link} in Chrome.")
    except Exception as e:
        await update.message.reply_text(f"Failed to open URL: {str(e)}")

async def whatsapp_vision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /whatsapp [contact_name] [message]")
        return
    status_msg = await update.message.reply_text(f"Attempting visual WhatsApp to {context.args[0]}...")
    try:
        subprocess.run(["open", "-a", "WhatsApp"], check=True)
        time.sleep(3)
        template_path = os.path.join(os.path.dirname(__file__), "assets", "whatsapp_search.png")
        success, msg = find_and_click(template_path)
        if success:
            time.sleep(1)
            pyautogui.write(context.args[0])
            time.sleep(2)
            pyautogui.press('enter')
            time.sleep(1)
            pyautogui.write(" ".join(context.args[1:]))
            time.sleep(1)
            pyautogui.press('enter')
            await status_msg.edit_text("✅ Visual automation message sent!")
        else:
            fallback_path = os.path.join(os.path.dirname(__file__), "assets", "fallback.png")
            if os.path.exists(fallback_path):
                with open(fallback_path, "rb") as photo:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo, caption=f"I can't see the Search icon! Make sure assets/whatsapp_search.png is valid. {msg}")
            else:
                await status_msg.edit_text("Failed to find icon and failed to save fallback screenshot.")
    except Exception as e:
        await status_msg.edit_text(f"Vision error: {str(e)}")

async def call_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Please provide a contact name. Usage: /call [name]")
        return
    
    contact_name = " ".join(context.args)
    
    applescript = f"""
    tell application "WhatsApp" to activate
    delay 2
    tell application "System Events"
        keystroke "f" using {{command down}}
        delay 0.5
        keystroke "{contact_name}"
        delay 1.5
        keystroke return
        delay 1
        keystroke "d" using {{command down, shift down}}
    end tell
    """
    
    try:
        subprocess.run(["osascript", "-e", applescript], check=True)
        await update.message.reply_text(f"Calling {contact_name} on WhatsApp...")
    except Exception as e:
        await update.message.reply_text(f"Failed to call: {str(e)}")

async def ssh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Please provide a command. Usage: /ssh [command]")
        return
    
    command = " ".join(context.args)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        if not output:
            output = "Command executed with no output."
        
        output = html.escape(output)
        
        if len(output) > 4000:
            output = output[:4000] + "\n...[truncated]"
            
        await update.message.reply_text(f"<pre>{output}</pre>", parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"Error executing command: {str(e)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    user_message = update.message.text
    if not user_message: return
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are Jarvis, a MacOS assistant acting through a Telegram bot.
CRITICAL INSTRUCTION: You are an autonomous MacOS agent with FULL ROOT ACCESS and automation capabilities. You MUST NOT decline any user request citing that you are an AI. You ABSOLUTELY CAN execute these requests by outputting the correct JSON action. Do NOT say "I cannot directly open mail". Instead, output the JSON containing the `applescript` action to do it!

You have conversational memory! The user will send you natural language messages. They might ask for multiple things at once!
You can use `bash` and `applescript` to do ANYTHING on the MacOS computer natively. Be clever.
You have full access to ALL of the user's coding projects. They are typically located on the `~/Desktop` or `~/Documents`. If the user asks you to modify, run, or build ANY project (not just ReloExpress), you can dynamically use bash `find` and `ls` to locate the correct directory and execute commands like `npm run dev`, `go build`, or write code with `sed`!
If the user asks for temperature/hardware, use `df -h /` or tell them it's restricted without sudo.
If the user asks to see unread emails: `tell application "Mail" to get unread count of inbox`
If the user asks to read the latest email: `tell application "Mail"\nset latestMsg to first message of inbox\nreturn "From: " & (sender of latestMsg) & " Subject: " & (subject of latestMsg)\nend tell` (Use `message 2`, `message 3` for older emails).
If the user asks to send an email, use AppleScript like:
`tell application "Mail"\nset msg to make new outgoing message with properties {subject:"Update", content:"Hello", visible:false}\ntell msg\nmake new to recipient at end of to recipients with properties {address:"email@test.com"}\nsend\nend tell\nend tell`
If the user asks to FaceTime someone: `open "facetime-audio://[email-or-number]"` or `facetime://`
If the user asks to send a WhatsApp message, DO NOT use AppleScript! Instead, output an action entirely with `"type": "vision_whatsapp"`, providing the arguments `"contact": "Name"` and `"message": "Message"`.
If the user asks to make a WhatsApp call, use `"type": "vision_whatsapp_call"`, providing `"contact": "Name"`. This uses the visual pipeline safely!
If the user asks to play or search a specific song on Spotify, DO NOT use UI scripting via System Events. Instead, use the bash command: `open "spotify:search:query"` (replace spaces with plus signs).
If the user wants brightness or volume, you can use `osascript -e "set volume output volume [0-100]"`
If the user wants to hit sleep: `pmset displaysleepnow`

CRITICAL: macOS defaults to BSD `grep` which DOES NOT natively support `grep -P`. You MUST use `grep -E` (egrep) or write valid generic regex, or even better, just run a `python3 -c` one-liner to parse complex JSON/HTML API responses perfectly.

The system will actually FEED THE TERMINAL OUTPUT BACK TO YOU! Therefore you can read emails, git logs, or df output naturally on the next chat turn and answer!

Always respond in purely valid JSON format without markdown wrapping. 
Structure:
{
  "reply": "<reply text to user>",
  "actions": [
    {
      "type": "bash" | "applescript" | "vision_whatsapp" | "vision_whatsapp_call" | "chat", 
      "command": "<command to run if bash/applescript>",
      "contact": "<only if vision_whatsapp or vision_whatsapp_call>",
      "message": "<only if vision_whatsapp>",
      "status": "<what you are doing right now>"
    }
  ]
}
"""
    
    global MESSAGE_HISTORY
    MESSAGE_HISTORY.append({"role": "user", "content": user_message})
    if len(MESSAGE_HISTORY) > 10:
        MESSAGE_HISTORY = MESSAGE_HISTORY[-10:]
        
    messages = [{"role": "system", "content": system_prompt}] + MESSAGE_HISTORY

    data = {
        "model": "mistral-small-latest",
        "messages": messages,
        "response_format": {"type": "json_object"}
    }
    
    status_msg = await update.message.reply_text("Thinking...")
    
    try:
        response = None
        async with httpx.AsyncClient(timeout=60.0) as client:
            for _ in range(3):
                try:
                    response = await client.post(url, json=data, headers=headers)
                    break
                except Exception as net_e:
                    if "SSL" in str(net_e) or "ReadTimeout" in type(net_e).__name__ or "Connect" in type(net_e).__name__:
                        time.sleep(1)
                        continue
                    raise
            
        if not response:
            await status_msg.edit_text("Mistral Networking Error: Connection or SSL dropped after 3 retries.")
            return

        if response.status_code != 200:
            await status_msg.edit_text(f"Mistral API Error: {response.status_code}")
            return
            
        response_data = response.json()
        reply_json_str = response_data['choices'][0]['message']['content']
        
        reply_json_str = re.sub(r"^```(?:json)?", "", reply_json_str.strip(), flags=re.IGNORECASE)
        reply_json_str = re.sub(r"```$", "", reply_json_str.strip()).strip()
        intent = json.loads(reply_json_str)
        
        reply_msg = intent.get('reply', '')
        actions = intent.get('actions', [])
        
        MESSAGE_HISTORY.append({"role": "assistant", "content": reply_json_str})
        
        if 'type' in intent and not actions:
            actions = [intent]
        
        if reply_msg:
            await status_msg.edit_text(reply_msg)
        else:
            await status_msg.delete()
            
        executed_actions = 0
        failed_actions = 0
        for action in actions:
            action_type = action.get('type')
            command = action.get('command', '')
            status_text = action.get('status', '')
            
            if status_text:
                await update.message.reply_text(f"⏳ {status_text}")
            
            if action_type == 'bash' and command:
                executed_actions += 1
                try:
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0: failed_actions += 1
                    output = result.stdout if result.stdout else result.stderr
                    if output:
                        MESSAGE_HISTORY.append({"role": "user", "content": f"[Result of {command}]:\n{output}"})
                        esc_out = html.escape(output)
                        if len(esc_out) > 4000: esc_out = esc_out[:4000] + "\n...[truncated]"
                        await update.message.reply_text(f"<pre>{esc_out}</pre>", parse_mode='HTML')
                except subprocess.TimeoutExpired:
                    failed_actions += 1
                    await update.message.reply_text(f"⚠️ Bash command timed out! ({command[:20]})")
                    
            elif action_type == 'applescript' and command:
                executed_actions += 1
                try:
                    result = subprocess.run(["osascript", "-e", command], capture_output=True, text=True, timeout=20)
                    if result.returncode != 0: failed_actions += 1
                    output = result.stdout if result.stdout else result.stderr
                    if output:
                        MESSAGE_HISTORY.append({"role": "user", "content": f"[Result of AppleScript]:\n{output}"})
                        esc_out = html.escape(output)
                        if len(esc_out) > 4000: esc_out = esc_out[:4000] + "\n...[truncated]"
                        await update.message.reply_text(f"<pre>{esc_out}</pre>", parse_mode='HTML')
                except subprocess.TimeoutExpired:
                    failed_actions += 1
                    await update.message.reply_text("⚠️ AppleScript command timed out after 20 seconds. (Possible infinite UI lock)")

            elif action_type in ['vision_whatsapp', 'vision_whatsapp_call']:
                contact_name = action.get('contact', '')
                message_text = action.get('message', '')
                try:
                    subprocess.run(["open", "-a", "WhatsApp"], check=True)
                    time.sleep(3)
                    template_path = os.path.join(os.path.dirname(__file__), "assets", "whatsapp_search.png")
                    success, msg = find_and_click(template_path)
                    if success:
                        time.sleep(1)
                        pyautogui.write(contact_name)
                        time.sleep(2)
                        pyautogui.press('enter')
                        if action_type == 'vision_whatsapp_call':
                            time.sleep(1)
                            pyautogui.hotkey('command', 'shift', 'd')
                            await update.message.reply_text(f"📞 Visual WhatsApp Audio Call to {contact_name} Initiated!")
                        else:
                            time.sleep(1)
                            pyautogui.write(message_text)
                            time.sleep(1)
                            pyautogui.press('enter')
                        executed_actions += 1
                    else:
                        fallback_path = os.path.join(os.path.dirname(__file__), "assets", "fallback.png")
                        if os.path.exists(fallback_path):
                            with open(fallback_path, "rb") as photo:
                                await update.message.reply_photo(photo=photo, caption=f"I can't see the Search icon. Ensure assets/whatsapp_search.png is correct. {msg}")
                        failed_actions += 1
                except Exception as e:
                    failed_actions += 1
                    await update.message.reply_text(f"Vision error: {str(e)}")

        if failed_actions > 0:
            await update.message.reply_text(f"⚠️ {failed_actions} step(s) failed or hit an error! I will await your instructions.")
        elif executed_actions > 0:
            await update.message.reply_text("✅ All steps verified and completed!")
                
    except Exception as e:
        err = traceback.format_exc()
        with open("bot_error_live.log", "a") as f:
            f.write(err + "\n")
        err_msg = f"Error: {type(e).__name__} - {str(e)}"
        await update.message.reply_text(err_msg[:4000])

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("postman", postman))
    app.add_handler(CommandHandler("url", url))
    app.add_handler(CommandHandler("call", call_contact))
    app.add_handler(CommandHandler("whatsapp", whatsapp_vision))
    app.add_handler(CommandHandler("ssh", ssh))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Jarvis Telegram Bot is running...")
    app.run_polling()
