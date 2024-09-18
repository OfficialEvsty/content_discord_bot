import os
import shutil

import aiohttp
import discord
import logging

logger = logging.getLogger("app.commands")

async def save_attachment(attachment: discord.Attachment, file_path:str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    with open(file_path, 'wb') as f:
                        f.write(await resp.read())
    except Exception as e:
        logger.error(f"Ошибка во время сохранения скриншота {attachment.filename}: {e}")
    logger.info(f"Файл {attachment.filename} успешно сохранен в директории {file_path}")


async def screenshots_cleaning(directory_path):
    if os.path.exists(directory_path):
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Удаляем и поддиректории с файлами
        logger.debug(f'Все файлы из директории {directory_path} были удалены.')
    else:
        logger.info(f'Директория {directory_path} не существует.')
