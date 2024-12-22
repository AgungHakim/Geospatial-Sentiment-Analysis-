# -*- coding: utf-8 -*-
"""Sudah bersih_Tugas_Akhir_Analisis_Sentimen_Bencana.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1b4kNcLfWORZNhXmiOmi5G_DLeT823mja

# **Import Library**
"""

!pip install pandas nltk tensorflow scikit-learn
!pip install sastrawi

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import pandas as pd
import re
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, make_scorer
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderQueryError
from tqdm import tqdm
from collections import Counter
from google.colab import drive
from wordcloud import WordCloud
from sklearn.pipeline import Pipeline
from imblearn.pipeline import Pipeline as ImbPipeline
import nltk
from nltk.corpus import stopwords
import json
from sklearn.model_selection import train_test_split
import tensorflow as tf
from collections import Counter
import warnings
from IPython.display import display


warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

"""# **Load Dataset**"""

# Mount Google Drive untuk akses file
drive.mount('/content/drive')

# Path ke file sumber
file_path = '/content/drive/My Drive/TA_Analisis_Sentimen/Fix_Labeled_Dataset_Crawling_Eruption Of Marapi.csv'

# Baca file CSV dengan pembatas yang sesuai
df = pd.read_csv(file_path, delimiter=';')

"""# **Praprocessing**"""

# Step 1: Preprocessing
# 1.1 Data Cleaning
def clean_text(text):
    text = re.sub(r'http\S+|www\S+|https\S+|https t|t co', '', text, flags=re.MULTILINE) # Remove URLs
    text = re.sub(r'@\w+|\#\w+', '', text)  # Remove mentions and hashtags
    text = re.sub(r'[^a-zA-Z\s]', '', text) # Remove non-alphanumeric characters
    text = text.strip()                     # Remove any leading/trailing whitespaces
    return text

# 1.2 Case Folding
def case_folding(text):
    return text.lower()

# 1.3 Tokenizing
def tokenize_text(text):
    return text.split()

# 1.4 Normalizing
def normalize_text(tokens):
    abbreviation_dict = {
        'gk': 'nggak', 'ga': 'nggak', 'g': 'nggak','ngga': 'nggak', 'dlm': 'dalam', 'dgn': 'dengan', 'krn': 'karena', 'sdh': 'sudah', 'udh': 'sudah',
        'blm': 'belum', 'aja': 'saja', 'sy': 'saya', 'aku': 'saya', 'q': 'saya', 'kamu': 'anda', 'km': 'kamu',
        'bgt': 'banget', 'trs': 'terus', 'sm': 'sama', 'org': 'orang', 'jg': 'juga', 'bs': 'bisa', 'gmn': 'gimana',
        'gimana': 'bagaimana', 'tp': 'tapi', 'y': 'ya', 'smg': 'semoga', 'hrs': 'harus', 'lbh': 'lebih', 'jgn': 'jangan',
        'pd': 'pada', 'utk': 'untuk', 'gmana': 'bagaimana', 'klu': 'kalau', 'klo': 'kalau', 'dl': 'dulu', 'dtg': 'datang',
        'bgmn': 'bagaimana', 'nih': 'ini', 'pls': 'tolong', 'btw': 'ngomong-ngomong', 'ya': 'iya', 'si': 'sih',
        'brp': 'berapa', 'tmn': 'teman', 'bbrp': 'beberapa', 'trmksh': 'terima kasih', 'makasih': 'terima kasih',
        'mks': 'makasih', 'sblm': 'sebelum', 'mo': 'mau', 'mlm': 'malam', 'pagi': 'selamat pagi',
        'siang': 'selamat siang', 'sore': 'selamat sore', 'malem': 'malam', 'ok': 'oke', 'oke': 'baik',
        'thx': 'terima kasih', 'wkwk': 'tertawa', 'lol': 'tertawa', 'he': 'haha', 'ah': 'ah', 'gt': 'gitu',
        'om': 'paman', 'pak': 'bapak', 'bu': 'ibu', 'dr': 'dokter', 'msh': 'masih', 'kl': 'kalau', 'kmrn': 'kemarin',
        'bsk': 'besok', 'gw': 'saya', 'loe': 'kamu', 'loh': 'lho', 'n': 'dan', 'yg': 'yang', 'knp': 'kenapa', 'tdk': 'tidak'
    }
    return [abbreviation_dict.get(word, word) for word in tokens]

# 1.5 Stopword Removal
# Download stopwords dari NLTK jika belum diunduh
nltk.download('stopwords')

# Daftar stopwords Bahasa Indonesia dari nltk
stop_words_id = set(stopwords.words('indonesian'))

def remove_stopwords(tokens):
    return [word for word in tokens if word not in stop_words_id]

# 1.6 Stemming
def sastrawi_stem(tokens):
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()

    # Lakukan stemming pada setiap token
    return [stemmer.stem(word) for word in tokens]

# Apply all steps to the text
df['cleaned_text'] = df['full_text'].apply(clean_text)
df['lowered_text'] = df['cleaned_text'].apply(case_folding)
df['tokenized_text'] = df['lowered_text'].apply(tokenize_text)
df['normalized_text'] = df['tokenized_text'].apply(normalize_text)
df['filtered_text'] = df['normalized_text'].apply(remove_stopwords)
df['stemmed_text'] = df['filtered_text'].apply(sastrawi_stem)  # Menggunakan Sastrawi untuk stemming
df['processed_text'] = df['stemmed_text'].apply(lambda tokens: ' '.join(tokens))  # Final processed text

display(df)

"""# **Aspek Aspek**"""

# Define keywords for additional aspects
aspect_keywords = {
    'Kebutuhan Dasar': [
        'Tempat tinggal', 'hunian', 'rumah', 'pengungsian', 'bangun', 'pemukiman', 'bangunan',
        'medis', 'obat', 'sakit', 'penyakit', 'kesehatan', 'dokter', 'masker',
        'makan', 'bahan pokok', 'lapar', 'pangan', 'makanan', 'dapur', 'Dapur', 'sembako',
        'air', 'minum', 'haus',
        'listrik', 'padam',
        'jalan', 'transportasi'
    ],
    'Respon dan Tindakan': [
        'santunan', 'bantuan', 'bantuan sosial', 'penyelamatan', 'relawan', 'sar', 'evakuasi', 'pertolongan',
        'membantu', 'mengevakuasi', 'asuransi'
    ],
    'Dampak dan Kerusakan': [
        'kerugian', 'dampak', 'kerusakan', 'hilang', 'bangunan', 'rumah', 'korban', 'meninggal', 'luka', 'jiwa', 'selamat'
    ],
    'Cuaca dan Alam': [
        'cuaca', 'hujan', 'tanah', 'gunung', 'pohon', 'abu', 'abuu', 'asap', 'siang', 'malam', 'pagi', 'sore', 'jurang',
        'erupsi', 'banjir', 'membaik', 'sembuh', 'longsor', 'vulkanik', 'gunuang', 'meletus', 'gempa'
    ]
}

# Add processed text column for classification
df['processed_text'] = df['full_text']

# Function to classify each text based on aspect keywords
def classify_aspect(text):
    for aspect, keywords in aspect_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return aspect
    return 'Lainnya'  # Classify as 'Other' if no keywords found

# Apply classification function to each row
df['Aspect'] = df['processed_text'].apply(classify_aspect)

"""# **Modeling**"""

label_encoder = LabelEncoder()
df['Sentimen'] = label_encoder.fit_transform(df['Sentimen'])

# Aspek yang akan dianalisis
aspects = ['Kebutuhan Dasar', 'Dampak dan Kerusakan', 'Respon dan Tindakan', 'Cuaca dan Alam']
kernels = ['linear', 'poly', 'rbf']
results = {}

for aspect in aspects:
    print(f"\nProcessing aspect: {aspect}")
    df_aspect = df[df['Aspect'] == aspect]
    if df_aspect.empty:
        print(f"No data for aspect: {aspect}")
        continue

    # TF-IDF
    tfidf_vectorizer = TfidfVectorizer(max_features=1000)
    X = tfidf_vectorizer.fit_transform(df_aspect['processed_text'])
    y = df_aspect['Sentimen']

    # Check class distribution
    class_counts = Counter(y)
    if len(class_counts) < 2 or any(count < 2 for count in class_counts.values()):
        print(f"Skipping aspect {aspect} due to insufficient samples in one or more classes.")
        continue

    # Stratified K-Fold
    kf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    aspect_results = {}

    for kernel in kernels:
        print(f"\nUsing kernel: {kernel}")
        scores = {'accuracy': [], 'precision': [], 'recall': [], 'f1_score': []}

        for train_index, test_index in kf.split(X, y):
            X_train, X_test = X[train_index], X[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]

            # SMOTE dengan validasi jumlah sampel
            minority_class_count = y_train.value_counts().min()
            if minority_class_count > 1:
                smote = SMOTE(random_state=42, k_neighbors=min(1, minority_class_count - 1) if minority_class_count > 1 else 1)
                X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
            else:
                print(f"Skipping SMOTE for aspect {aspect} due to insufficient minority class samples.")
                X_train_resampled, y_train_resampled = X_train, y_train

            # SVM dengan kernel dinamis
            pipeline = ImbPipeline([
                ('svm', SVC(C=1, kernel=kernel, gamma='scale'))
            ])
            pipeline.fit(X_train_resampled, y_train_resampled)

            y_pred = pipeline.predict(X_test)

            scores['accuracy'].append(accuracy_score(y_test, y_pred))
            scores['precision'].append(precision_score(y_test, y_pred, average='weighted', zero_division=0))
            scores['recall'].append(recall_score(y_test, y_pred, average='weighted', zero_division=0))
            scores['f1_score'].append(f1_score(y_test, y_pred, average='weighted', zero_division=0))

        # Average Metrics per kernel
        aspect_results[kernel] = {
            'accuracy': sum(scores['accuracy']) / len(scores['accuracy']),
            'precision': sum(scores['precision']) / len(scores['precision']),
            'recall': sum(scores['recall']) / len(scores['recall']),
            'f1_score': sum(scores['f1_score']) / len(scores['f1_score'])
        }

    results[aspect] = aspect_results

"""# **Evaluasi**"""

# Print Results
for aspect, kernel_results in results.items():
    print(f"\nAspect: {aspect}")
    for kernel, metrics in kernel_results.items():
        print(f"\nKernel: {kernel}")
        for metric, score in metrics.items():
            print(f"{metric.capitalize()}: {score:.4f}")

"""# **Visualisasi**"""

# Group by aspect and sentiment to get counts
aspect_sentiment_counts = df.groupby(['Aspect', 'Sentimen']).size().unstack(fill_value=0)

# Create a single grouped bar plot for all aspects with labels on top of each bar
fig, ax = plt.subplots(figsize=(15, 10))

# Generate the grouped bar plot
aspect_sentiment_counts.plot(kind='bar', ax=ax, color=['red', 'green'], width=0.8)

# Add numbers on top of the bars
for i, bar in enumerate(ax.patches):
    if bar.get_height() > 0:  # Display labels only for bars with height > 0
        ax.text(
            bar.get_x() + bar.get_width() / 2,  # X coordinate
            bar.get_height() + 1,  # Y coordinate (slightly above the bar)
            int(bar.get_height()),  # Text to display (the height value)
            ha='center', va='bottom', fontsize=9  # Center alignment
        )

# Set titles and labels
ax.set_title("Sentimen Berdasarkan Aspek", fontsize=16)
ax.set_xlabel("Aspek", fontsize=12)
ax.set_ylabel("Jumlah", fontsize=12)
ax.legend(["Negatif", "Positif"], title="Sentimen", fontsize=10)
plt.xticks(rotation=45, fontsize=10)
plt.tight_layout()

# Show plot
plt.show()

df['Sentimen'] = label_encoder.inverse_transform(df['Sentimen'])

# Inisialisasi Geolocator
geolocator = Nominatim(user_agent="geoapi")

# Fungsi untuk mendapatkan koordinat lokasi
def get_coordinates(location):
    try:
        if not location or pd.isna(location):
            return None  # Kembalikan None jika lokasi kosong atau tidak valid
        loc = geolocator.geocode(location, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
        else:
            return None
    except (GeocoderTimedOut, GeocoderQueryError) as e:
        print(f"Error mendapatkan koordinat untuk lokasi: {location} | Error: {e}")
        return None

# Menambahkan koordinat ke dataset
df['Coordinates'] = df['Location'].apply(get_coordinates)

# Memisahkan koordinat menjadi latitude dan longitude
df['Latitude'] = df['Coordinates'].apply(lambda x: x[0] if x else None)
df['Longitude'] = df['Coordinates'].apply(lambda x: x[1] if x else None)

# Menangani lokasi yang tidak dikenali dengan memberikan nilai default
df['Latitude'] = df['Latitude'].fillna(0)  # Default latitude
df['Longitude'] = df['Longitude'].fillna(0)  # Default longitude

# Step 1: Agregasi data untuk setiap aspek dan sentimen
aspect_sentimen_aggregated = df.groupby(['Aspect', 'Location', 'Sentimen']).size().unstack(fill_value=0)
aspect_sentimen_aggregated['Dominant_Sentimen'] = aspect_sentimen_aggregated.idxmax(axis=1)  # Sentimen terbanyak
aspect_sentimen_aggregated = aspect_sentimen_aggregated.reset_index()

# Menggabungkan koordinat ke data agregasi berdasarkan lokasi
location_coordinates = df.groupby('Location')[['Latitude', 'Longitude']].mean().reset_index()
map_data = pd.merge(aspect_sentimen_aggregated, location_coordinates, on='Location', how='left')

# Menyaring data berdasarkan masing-masing aspek
aspects = ['Kebutuhan Dasar', 'Dampak dan Kerusakan', 'Respon dan Tindakan', 'Cuaca dan Alam']

# Menyimpan peta di luar loop untuk ditampilkan secara terpisah
maps = {}

# Loop untuk memproses data setiap aspek
for aspect in aspects:
    # Filter data berdasarkan aspek
    aspect_data = map_data[map_data['Aspect'] == aspect]

    # Membuat peta dasar untuk setiap aspek
    m = folium.Map(location=[-2.5489, 118.0149], zoom_start=5, tiles="cartodb positron")

    # Menambahkan marker berdasarkan sentimen dominan untuk setiap lokasi dan aspek
    for _, row in aspect_data.iterrows():
        folium.CircleMarker(
            location=(row['Latitude'], row['Longitude']),
            radius=8,
            color='blue' if row['Dominant_Sentimen'] == 'Positif' else 'red',
            fill=True,
            fill_opacity=0.6,
            popup=f"Lokasi: {row['Location']}<br>Aspek: {row['Aspect']}<br>Sentimen Dominan: {row['Dominant_Sentimen']}"
        ).add_to(m)

    # Menyimpan peta di dictionary berdasarkan aspek
    maps[aspect] = m

# Sekarang Anda bisa menampilkan peta untuk setiap aspek dengan cara manual

# Menampilkan peta untuk 'Kebutuhan Dasar'
display(maps['Kebutuhan Dasar'])
# Print nama-nama daerah beserta sentimen dominan untuk 'Kebutuhan Dasar'
kebutuhan_dasar_data = map_data[map_data['Aspect'] == 'Kebutuhan Dasar']
print("Daerah dan Sentimen Dominan untuk 'Kebutuhan Dasar':")
for _, row in kebutuhan_dasar_data.iterrows():
    print(f"Lokasi: {row['Location']}, Sentimen Dominan: {row['Dominant_Sentimen']}")

# Menampilkan peta untuk 'Dampak dan Kerusakan'
display(maps['Dampak dan Kerusakan'])
# Print nama-nama daerah beserta sentimen dominan untuk 'Dampak dan Kerusakan'
dampak_kerusakan_data = map_data[map_data['Aspect'] == 'Dampak dan Kerusakan']
print("Daerah dan Sentimen Dominan untuk 'Dampak dan Kerusakan':")
for _, row in dampak_kerusakan_data.iterrows():
    print(f"Lokasi: {row['Location']}, Sentimen Dominan: {row['Dominant_Sentimen']}")

# Menampilkan peta untuk 'Respon dan Tindakan'
display(maps['Respon dan Tindakan'])
# Print nama-nama daerah beserta sentimen dominan untuk 'Respon dan Tindakan'
respon_tindakan_data = map_data[map_data['Aspect'] == 'Respon dan Tindakan']
print("Daerah dan Sentimen Dominan untuk 'Respon dan Tindakan':")
for _, row in respon_tindakan_data.iterrows():
    print(f"Lokasi: {row['Location']}, Sentimen Dominan: {row['Dominant_Sentimen']}")

# Menampilkan peta untuk 'Cuaca dan Alam'
display(maps['Cuaca dan Alam'])
# Print nama-nama daerah beserta sentimen dominan untuk 'Cuaca dan Alam'
cuaca_alam_data = map_data[map_data['Aspect'] == 'Cuaca dan Alam']
print("Daerah dan Sentimen Dominan untuk 'Cuaca dan Alam':")
for _, row in cuaca_alam_data.iterrows():
    print(f"Lokasi: {row['Location']}, Sentimen Dominan: {row['Dominant_Sentimen']}")