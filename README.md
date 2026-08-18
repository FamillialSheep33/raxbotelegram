##Raxbotelegram
A Telegram bot developed in Python with Pyrogram designed to automatically download audio files and documents directly to a server's local storage, verify transfer integrity, manage retries via an asynchronous queue, and provide a secure remote shutdown mechanism for the host system.
---

## Features
* **Audio & Document Ingestion:** Handles private chat file uploads up to 2 GB.
* **Access Control:** Whitelist-based access restricted to specific Telegram usernames.
* **Integrity Verification:** Compares the downloaded file size in bytes against the expected Telegram file metadata (file_size).
* **Asynchronous Retry Queue:** Automatically pushes failed downloads (after 3 initial attempts) to a background queue (asyncio.Queue) for scheduled re-processing.
* **Activity Logging:** Writes a persistent timestamped history of successful downloads, errors, and retry attempts.
* **Remote Host Shutdown:** Executes a remote system power-off using nsenter via the /apagar command.
---

## Requirements
* Python 3.8+
* Telegram API Credentials:
  * API_ID and API_HASH (obtainable at my.telegram.org)
  * BOT_TOKEN (created via @BotFather)
* Superuser / Privileged container permissions (required only for the /apagar remote shutdown feature).
---

## Installation
1. Clone the repository:
   git clone https://github.com/your-username/your-repository.git
   cd your-repository
2. Install dependencies:
   pip install pyrogram tgcrypto

---
## Configuration
Set your environment configuration inside the main script:
# --- CONFIGURATION ---
RUTA_DESCARGA = "/music/"                     # Target download directory
ARCHIVO_LOG = "/app/logs/descargas_musica.log" # Log output path
USUARIO_PERMITIDO = "user"                    # Primary authorized username (without @)
USUARIO_PERMITIDO2 = "user2"                  # Secondary authorized username (without @)
API_ID = "your_api_id"                        # Telegram API ID
API_HASH = "your_api_hash"                    # Telegram API Hash
BOT_TOKEN = "your_bot_token"                  # Telegram Bot Token
---

## Usage
Run the bot directly:
python3 raxbottelegram.py

### Commands and Actions
| Command / Action | Description | Access Level |
| :--- | :--- | :--- |
| /start | Displays bot status and current download path. | Public |
| /apagar | Executes a host shutdown (nsenter poweroff). | Authorized Users Only |
| Send Audio/Document | Downloads, verifies, and stores the file in the target directory. | Authorized Users Only |
---

## Retry Queue Workflow
Incoming File
       │
       ▼
[Direct Download] ───► (Up to 3 attempts with a 10s delay)
       │
       ├──► Success ──► Verify file size ──► Save to RUTA_DESCARGA
       │
       └──► Failure ──► Enqueue into COLA_REINTENTOS
                             │
                             ▼
              [Async Background Worker (every 60s)]
                             │
                             ▼
              [Queue Retry] ───► (Up to 6 attempts)
                             │
                             ├──► Success ──► Save to RUTA_DESCARGA
                             └──► Failure ──► Log permanent failure & notify user

---
## Log Format

Events are logged with standard timestamps:

YYYY-MM-DD HH:MM:SS - Downloaded correctly: audio.flac
YYYY-MM-DD HH:MM:SS - Error on try 1/3: [Error details]
YYYY-MM-DD HH:MM:SS - added to the query: track.mp3

## What I Learned

Developing RaxSounds provided practical experience building resilient asynchronous Python applications and server automations:
Working with asynchronous Python using asyncio and Pyrogram[cite: 1]
Designing producer-consumer patterns using asyncio.Queue[cite: 1]
Verifying file integrity during network streaming[cite: 1]
Managing container-to-host system interactions using nsenter[cite: 1]
Structuring error-handling and automated retry policies[cite: 1]
Writing event logs for background daemons[cite: 1]
---
## 👨‍💻 Author
**Angel Edell **

IT & Digital Innovation Engineering Student

Interested in:

* Linux
* Backend Development
* DevOps
* Infrastructure
* Networking
* Automation
* Open Source

GitHub: **[@FamillialSheep33](https://github.com/FamillialSheep33)**

---

## License

This project is primarily intended as an educational and portfolio project.


