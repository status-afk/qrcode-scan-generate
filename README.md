# 📷 QRBeam Bot
 
A Telegram bot for generating and scanning QR codes — including Wi-Fi QR codes and inline mode support.
 
## ✨ Features
 
- **Generate QR codes** from any text or link
- **Scan QR codes** by sending a photo
- **Wi-Fi QR codes** — enter SSID and password, get a scannable QR
- **Inline mode** — use `@qrbeam_bot <text>` in any Telegram chat
- **Admin panel** — stats, broadcast, and direct messaging
 
## 🚀 Usage
 
| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/generate <text>` | Generate a QR code from text or URL |
| `/wifiqr` | Create a Wi-Fi QR code |
| `/help` | Show all commands |
| `/cancel` | Cancel current operation |
 
**Scan a QR code:** Just send a photo containing a QR code — the bot will decode it automatically.
 
**Inline mode:** Type `@qrbeam_bot <text>` in any chat to generate a QR code on the spot.
 
## 🛠️ Tech Stack
 
- **Python**
- **aiogram** — Telegram bot framework
- **qrcode** — QR code generation
- **pyzbar + Pillow** — QR code scanning
- **FSM (Finite State Machine)** — for multi-step conversations
 
## ⚙️ Setup
 
1. Clone the repo
2. Install dependencies:
   ```bash
   pip install aiogram qrcode pyzbar Pillow
   ```
3. Create a `.env` file:
   ```python
   BOT_TOKEN = "your_bot_token_here"
   ```
4. Run the bot:
   ```bash
   python main.py
   ```
 
## 👤 Author
 
Made by [@lol_wave](https://t.me/lolwave)
