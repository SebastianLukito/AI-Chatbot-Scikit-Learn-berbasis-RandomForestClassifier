import string
import time
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from telegram import CallbackQuery
from util import JSONParser
import re as regex
from sympy import *
from sympy import simplify
from collections import deque
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from math import *

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from dotenv import load_dotenv
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.storage import FSMContext
from mystates import MyStates
import random

import os
import logging
import asyncio


logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

last_message = None
last_tag = None
bot_id = None

async def on_startup(dp):
    global bot_id
    bot_id = (await bot.me).id
    
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')

bot = Bot(token=API_TOKEN)

# Initialize dispatcher
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Fungsi dengan memoisasi untuk lematisasi kata
@lru_cache(maxsize=None)
def stem_word(stemmer, word):
    return stemmer.stem(word)

# Fungsi praproses data dengan memoisasi
@lru_cache(maxsize=None)
def preprocess(chat):
    # Konversi ke non kapital
    chat = chat.lower()
    # Hilangkan tanda baca
    translator = str.maketrans('', '', string.punctuation)
    chat = chat.translate(translator)
    # Pecah teks menjadi kata-kata
    chat = chat.split()
    # Lematisasi kata-kata (Menghilangkan imbuhan kata)
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    
    # Paralelisasi lematisasi dengan memoisasi menggunakan list comprehension
    with ThreadPoolExecutor() as executor:
        chat = ' '.join([executor.submit(stem_word, stemmer, word).result() for word in chat])
    
    return chat

# Inisialisasi variabel global
asking_name = False
user_name = None

def bot_therapist_response(chat, user_name):
    # Membuka dan memuat file JSON
    with open('responses.json') as file:
        data = json.load(file)
    
    # Mengambil data dari file JSON
    therapist_responses = data["therapist_responses"]
    default_responses = data["default_responses"]

    # Menemukan pola pertanyaan yang cocok dengan inputan chat dan memberikan respons
    for pattern, responses in therapist_responses.items():
        match = regex.match(pattern, chat)
        if match is not None:
            response = random.choice(responses).format(*match.groups(), name=user_name)
            return response

    # Jika tidak ada pola yang cocok, berikan respons default
    return random.choice(default_responses).format(name=user_name)
    
def format_ribuan(angka):
    if angka == int(angka):  
        angka = int(angka)
        return f"{angka:,}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"{angka:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def replace_operator(match):
    operators = {
        "dikali": "*",
        "kali": "*",
        "x": "*",
        "X": "*",
        "dibagi": "/",
        "bagi": "/",
        ":": "/",
        " : ": "/", 
        "ditambah": "+",
        "tambah": "+",
        "dikurangi": "-",
        "kurang": "-",
        "mod": "%"
    }
    return operators[match.group()]  

def kalkulator(expr):
    try:
        expression = regex.sub(r'\b(?:dikali|kali|[xX]|dibagi|bagi|ditambah|tambah|dikurangi|kurang|mod|:)\b', replace_operator, expr)  
        expression = regex.sub(r'\s+', '', expression)  # Menghapus spasi ekstra
        result = eval(expression)
        result_formatted = format_ribuan(result)
        return f"Hasil dari {expr} adalah {result_formatted}"
    except Exception as e:
        print(e)  # Tambahkan ini untuk melihat kesalahan yang terjadi
        return "Ekspresi matematika tidak valid"

def match_math_expression(chat):
    math_expr = regex.findall(r'\d+\s*(?:dikali|dibagi|ditambah|dikurangi|mod|kali|tambah|kurang|bagi|[xX\/*+\-:])\s*\d+', chat)  # Tambahkan : di sini
    return math_expr
# Membuat struktur data untuk menyimpan 3 pertanyaan terakhir
recent_questions = deque(maxlen=3)

therapist_mode = False  # variabel global untuk mengetahui apakah mode therapist aktif atau tidak

def bot_response(chat, pipeline, jp):
    global recent_questions
    global therapist_mode
    global user_name
    global asking_name
    global therapist_responses
    global default_responses
    recent_questions.append(chat)

    # Membuka dan memuat file JSON
    with open('responses.json') as file:
        data = json.load(file)
    
    # Mengambil data dari file JSON
    therapist_responses = data["therapist_responses"]
    default_responses = data["default_responses"]
    therapist_keywords = data["therapist_keywords"]
    exit_keywords = data["exit_keywords"]

    same_question_count = recent_questions.count(chat)

    if same_question_count == 3:
        return "Kenapa ngomong itu terus sih bang? Sekali lagi dapet piring cantik nih.", None
    else:
        math_expr = match_math_expression(chat)
        if math_expr:
            responses = []
            for expr in math_expr:
                response = kalkulator(expr)
                responses.append(response)

            # Gabungkan semua respons menjadi satu string
            response = ', '.join(responses)
            return response, None
        else:
            if any(keyword in chat.lower() for keyword in therapist_keywords):
                therapist_mode = True
                if user_name is None:
                    asking_name = True
                    return "Hai, sebelumnya aku boleh tau nama kamu?", None
                else:
                    return bot_therapist_response(chat), None

            # Jika mode therapist aktif, gunakan fungsi bot_therapist_response untuk merespons
            elif therapist_mode:
                if asking_name:
                    name_regex = r'(?i)(namaku|nama|aku|saya|gw|nama gw|)\s*:?([a-zA-Z]*)'
                    match = regex.search(name_regex, chat)
                    if match:
                        user_name = match.group(2)  # mengambil grup kedua dari hasil regex, yaitu nama pengguna
                        asking_name = False
                        return "Senang bertemu denganmu, " + user_name + ". Bagaimana aku bisa membantu kamu hari ini?", None
                elif any(keyword in chat.lower() for keyword in exit_keywords):
                    therapist_mode = False
                    user_name = None
                    return "Senang bisa membantumu, "+ user_name + ". Sampai jumpa lagi!", None
                else:
                    return bot_therapist_response(chat), None
            
            else:
                chat = preprocess(chat)
                res = pipeline.predict_proba([chat])
                max_prob = max(res[0])
                if max_prob < 0.15:
                    return "Maaf kak, aku ga ngerti :(", None
                else:
                    max_id = np.argmax(res[0])
                    pred_tag = pipeline.classes_[max_id]
                    return jp.get_response(pred_tag), pred_tag

# Load data
path = "data/intents.json"
jp = JSONParser()
jp.parse(path)
df = jp.get_dataframe()
df['text_input_prep'] = df.text_input.apply(preprocess)

# Pemodelan
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

pipeline = make_pipeline(TfidfVectorizer(ngram_range=(1, 3), min_df=2, max_df=0.9),
                         RandomForestClassifier(n_jobs=3))

# train
print("[INFO] Training Data ...")
pipeline.fit(df.text_input_prep, df.intents)

# save model
with open("model_chatbot.pkl", "wb") as model_file:
    pickle.dump(pipeline, model_file)
    
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("Halo, selamat datang di Jarwo! Saya siap membantu Anda!")

@dp.message_handler(content_types=["text"])
async def text_message_handler(message: types.Message):
    chat_id = message.chat.id
    print(f"Chat ID: {chat_id}")
    global last_message, last_tag
    chat = message.text
    response, pred_tag = bot_response(chat, pipeline, jp)
    last_message = chat
    last_tag = pred_tag
    await bot.send_message(message.chat.id, response)

@dp.message_handler(lambda message: message.reply_to_message and message.text and message.reply_to_message.from_user.id == bot_id(), content_types=types.ContentTypes.TEXT)
async def on_reply(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    current_state = await state.get_state()
    if current_state in [MyStates.waiting_for_context.state, MyStates.waiting_for_fix.state]:
        await state.update_data(response_received=True, response=message.text)
    else:
        # Jika bukan balasan untuk konteks atau respons yang diperbaiki, proses pesan sebagai pesan biasa
        await text_message_handler(message)

if __name__ == '__main__':
    from aiogram import executor
    logger.info("[INFO] Bot is running ...")
    try:
        executor.start_polling(dp, on_startup=on_startup)
    except Exception as e:
        logger.error("Error occurred: %s", str(e))