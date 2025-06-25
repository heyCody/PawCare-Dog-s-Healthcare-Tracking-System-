


from flask import Flask,Blueprint, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import tensorflow as tf
import numpy as np
from PIL import Image
from io import BytesIO
from tensorflow.keras.preprocessing.image import img_to_array

chatbot_bp = Blueprint('chatbot', __name__)
CORS(chatbot_bp)

# Load ML models
model = joblib.load('C:/Pawcare/dog_health_model1.pkl')
le = joblib.load('C:/PawCare/label_encoder1.pkl')
cnn_model = tf.keras.models.load_model('C:/Pawcare/dog_emotion_model.h5')

cnn_class_names = ['angry', 'happy', 'relaxed', 'sad']

# Symptom vectorization list
all_symptoms = ["fever","vomiting","paralysis","reducedappetite","coughing","dischargefromeyes","hyperkeratosis","nasaldischarge","lethargy","sneezing","diarrhea","depression","difficultyinbreathing","pain","skinsores","inflammation_eyes","anorexia","seizures","dehydration","weightloss","bloodystool","weakness","inflammation_mouth","rapidheartbeat","fatigue","swollenbelly","laziness","anemia","fainting","reversesneezing","gagging","lameness","stiffness","limping","increasedthirst","increasedurination","excesssalivation","aggression","foamingatmouth","difficultyinswallowing","irritable","pica","hydrophobia","highlyexcitable","shivering","jaundice","decreasedthirst","decreasedurination","bloodinurine","palegums","ulcersinmouth","badbreath"]

def preprocess(symptoms):
    return [1 if symptom in symptoms else 0 for symptom in all_symptoms]

def preprocess_image(file_bytes):
    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    image = image.resize((96,96))
    img_array = img_to_array(image) / 255.0
    return np.expand_dims(img_array, axis=0)



@chatbot_bp.route("/api/diagnose", methods=["POST"])
def diagnose():
    data = request.get_json()
    symptoms = data.get("symptoms", [])

    input_vector = preprocess(symptoms)
    print("Preprocessed Input Vector:", input_vector)
    print("Shape of input vector:", len(input_vector))

    try:
        prediction = model.predict([input_vector])[0]
        condition = le.inverse_transform([prediction])[0]
        return jsonify({"condition": condition})
    except Exception as e:
        print("Error during prediction:", str(e))
        return jsonify({"error": str(e)}), 500


@chatbot_bp.route("/api/analyze-image", methods=["POST", "OPTIONS"])
def analyze_image():
    if request.method == 'OPTIONS':
        return '', 200

    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    try:
        image_bytes = request.files['image'].read()
        input_img = preprocess_image(image_bytes)
        prediction = cnn_model.predict(input_img)[0]
        predicted_label = cnn_class_names[np.argmax(prediction)]
        return jsonify({"condition": predicted_label})
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

