import joblib
import os
from django.conf import settings
import re
MODEL_PATH = os.path.join(settings.BASE_DIR, 'advocate', 'ml_model.pkl')

# Load the trained model
try:
    model = joblib.load(MODEL_PATH)
    print(f"Model loaded successfully from {MODEL_PATH}")
except FileNotFoundError:
    model = None
    print(f"Model file not found at {MODEL_PATH}. Please ensure 'ml_model.pkl' is in the correct directory.")
except Exception as e:
    model = None
    print(f"Error loading model: {e}")

def clean_text(text):
    # Remove case numbers, dates, special characters, and digits
    text = re.sub(r'\d+', '', text)  # Remove digits
    text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
    text = text.lower()  # Convert to lowercase
    return text

def preprocess_text(text):
    # Basic preprocessing: Lowercase, remove extra spaces, etc.
    return text.lower().strip()

def classify_document(text):
    if model:
        try:
            # Preprocess the input text
            preprocessed_text = preprocess_text(text)
            prediction = model.predict([preprocessed_text])[0]
            print(f"Predicted category: {prediction}")
            return prediction
        except Exception as e:
            print(f"Error during prediction: {e}")
            return 'Uncategorized'
    else:
        return 'Uncategorized'

