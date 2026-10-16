from flask import Flask, render_template, request
import librosa
import mysql.connector
import os
from pydub import AudioSegment
from werkzeug.utils import secure_filename

# FFmpeg Path
AudioSegment.converter = r"C:\Users\Anish\Downloads\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffprobe   = r"C:\Users\Anish\Downloads\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin\ffprobe.exe"

app = Flask(__name__)

UPLOAD_FOLDER = "audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DB
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1905",
    database="infant_db"
)
cursor = db.cursor()

# ✅ FILE VALIDATION
def allowed_file(filename):
    return filename.lower().endswith(('.wav', '.mp3', '.webm'))

# 🎧 MP3 → WAV
def convert_to_wav(file_path):
    if file_path.endswith(".mp3"):
        sound = AudioSegment.from_mp3(file_path)
        new_path = file_path.replace(".mp3", ".wav")
        sound.export(new_path, format="wav")
        return new_path
    return file_path

# 🎼 FEATURE EXTRACTION
def extract_features(file_path):
    y, sr = librosa.load(file_path, sr=None)
    pitch = librosa.yin(y, fmin=50, fmax=600).mean()
    duration = librosa.get_duration(y=y, sr=sr)
    intensity = abs(y).mean()

    # 🔍 DEBUG (very useful)
    print("Pitch:", pitch, "Intensity:", intensity)

    return float(pitch), float(duration), float(intensity)

# 🧠 CLASSIFICATION
def classify(pitch):
    if pitch > 400:
        return "Pain"
    elif pitch > 200:
        return "Discomfort"
    else:
        return "Normal"

# 👶 SMART BABY DETECTION (UPDATED)
def is_baby_voice(pitch, intensity):
    return 120 < pitch < 600 and intensity > 0.003

@app.route("/", methods=["GET", "POST"])
def index():

    result = ""

    # 📊 ALWAYS LOAD COUNTS
    cursor.execute("SELECT label FROM CryData")
    data = cursor.fetchall()

    counts = {"Pain": 0, "Discomfort": 0, "Normal": 0}
    for d in data:
        if d[0] in counts:
            counts[d[0]] += 1

    if request.method == "POST":
        file = request.files["audio"]

        if file:

            # ❌ INVALID FILE
            if not allowed_file(file.filename):
                return render_template("index.html",
                                       result="❌ Invalid file! Upload audio file",
                                       counts=counts)

            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)

            path = convert_to_wav(path)

            pitch, duration, intensity = extract_features(path)

            # ❌ NOT BABY
            if not is_baby_voice(pitch, intensity):
                return render_template("index.html",
                                       result="❌ Not a baby cry",
                                       counts=counts)

            result = classify(pitch)

            cursor.execute("INSERT INTO Infant (age, gender) VALUES (1, 'male')")
            infant_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO CryData (infant_id, audio_path, duration, label) VALUES (%s, %s, %s, %s)",
                (infant_id, path, duration, result)
            )

            db.commit()

    return render_template("index.html", result=result, counts=counts)

# 🎤 MIC ROUTE
@app.route("/record", methods=["POST"])
def record():

    file = request.files["audio"]

    if file:
        path = os.path.join(UPLOAD_FOLDER, "recorded.webm")
        file.save(path)

        sound = AudioSegment.from_file(path, format="webm")
        wav_path = path.replace(".webm", ".wav")
        sound.export(wav_path, format="wav")

        pitch, duration, intensity = extract_features(wav_path)

        if not is_baby_voice(pitch, intensity):
            return {"result": "❌ Not a baby cry"}

        result = classify(pitch)

        cursor.execute("INSERT INTO Infant (age, gender) VALUES (1, 'male')")
        infant_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO CryData (infant_id, audio_path, duration, label) VALUES (%s, %s, %s, %s)",
            (infant_id, wav_path, duration, result)
        )

        db.commit()

        return {"result": result}

    return {"result": "❌ No audio"}

app.run(debug=True)