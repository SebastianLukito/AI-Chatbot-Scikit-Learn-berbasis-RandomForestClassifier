import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import pickle

# Membaca data dari CSV (misalnya) dimana kolom 'text' adalah teks dan 'context' adalah label konteks
df = pd.read_csv('context_data.csv')

# Membuat model pipeline
model = make_pipeline(TfidfVectorizer(), MultinomialNB())

# Melatih model
model.fit(df['text'], df['context'])

# Menyimpan model
with open("model_konteks.pkl", "wb") as file:
    pickle.dump(model, file)

class KonteksPrediktor:
    def __init__(self, model_path="model_konteks.pkl"):
        with open(model_path, "rb") as file:
            self.model = pickle.load(file)
    
    def prediksi_konteks(self, text):
        return self.model.predict([text])[0]