import os
import librosa
import mysql.connector

# Connect to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1905",
    database="infant_db"
)

cursor = db.cursor()

# Extract features
def extract_features(file_path):
    y, sr = librosa.load(file_path)
    pitch = librosa.yin(y, fmin=50, fmax=300).mean()
    duration = librosa.get_duration(y=y, sr=sr)
    intensity = abs(y).mean()

    return float(pitch), float(duration), float(intensity)

# Classify cry
def classify(pitch):
    if pitch > 200:
        return "pain"
    elif pitch > 150:
        return "discomfort"
    else:
        return "normal"

# Insert data
def insert_data(file_path):
    pitch, duration, intensity = extract_features(file_path)
    label = classify(pitch)

    cursor.execute("INSERT INTO Infant (age, gender) VALUES (1, 'male')")
    infant_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO CryData (infant_id, audio_path, duration, label) VALUES (%s, %s, %s, %s)",
        (infant_id, file_path, duration, label)
    )
    cry_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO Features (cry_id, pitch, frequency, intensity) VALUES (%s, %s, %s, %s)",
        (cry_id, pitch, pitch, intensity)
    )

    db.commit()

# Read all audio files
folder = "audio"

for file in os.listdir(folder):
    if file.endswith(".wav"):
        insert_data(os.path.join(folder, file))

print("✅ Data inserted successfully!")

# Menu
while True:
    print("\n1. Show All Data")
    print("2. Show Pain Cries")
    print("3. Show discomfort Cries")
    print("4. Exit")

    choice = input("Enter choice: ")

    if choice == '1':
        cursor.execute("SELECT * FROM CryData")
        for row in cursor.fetchall():
            print(row)

    elif choice == '2':
        cursor.execute("SELECT * FROM CryData WHERE label='pain'")
        for row in cursor.fetchall():
            print(row)

    
    elif choice == '3':
        cursor.execute("SELECT * FROM CryData WHERE label='discomfort'")
        for row in cursor.fetchall():
            print(row)

    elif choice == '4':
        break