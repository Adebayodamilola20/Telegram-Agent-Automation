# Jarvis Telegram Bot - MacOS Automation

![GitHub License](https://img.shields.io/github/license/Adebayodamilola20/Telegram-Agent-Automation?style=flat-square)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square)
![GitHub Stars](https://img.shields.io/github/stars/Adebayodamilola20/Telegram-Agent-Automation?style=flat-square)
![GitHub Forks](https://img.shields.io/github/forks/Adebayodamilola20/Telegram-Agent-Automation?style=flat-square)
![GitHub Issues](https://img.shields.io/github/issues/Adebayodamilola20/Telegram-Agent-Automation?style=flat-square)
![Last Commit](https://img.shields.io/github/last-commit/Adebayodamilola20/Telegram-Agent-Automation?style=flat-square)

A powerful, LLM-driven MacOS automation system controlled via Telegram. Inspired by Iron Man's Jarvis, this bot allows you to remotely control your Mac using natural language, execute shell commands, run AppleScripts, and even perform vision-based automation for apps like WhatsApp.

## 🚀 Features

- **Natural Language Processing**: Powered by Mistral AI to understand and execute complex requests.
- **Vision-Based Automation**: Uses OpenCV and PyAutoGUI to "see" and interact with UI elements (e.g., searching contacts in WhatsApp).
- **System Control**: Open applications, URLs, and perform system tasks via AppleScript.
- **Remote Shell**: Execute bash commands directly from Telegram with output feedback.
- **Secure Access**: Restricted to authorized Telegram IDs only.

## 🛠️ Setup

### Prerequisites

- MacOS (for AppleScript and system automation support)
- Python 3.12+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Mistral AI API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/adebayodamilola20/jarvis-telegram-bot.git
   cd jarvis-telegram-bot
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory and add your keys:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   ALLOWED_TELEGRAM_ID=your_telegram_user_id
   MISTRAL_API_KEY=your_mistral_api_key
   ```

## 📖 Usage

Run the bot:
```bash
python3 bot.py
```

### Commands

- `/start`: Initialize connection.
- `/whatsapp [contact] [message]`: Send a WhatsApp message using vision automation.
- `/call [contact]`: Make a WhatsApp audio call.
- `/url [link]`: Open a URL in Chrome.
- `/postman`: Open Postman.
- `/ssh [command]`: Run a shell command.
- **Natural Language**: Just type anything (e.g., "Open Spotify and play some jazz") and Jarvis will handle it.

## ⚠️ Security Note

Ensure your `.env` file is **never** committed to version control. The included `.gitignore` is pre-configured to protect your secrets.

## 📄 License

MIT License. See `LICENSE` for details.
