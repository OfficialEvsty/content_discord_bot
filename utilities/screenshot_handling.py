import io
import json
import os
import uuid

import cv2
import discord
import easyocr
import re

import numpy as np

from utilities.ingame_entities import ATag
import logging

logger = logging.getLogger("app.utilities")

# Функция для проверки, содержит ли строка больше 1 заглавной буквы
def has_more_than_one_uppercase(line):
    uppercase_count = sum(1 for char in line if char.isupper())
    return uppercase_count > 1

# Удаляем строки, которые содержат больше 1 заглавной буквы

def clean_and_split(data):
    cleaned = []
    for bbox, text, confidence in data:
        # Удаляем специальные символы с помощью регулярного выражения
        cleaned_text = re.sub(r'[^\w\s]', '', text)
        cleaned_text = cleaned_text.replace('_', '')
        cleaned_text = cleaned_text.replace(' ', '')
        if not has_more_than_one_uppercase(cleaned_text) and len(cleaned_text) > 1:
            cleaned.append([bbox, cleaned_text, confidence])
    return cleaned

# Upscaling image with AI
async def enchant_image(image_path, model_type, model_path, scale, image_output_path):
    try:
        img = cv2.imread(image_path)

        # Создаём sr-объект
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        # Считываем модель
        path = model_path
        sr.readModel(path)

        # Устанавливаем модель и масштаб
        sr.setModel(model_type, scale)

        # Улучшаем
        result = sr.upsample(img)

        # Сохраняем
        cv2.imwrite(image_output_path, result)

        logger.info(
            f"Качество файла {img} было улучшено при помощи ИИ-модели {model_type} с scale {scale}")
    except Exception as e:
        logger.error(f"Ошибка при попытке улучшить качество изображения {img} при помощи ИИ-модели {model_type} с scale {scale}: {e}")


async def recognize_nicknames_on_image(lang_list, image_to_recognize, nicknames):
    directory_path = "/app/images"  # Измените на ваш путь

    # Получаем список файлов и папок
    files = os.listdir(directory_path)
    print(f"Файлы в: {files}")
    reader = easyocr.Reader(lang_list)
    data = reader.readtext(image_to_recognize)

    similar_letters = None
    with open("utilities/similar_letters.json", encoding='utf-8') as file:
        similar_letters = json.load(file)

    proceed_words = clean_and_split(data)
    print(proceed_words)
    visited_members = []
    for bbox, substring, confidence in proceed_words:

        pattern = f"^{re.escape(substring)}"

        occurrences = find_nicknames_by_predicate(pattern, visited_members, nicknames)
        if len(occurrences) == 0 and similar_letters is not None:
            rus, eng = translate_substring_to_similar_lang(similar_letters, substring)
            for substr in [rus, eng]:
                if substr:
                    print(f"{substr} skip")
                    continue
                print(f"{substr} proccess")
                translate_pattern = f"^{re.escape(substr)}"
                occurrences = find_nicknames_by_predicate(translate_pattern, visited_members, nicknames)

                if len(occurrences) > 0:
                    visited_members.append([occurrences, get_nickname_box_image(image_to_recognize, bbox)])

    # Отдельно обработать n колизии с n совпадающими никами
    for i in range(len(visited_members)):
        if len(visited_members[i][0]) < 2:
            continue
        count = 1
        pos = [i]
        for j in range(i + 1, len(visited_members)):

            if len(visited_members[j][0]) < 2:
                continue
            if len(set(visited_members[i][0]) ^ set(visited_members[j][0])) == 0:
                count += 1
                pos.append(j)
                if len(visited_members[i][0]) == count:
                    for p in pos:
                        visited_members[p][0] = [visited_members[p][0][count - 1]]
                        count -= 1
                    break

    print(visited_members)
    return visited_members

def find_nicknames_by_predicate(pattern, visited_members, nicknames) -> []:
    occurrence_list = []
    for nickname in nicknames:
        if nickname in sum(visited_members, []):
            continue
        if re.match(pattern, nickname):
            occurrence_list.append(nickname)
    return occurrence_list


def translate_substring_to_similar_lang(similar: dict, substring) -> ():
    def is_russian(text):
        return all('А' <= char <= 'я' or char == 'ё' for char in text)

    def is_english(text):
        return all('A' <= char <= 'Z' or 'a' <= char <= 'z' for char in text)

    translate_rus_substring = ""
    translate_eng_substring = ""
    for char in substring:
        for char_rus, char_eng in similar.items():
            if char == char_rus:
                translate_eng_substring += char_eng
            elif char == char_eng:
                translate_rus_substring += char_rus

    if len(translate_rus_substring) > 0 and len(translate_eng_substring) > 0:
        return translate_rus_substring, translate_eng_substring
    if len(translate_eng_substring) > 0:
        return None, translate_eng_substring
    if len(translate_rus_substring) > 0:
        return  translate_rus_substring, None

    else:
        try:
            raise Exception("Язык для перевода не поддерживается или язык подстроки неоднороден")
        except Exception as e:
            logger.debug(e)


def get_nickname_box_image(img_path, bbox):
    img = cv2.imread(img_path)
    x, y, w, h = int(bbox[0][0]), int(bbox[0][1]), int(bbox[2][0]-bbox[0][0]), int(bbox[2][1]-bbox[0][1])
    img_box = img[y:y+h, x:x+w]

    resized_img_box = cv2.resize(img_box, [img_box.shape[0]*6, img_box.shape[1]*3], interpolation=cv2.INTER_LINEAR)

    buf = io.BytesIO()
    # Кодируем изображение в формате PNG
    _, encoded_img = cv2.imencode('.png', resized_img_box)
    buf.write(encoded_img.tobytes())
    buf.seek(0)
    file = discord.File(fp=buf, filename=f"{uuid.uuid4().hex}.png")
    return file
