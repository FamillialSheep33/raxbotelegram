#!/usr/bin/env python3

import os
from pyrogram import Client, filters
from pyrogram.types import Message
import datetime
import asyncio
import subprocess

# --- CONFIGURACIÓN ---
RUTA_DESCARGA = "/music/"
ARCHIVO_LOG = "/app/logs/descargas_musica.log"
USUARIO_PERMITIDO = "user"
USUARIO_PERMITIDO2 = "user2"
API_ID = "private"        # your api id from telegram
API_HASH = "private"              # your telegram api hash
BOT_TOKEN = "private"             # your telegram bot token

# retrys for each download ---
MAX_REINTENTOS_INDIVIDUAL = 3
TIEMPO_ENTRE_REINTENTOS_INDIVIDUAL_SEGS = 10

# general retry queque
COLA_REINTENTOS = asyncio.Queue()
TIEMPO_ENTRE_VERIFICACION_COLA_SEGS = 60

# startup
app = Client("descarga_musica_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

#functions
def registrar_descarga(nombre_archivo, estado="Downloaded"):
    """show the download on the logfile"""
    os.makedirs(os.path.dirname(ARCHIVO_LOG), exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ARCHIVO_LOG, "a") as archivo_log:
        archivo_log.write(f"{timestamp} - {estado}: {nombre_archivo}\n")

async def descargar_y_verificar(client: Client, message: Message, archivo_data: dict, es_reintento_cola=False):
    """
    auxiliar function to check and retry a single file
    """
    nombre_archivo = archivo_data['nombre_archivo']
    total_size = archivo_data['total_size']
    original_message = archivo_data['message']

    intentos_actuales = 0
    max_intentos = MAX_REINTENTOS_INDIVIDUAL if not es_reintento_cola else MAX_REINTENTOS_INDIVIDUAL * 2

    while intentos_actuales < max_intentos:
        try:
            ruta_descarga_completa = os.path.join(RUTA_DESCARGA, nombre_archivo)
            os.makedirs(RUTA_DESCARGA, exist_ok=True)

            print(f"[{'Retry queque' if es_reintento_cola else 'Direct download'}] trying to  download '{nombre_archivo}' (Try {intentos_actuales + 1}/{max_intentos})")
            downloaded_file_path = await client.download_media(original_message, file_name=ruta_descarga_completa)

            if downloaded_file_path and os.path.exists(downloaded_file_path):
                actual_size = os.path.getsize(downloaded_file_path)
                if actual_size == total_size:
                    registrar_descarga(nombre_archivo, "Downloaded correctly")
                    await original_message.reply_text(f"File '{nombre_archivo}' downloaded on {RUTA_DESCARGA}.")
                    return True
                else:
                    if os.path.exists(downloaded_file_path):
                        os.remove(downloaded_file_path)
                    raise Exception(f"Download incomplete. Expected size: {total_size}, Real Size: {actual_size}")
            else:
                raise Exception("the download didnt responded with a valid route.")

        except Exception as e:
            intentos_actuales += 1
            registro_estado = f"Error on try {intentos_actuales}/{max_intentos}"
            print(f"{registro_estado} for '{nombre_archivo}': {e}")
            registrar_descarga(nombre_archivo, f"{registro_estado}: {e}")

            if intentos_actuales < max_intentos:
                await asyncio.sleep(TIEMPO_ENTRE_REINTENTOS_INDIVIDUAL_SEGS)
            else:
                print(f"[{'Retry queque' if es_reintento_cola else 'direct download'}] Final failure for '{nombre_archivo}' After {max_intentos} atempts.")
                return False

    return False

@app.on_message(filters.command("start"))
async def comando_start(client: Client, message: Message):
    """manage the start command."""
    await message.reply_text(f"Hello, {message.from_user.username}!this bot downloads files on {RUTA_DESCARGA} (With capacity of 2GB).")

@app.on_message(filters.command("apagar"))
async def comando_apagar(client: Client, message: Message):
    """Maneja el comando /apagar para apagar el servidor."""
    if message.from_user.username == USUARIO_PERMITIDO or message.from_user.username == USUARIO_PERMITIDO2:
        await message.reply_text("¡Starting shutdown of the server")
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Comando /apagar recibido de {message.from_user.username}. Turning down server.")
        await asyncio.sleep(2)
        try:
            subprocess.run(["nsenter", "-t", "1", "-m", "-u", "-i", "-n", "poweroff"], check=True)
        except subprocess.CalledProcessError as e:
            await message.reply_text(f"Error shutting down: {e}")
            print(f"Error shutdown: {e}")
        except Exception as e:
            await message.reply_text(f"Error shutting down: {e}")
            print(f"Error shutdown: {e}")
    else:
        await message.reply_text("Sorry, you dont have access for shutdown the server.")
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] shutdown attempt denied for  {message.from_user.username}.")

@app.on_message(filters.private & (filters.document | filters.audio))
async def manejar_archivos(client: Client, message: Message):
    """manages file and audio treatment"""
    if message.from_user.username == USUARIO_PERMITIDO or message.from_user.username == USUARIO_PERMITIDO2:
        try:
            if message.document:
                archivo = message.document
            elif message.audio:
                archivo = message.audio
            else:
                await message.reply_text("File type not supported.")
                return

            nombre_archivo = archivo.file_name if archivo.file_name else f"sin_nombre_{archivo.file_id}.flac"
            total_size = archivo.file_size

            archivo_data = {
                'message': message,
                'nombre_archivo': nombre_archivo,
                'total_size': total_size
            }

            if not await descargar_y_verificar(client, message, archivo_data, es_reintento_cola=False):
                await COLA_REINTENTOS.put(archivo_data)
                await message.reply_text(f"the first download for '{nombre_archivo}' failed. added to the query.")
                registrar_descarga(nombre_archivo, "added to the query")

        except Exception as e:
            await message.reply_text(f"an error occured during the download of the file: {e}")
            print(f"Error managing the file: {e}")
    else:
        await message.reply_text("sorry, you dont have permission to use this bot")

async def procesar_cola_reintentos():
    """Tarea asíncrona para procesar la cola de reintentos."""
    while True:
        await asyncio.sleep(TIEMPO_ENTRE_VERIFICACION_COLA_SEGS)
        print(f"checking retries query... ({COLA_REINTENTOS.qsize()} elements)")
        while not COLA_REINTENTOS.empty():
            archivo_data = await COLA_REINTENTOS.get()
            nombre_archivo = archivo_data['nombre_archivo']
            print(f"Retry download for '{nombre_archivo}' from the query.")

            if await descargar_y_verificar(app, archivo_data['message'], archivo_data, es_reintento_cola=True):
                print(f"'{nombre_archivo}' correctly downloaded from the query.")
            else:
                registrar_descarga(nombre_archivo, "Permanent failure from the query")
                await archivo_data['message'].reply_text(f"The download for '{nombre_archivo}' ha has permamemtly failed")


# bot startup
async def main():
    await app.start()
    print("the bot is listening")
    asyncio.get_event_loop().create_task(procesar_cola_reintentos())
    await asyncio.Event().wait()

if __name__ == '__main__':
    app.run(main())
