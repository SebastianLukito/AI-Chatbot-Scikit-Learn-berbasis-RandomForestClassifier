import string
import pickle
import numpy as np
from sklearn.pipeline import make_pipeline
from util import JSONParser
import re as regex
from sympy import *
from collections import deque
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from math import *

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from dotenv import load_dotenv
from mystates import MyStates
import random

import os
import logging


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

def bot_therapist_response(chat):
    global asking_name
    global user_name
    # Pola pertanyaan dan tanggapan
    therapist_responses = {
    r'aku merasa (.*)': [
        'Kenapa kamu merasa {0}, ' + user_name + '?',
        'Apa yang membuat kamu merasa {0}, ' + user_name + '?',
        'Berapa lama kamu merasa {0}, ' + user_name + '?'],
    r'apa yang membuatku merasa (.*)': [
        'Apakah ada hal atau situasi tertentu yang membuat kamu merasa {0}, ' + user_name + '?',
        'Apakah kamu bisa menjelaskan lebih detail mengenai faktor-faktor yang mempengaruhi perasaanmu {0}, ' + user_name + '?'],
    r'kenapa aku merasa (.*)': [
        'Apakah ada alasan spesifik mengapa kamu merasa {0}, ' + user_name + '?',
        'Apakah ada peristiwa atau perubahan dalam hidupmu yang berhubungan dengan perasaan {0}, ' + user_name + 'mu?'],
    r'mengapa (.*)': [
        'Apakah kamu yakin bahwa {0}, ' + user_name + '?',
        'Apa sebenarnya yang kamu tanyakan, apakah ada pertanyaan lain, ' + user_name + '?',
        'Apakah pertanyaan tersebut sangat penting buat kamu, ' + user_name + '?'],
    r'apa sebenarnya yang aku rasakan': [
        'Penting bagi kamu, ' + user_name + ', untuk menyadari dan mengakui perasaanmu sendiri. Apa yang membuatmu bingung tentang perasaanmu?',
        'Mungkin kamu bisa mencoba merenung sejenak dan mengidentifikasi perasaan yang ada dalam dirimu, ' + user_name + '.'],
    r'aku (.*) kamu': [
        'Bicarakan lebih lanjut mengenai perasaanmu terhadap saya, ' + user_name + '.',
        'Apakah ada hal khusus yang membuatmu merasa demikian terhadap saya, ' + user_name + '?'],
    r'apa yang harus aku lakukan': [
        'Pertanyaan itu mungkin tergantung pada situasinya, ' + user_name + '. Bisakah kamu memberikan lebih banyak konteks atau detail?',
        'Pertama-tama, cobalah untuk tenang dan mengevaluasi situasinya dengan objektif, ' + user_name + '. Setelah itu, kamu dapat membuat keputusan yang lebih baik.'],
    r'apa yang harus aku lakukan jika (.*)': [
        'Setiap situasi memiliki cara yang berbeda untuk ditangani, ' + user_name + '. Bisakah kamu memberikan lebih banyak informasi tentang situasi tersebut?',
        'Penting untuk mempertimbangkan konteks dan konsekuensi sebelum membuat keputusan, ' + user_name + '. Ceritakan lebih banyak tentang situasinya.'],
    r'aku sedang jatuh cinta dengan (.*)': [
        'Bagaimana perasaanmu ketika berada di dekat {0}, ' + user_name + '?',
        'Apa yang membuatmu tertarik pada {0}, ' + user_name + '?',
        'Ceritakan lebih banyak tentang perasaan cintamu terhadap {0}, ' + user_name + '.'],
    r'aku lagi naksir sama (.*)': [
        'Apa yang menarik dari {0} yang membuatmu naksir, ' + user_name + '?',
        'Apakah kamu pernah mencoba berinteraksi dengan {0} secara langsung, ' + user_name + '?',
        'Bagaimana perasaanmu ketika melihat {0}, ' + user_name + '?'],
    r'aku lagi jatuh cinta sama (.*)': [
        'Apakah {0} menyadari perasaanmu, ' + user_name + '?',
        'Apa yang membuatmu jatuh cinta pada {0}, ' + user_name + '?',
        'Bagaimana perasaanmu ketika berpikir tentang {0}, ' + user_name + '?'],
    r'gw suka banget sama (.*)': [
        'Apa yang membuatmu suka banget dengan {0}, ' + user_name + '?',
        'Apakah kamu berharap untuk memiliki hubungan khusus dengan {0}, ' + user_name + '?',
        'Ceritakan lebih banyak tentang perasaan suka bangetmu terhadap {0}, ' + user_name + '.'],
    r'gw naksir banget sama (.*)': [
        'Apakah kamu memiliki kesempatan untuk berbicara atau berteman dengan {0}, ' + user_name + '?',
        'Apa yang paling menarik dari {0} yang membuatmu naksir banget, ' + user_name + '?',
        'Bagaimana perasaanmu ketika melihat {0}, ' + user_name + '?'],
    r'saya (.*)': [
        'Ceritakan lebih lanjut tentang pengalamanmu sebagai {0}, ' + user_name + '.',
        'Apa yang membuatmu merasa {0}, ' + user_name + '?',
        'Bagaimana perasaanmu ketika menjadi {0}, ' + user_name + '?',
        'Berapa lama kamu merasa {0}, ' + user_name + '?'],
    r'saya sedang (.*)': [
        'Apakah ada alasan khusus mengapa kamu sedang {0}, ' + user_name + '?',
        'Bagaimana perasaanmu ketika sedang {0}, ' + user_name + '?',
        'Apa yang membuatmu merasa {0} saat ini, ' + user_name + '?',
        'Berapa lama kamu merasa {0}, ' + user_name + '?'],
    r'aku sedang (.*)': [
        'Bagaimana perasaanmu ketika sedang {0}, ' + user_name + '?',
        'Apakah ada hal yang mempengaruhi perasaan {0}mu, ' + user_name + '?',
        'Ceritakan lebih banyak tentang pengalamanmu saat sedang {0}, ' + user_name + '.',
        'Berapa lama kamu merasa {0}, ' + user_name + '?'],
    r'gw lagi (.*)': [
        'Apa yang membuatmu sedang {0}, ' + user_name + '?',
        'Bagaimana perasaanmu ketika lagi {0}, ' + user_name + '?',
        'Ceritakan lebih lanjut tentang pengalamanmu saat lagi {0}, ' + user_name + '.',
        'Berapa lama kamu merasa {0}, ' + user_name + '?'],
    r'saya lagi (.*)': [
        'Apakah ada alasan tertentu mengapa kamu lagi {0}, ' + user_name + '?',
        'Bagaimana perasaanmu ketika lagi {0}, ' + user_name + '?',
        'Apa yang membuatmu merasa {0} saat ini, ' + user_name + '?',
        'Berapa lama kamu merasa {0}, ' + user_name + '?'],
    r'aku lagi (.*)': [
        'Bagaimana perasaanmu ketika lagi {0}, ' + user_name + '?',
        'Apakah ada faktor yang berkontribusi pada perasaan {0}mu, ' + user_name + '?',
        'Ceritakan lebih banyak tentang pengalamanmu saat lagi {0}, ' + user_name + '.',
        'Berapa lama kamu merasa {0}, ' + user_name + '?'],
    r'nggak tau kenapa (.*)': [
        'Mungkin kamu perlu sedikit waktu untuk merenung dan memahami perasaanmu terhadap {0}, ' + user_name + '.',
        'Tidak apa-apa jika kamu tidak tahu alasan pasti, tapi coba perhatikan perasaanmu ketika berada di sekitar {0}, ' + user_name + '.',
        'Terkadang, kita tidak tahu dengan pasti mengapa kita merasakan sesuatu. Bagaimana perasaanmu ketika memikirkan {0}, ' + user_name + '?'],
    r'gak tau kenapa merasa (.*)': [
        'Mungkin kamu bisa mencoba mengidentifikasi situasi atau faktor-faktor tertentu yang mungkin mempengaruhi perasaanmu terhadap {0}, ' + user_name + '.',
        'Tidak apa-apa jika kamu tidak mengetahui alasan pasti. Cobalah untuk menjelajahi perasaanmu lebih dalam saat berada di sekitar {0}, ' + user_name + '.',
        'Kadang-kadang, perasaan datang tanpa alasan yang jelas. Bagaimana perasaanmu ketika memikirkan {0}, ' + user_name + '?'],
    r'gak tau': [
        'Mungkin kamu bisa merenung sejenak untuk mencari tahu apa yang sedang kamu rasakan atau alasan di balik perasaanmu, ' + user_name + '.',
        'Tidak apa-apa jika kamu tidak tahu, tapi cobalah untuk lebih memahami perasaanmu dengan mengamati situasi atau faktor-faktor yang mungkin mempengaruhinya.',
        'Terkadang, perasaan kita membutuhkan waktu untuk dipahami. Bagaimana kamu menggambarkan perasaanmu saat ini, ' + user_name + '?'],
    r'lagi (.*) aja': [
        'Apa yang membuatmu memilih untuk tetap {0}, ' + user_name + '?',
        'Apakah ada alasan khusus yang membuatmu memilih untuk terus {0}, ' + user_name + '?',
        'Bagaimana perasaanmu ketika sedang {0}, ' + user_name + '?'],
    r'nggak tau': [
        'Jika kamu merasa bingung, mungkin kamu bisa mencoba merenung sejenak dan mencari tahu apa yang sedang kamu rasakan, ' + user_name + '.',
        'Tidak apa-apa jika kamu tidak tahu, tapi cobalah untuk lebih memahami perasaanmu dengan mengamati situasi atau faktor-faktor yang mungkin mempengaruhinya.',
        'Kadang-kadang, kita membutuhkan waktu untuk memahami perasaan kita dengan lebih baik. Bagaimana kamu menggambarkan perasaanmu saat ini, ' + user_name + '?'],
    r'tidak mau': [
        'Baik, jika kamu tidak ingin bercerita lebih banyak, itu tidak masalah, ' + user_name + '. Apakah ada hal lain yang ingin kamu diskusikan?',
        'Jika kamu tidak ingin membicarakannya, tidak masalah. Apakah ada topik lain yang ingin kamu ajukan?',
        'Tidak apa-apa jika kamu tidak mau bercerita lebih banyak. Apakah ada hal lain yang ingin kamu sampaikan atau diskusikan?'],
    r'gak mau': [
        'Baik, jika kamu tidak mau, itu tidak masalah, ' + user_name + '. Apakah ada hal lain yang ingin kamu diskusikan?',
        'Jika kamu tidak mau, tidak masalah. Apakah ada topik lain yang ingin kamu ajukan?',
        'Tidak apa-apa jika kamu tidak mau. Apakah ada hal lain yang ingin kamu sampaikan atau diskusikan?'],
    r'gak': [
        'Jika kamu tidak ingin, itu tidak masalah, ' + user_name + '. Apakah ada hal lain yang ingin kamu diskusikan?',
        'Jika kamu tidak ingin, tidak masalah. Apakah ada topik lain yang ingin kamu ajukan?',
        'Tidak apa-apa jika kamu tidak ingin. Apakah ada hal lain yang ingin kamu sampaikan atau diskusikan?'],
    r'nggak': [
        'Baik, jika kamu nggak ingin, itu tidak masalah, ' + user_name + '. Apakah ada hal lain yang ingin kamu diskusikan?',
        'Jika kamu nggak ingin, tidak masalah. Apakah ada topik lain yang ingin kamu ajukan?',
        'Tidak apa-apa jika kamu nggak ingin. Apakah ada hal lain yang ingin kamu sampaikan atau diskusikan?'],
    r'tidak': [
        'Jika kamu tidak ingin, itu tidak masalah, ' + user_name + '. Apakah ada hal lain yang ingin kamu diskusikan?',
        'Jika kamu tidak ingin, tidak masalah. Apakah ada topik lain yang ingin kamu ajukan?',
        'Tidak apa-apa jika kamu tidak ingin. Apakah ada hal lain yang ingin kamu sampaikan atau diskusikan?'],
    r'aku (.*) sekali': [
        'Bagaimana perasaanmu saat menjadi {0} sekali, ' + user_name + '?',
        'Apa yang membuatmu merasa sangat {0}, ' + user_name + '?',
        'Ceritakan lebih banyak tentang perasaanmu yang sangat {0}, ' + user_name + '.'],
    r'saya (.*) sekali': [
        'Apa yang membuatmu jadi {0} sekali, ' + user_name + '?',
        'Apa yang membuatmu merasa sangat {0}, ' + user_name + '?',
        'Ceritakan lebih banyak tentang perasaanmu yang sangat {0}, ' + user_name + '.'],
    r'aku (.*) banget': [
        'Apa yang membuatmu merasa sangat {0}, ' + user_name + '?',
        'Bagaimana perasaanmu ketika menjadi {0} banget, ' + user_name + '?',
        'Ceritakan lebih banyak tentang perasaanmu yang sangat {0}, ' + user_name + '.'],
    r'saya (.*) banget': [
        'Apa yang membuatmu merasa sangat {0}, ' + user_name + '?',
        'Bagaimana perasaanmu ketika menjadi {0} banget, ' + user_name + '?',
        'Ceritakan lebih banyak tentang perasaanmu yang sangat {0}, ' + user_name + '.'],
    r'aku tadi dijahati oleh (.*)': [
        'Itu pasti pengalaman yang sulit, ' + user_name + '. Bagaimana kamu merasa setelah dijahati oleh {0}?',
        'Apa yang membuatmu merasa dijahati oleh {0}, ' + user_name + '?',
        'Ceritakan lebih banyak tentang pengalamanmu ketika dijahati oleh {0}, ' + user_name + '.'],
    r'aku tadi dijahati sama (.*)': [
        'Itu pasti pengalaman yang sulit, ' + user_name + '. Bagaimana kamu merasa setelah dijahati oleh {0}?',
        'Apa yang membuatmu merasa dijahati oleh {0}, ' + user_name + '?',
        'Ceritakan lebih banyak tentang pengalamanmu ketika dijahati oleh {0}, ' + user_name + '.'],
    r'aku tadi melihat (.*)': [
        'Bagaimana perasaanmu setelah melihat {0}, ' + user_name + '?',
        'Apakah melihat {0} mempengaruhi emosimu, ' + user_name + '?',
        'Ceritakan lebih banyak tentang pengalamanmu ketika melihat {0}, ' + user_name + '.'],
    r'aku tadi lihat (.*) di kamar mandi': [
        'Itu pasti pengalaman yang mengejutkan, ' + user_name + '. Bagaimana kamu merasa setelah melihat {0} di kamar mandi?',
        'Apa yang ada dalam pikiranmu saat melihat {0} di kamar mandi, ' + user_name + '?',
        'Ceritakan lebih banyak tentang pengalamanmu saat melihat {0} di kamar mandi, ' + user_name + '.'],
    r'ya aku (.*)': [
        'Maaf jika ada yang membuatmu kesal, ' + user_name + '. Bagaimana saya bisa membantu kamu dalam hal ini?',
        'Apa yang membuatmu merasa seperti itu, ' + user_name + '?',
        'Ceritakan lebih lanjut tentang perasaanmu saat menjadi {0}, ' + user_name + '.'],
    r'ya gw (.*)': [
        'Maaf jika ada yang membuatmu kesal, ' + user_name + '. Apakah ada yang bisa saya bantu?',
        'Apa yang membuatmu merasa seperti itu, ' + user_name + '?',
        'Ceritakan lebih lanjut tentang perasaanmu saat menjadi {0}, ' + user_name + '.'],
    r'ya begitulah': [
        'Saya minta maaf jika ada yang membuatmu kesal, ' + user_name + '. Apakah ada yang bisa saya bantu?',
        'Apa yang membuatmu merasa seperti itu, ' + user_name + '?',
        'Ceritakan lebih lanjut tentang perasaanmu saat mengatakan begitu, ' + user_name + '.'],
    r'yagitu': [
        'Maaf jika ada yang membuatmu kesal, ' + user_name + '. Apakah ada yang bisa saya bantu?',
        'Apa yang membuatmu merasa seperti itu, ' + user_name + '?',
        'Ceritakan lebih lanjut tentang perasaanmu saat mengatakan begitu, ' + user_name + '.'],
    r'ya gitu': [
        'Saya minta maaf jika ada yang membuatmu kesal, ' + user_name + '. Bagaimana saya bisa membantu kamu?',
        'Apa yang membuatmu merasa seperti itu, ' + user_name + '?',
        'Ceritakan lebih lanjut tentang perasaanmu saat mengatakan begitu, ' + user_name + '.'],
    r'bodo amat lah': [
        'Maaf jika ada yang membuatmu kesal, ' + user_name + '. Apakah ada yang bisa saya bantu?',
        'Bagaimana saya bisa membantu kamu, ' + user_name + '?',
        'Ceritakan lebih lanjut tentang perasaanmu saat mengatakan begitu.'],
    r'hahaha': [
        'Maaf jika ada yang membuatmu kesal, ' + user_name + '. Apakah ada yang bisa saya bantu?',
        'Saya minta maaf jika ada yang tidak lucu. Apakah ada yang ingin kamu sampaikan atau diskusikan, ' + user_name + '?'],
    r'karena (.*)': [
        'Mengapa {0} membuatmu merasa seperti itu, ' + user_name + '?',
        'Bagaimana perasaanmu ketika mengalami {0}?',
        'Ceritakan lebih lanjut tentang hubungan antara {0} dan perasaanmu, ' + user_name + '.'],
    r'aku (.*) aja, mau ku-(.*) orang itu': [
        'Hm, perasaanmu terhadap {0} sangat kuat, ' + user_name + '. Namun, penting untuk menjaga keamanan dan menyelesaikan masalah dengan cara yang positif dan damai. Apakah ada cara lain yang bisa kamu pilih untuk mengatasi masalah ini?',
        'Saya mengerti bahwa kamu merasa ingin membalas dendam terhadap {1} karena {0}. Namun, penting untuk diingat bahwa balas dendam seringkali tidak membawa kebahagiaan jangka panjang. Apakah ada cara lain untuk menyelesaikan masalah ini tanpa kekerasan?',
        'Aku mendengar keinginanmu untuk membalas dendam terhadap {1} karena {0}. Namun, marilah kita mencari cara yang lebih positif untuk menyelesaikan masalah ini. Bagaimana pendapatmu?'],
    r'(?:aku )?(?:mau curhat|butuh teman curhat|pengen curhat|ingin curhat|curhat dong|curcol dong)': [
        'Tentu, aku di sini untuk mendengarkan. Silakan ceritakan apa yang sedang kamu rasakan, ' + user_name + '.',
        'Aku siap mendengarkan curhatanmu. Apa yang ingin kamu ceritakan?',
        'Jika kamu butuh teman curhat, aku di sini untukmu. Apa yang ingin kamu sampaikan?',
        'Aku siap mendengarkan curhatanmu, ' + user_name + '. Silakan ceritakan apa yang sedang membuatmu gelisah atau stres.',
        'Saat kamu siap, ceritakan apa yang ingin kamu curhatkan. Aku di sini untuk mendengarkan.'],
    r'(?:aku )?(?:sedang panik|panik|gelisah|depresi|stres|lagi stres|lagi gelisah|lagi kesal|kesal|putus asa|cemas|sedih|marah|frustrasi|tertekan|terbebani|khawatir|kecewa|sakit hati|takut|malu|frustrasi|bingung|lelah|sia-sia|kecewa|bosan|jengkel|tersinggung)': [
        'Aku mendengar kamu sedang mengalami perasaan {0}, ' + user_name + '. Berceritalah lebih lanjut, aku di sini untuk mendengarkan.',
        'Jika kamu ingin mengungkapkan perasaan {0}, aku di sini untuk mendengarkan. Apa yang sedang kamu alami?',
        'Aku siap mendengarkan dan mendukungmu dalam menghadapi perasaan {0}, ' + user_name + '. Ceritakan lebih lanjut tentang apa yang sedang kamu rasakan.',
        'Aku di sini untukmu. Jika kamu ingin berbagi tentang perasaan {0} yang sedang terjadi, silakan ceritakan lebih lanjut.'],
    r'(?:ngomong apasih|dasar gaje|ye gaje|gajelas|dasar gajelas|ye gajelas|apasih goblok|gajelas tolol|gaje|gaje lu|apasih)': [
        'Maaf kalau responsku kurang memuaskan, ' + user_name + '. Apa yang sebenarnya ingin kamu ceritakan?',
        'Mungkin ada kesalahan dalam responsku, ' + user_name + '. Ceritakanlah lebih detail agar aku bisa lebih memahamimu.',
        'Saya minta maaf jika responsku tidak sesuai harapan, ' + user_name + '. Apa yang ingin kamu ceritakan?',
        'Aku minta maaf jika responsku tidak memuaskan, ' + user_name + '. Berceritalah lebih lanjut, aku di sini untuk mendengarkan.']
    }

    # default responses
    default_responses = [
    'Kok bisa begitu, ' + user_name + '?',
    'Coba ceritakan lebih dalam lagi, ' + user_name + '.',
    'Terus-terus, ' + user_name + '?',
    'Mau dong cerita lengkapnya, ' + user_name + '!',
    'Kok bisa begitu, ' + user_name + '? Aku jadi penasaran.',
    'Menurutmu kenapa bisa begitu, ' + user_name + '?',
    'Waduh, gimana tuh, ' + user_name + '?',
    'Kamu merasa apa tuh abis itu, ' + user_name + '?',
    'Kamu merasa gimana tuh abis itu, ' + user_name + '?',
    'Kamu merasa apa, ' + user_name + '?',
    'Kamu merasa gimana, ' + user_name + '?',
    'Terus gimana, ' + user_name + '?',
]

    # Menemukan pola pertanyaan yang cocok dengan inputan chat dan memberikan respons
    for pattern, responses in therapist_responses.items():
        match = regex.match(pattern, chat)
        if match is not None:
            response = random.choice(responses).format(*match.groups())
            return response

    # Jika tidak ada pola yang cocok, berikan respons default
    return random.choice(default_responses)
    
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
    recent_questions.append(chat)

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
            # Jika pengguna mengetikkan salah satu dari keyword berikut, aktifkan mode therapist dan balikkan ke bot_therapist_response
            therapist_keywords = ['therapist', 'aku mau curhat', 'aku mau curhat dong', 'aku butuh teman curhat',
                                  'curhat', 'mau curhat', 'pengen curhat', 'ingin curhat', 'curhat dong', 'curcol dong',
                                  'aku sedang panik', 'aku panik', 'aku gelisah', 'aku depresi', 'aku stres', 'aku lagi stres',
                                  'aku kesal', 'aku putus asa', 'aku cemas', 'aku sedih', 'aku marah', 'aku frustasi',
                                  'aku tertekan', 'aku terbebani', 'aku khawatir', 'aku kecewa', 'aku sakit hati', 'aku takut',
                                  'aku malu', 'aku bingung', 'aku lelah', 'aku sia-sia', 'aku bosan', 'aku jengkel', 'aku tersinggung',
                                  'aku kehilangan', 'aku merasa hampa', 'aku merasa sendirian', 'aku terluka', 'aku patah hati',
                                  'aku tidak berdaya', 'aku cemburu', 'aku gelap mata', 'aku frustrasi', 'aku kecewa pada diri sendiri',
                                  'aku merasa tidak berarti', 'aku tidak punya harapan', 'aku kelelahan', 'aku kesepian', 'aku merasa diabaikan',
                                  'aku merasa takut masa depan', 'aku khawatir tentang hidupku', 'aku bingung dengan diriku sendiri',
                                  'aku terjebak dalam keputusasaan', 'aku merasa tidak dicintai', 'aku merasa tidak diperhatikan',
                                  'aku merasa terasing', 'aku merasa tidak memiliki kendali', 'aku merasa terjebak dalam masalah',
                                  'aku merasa tidak bisa mengatasinya', 'aku merasa terpuruk',
                                  'gemes', 'galau', 'bete', 'mager', 'baper', 'kepo', 'gapapa', 'bingung', 'bosan', 'jenuh',
                                  'hancur', 'bodoh', 'sumpah', 'ciyee', 'gue', 'nangis', 'seneng', 'kece', 'asik', 'anxiety', 'gila',
                                  'cringe', 'awkward', 'mood', 'trigger', 'apatis', 'fomo', 'deadline', 'self-doubt', 'sks',
                                  'procrastination', 'sok cool', 'yasudahlah', 'capek', 'jijik', 'nyesek', 'santai', 'ambigu', 'bodo amat',
                                  'garing', 'gemesin', 'jatuh cinta', 'naksir', 'patah hati', 'ngebetein', 'nyesekin', 'ngebosenin',
                                  'bikin stres', 'capek banget', 'kepo banget', 'ga enak', 'keki', 'galau banget', 'gemes banget',
                                  'ingin curhat', 'ingin cerita', 'mau cerita', 'mau banget curhat', 'pengen banget cerita',]
            
            exit_keywords = ['terima kasih, jarwo', 'makasi', 'terima kasih', 'makasi jarwo', 'terima kasih, jarwo', 'makasi ya'
                             'makasi, jarwo', 'tq jarwo', 'tq', 'ya itu aja', 'ya begitu aja', 'ya udah gitu aja', 'udah gitu aja', 'daa', 'daaa', 'dadaaah',
                             'dadah', 'udah kayaknya gitu aja', 'udah kayaknya gitu aja deh', 'ya udah makasi', 'ya makasi', 'oke makasi', 'oke tq', 'oke terima kasih']
            
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

                        # daftar penolakan pengguna
                        rejection_responses = ['tidak boleh', 'tidak', 'mau tau aja', 'gaboleh', 'ga', 'nggak', 'nggak boleh',
                                                'kepo', 'ngapain nanya2', 'ngapain nanya-nanya', 'ga boleh']

                        # Cek jika user_name ada dalam daftar penolakan
                        if user_name.lower() in rejection_responses:
                            user_name = "Kak"
                            asking_name = False
                            return "Baik, tidak apa-apa. Bagaimana aku bisa membantu kamu hari ini, kak?", None

                        asking_name = False
                        return "Senang bertemu denganmu, " + user_name + ". Bagaimana aku bisa membantu kamu hari ini?", None
                elif any(keyword in chat.lower() for keyword in exit_keywords):
                    therapist_mode = False
                    return "Senang bisa membantumu, "+ user_name, None
                else:
                    return bot_therapist_response(chat), None
            
            else:
                chat = preprocess(chat)
                res = pipeline.predict_proba([chat])
                max_prob = max(res[0])
                if max_prob < 0.19:
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