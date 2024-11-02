import os
from django.conf import settings
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_NAME = "nlpaueb/legal-bert-base-uncased"  # Hugging Face model for legal text classification

# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

def classify_document(text):
    try:
        # Tokenize the input text
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        
        # Perform prediction
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            predicted_class_id = logits.argmax().item()
        
        # Map predicted class ID to class name (you need to define this mapping)
        class_names = ["theft", "murder", "robbery", 
        "other", "assault", "fraud", "embezzlement", "kidnapping", 
        "business_disputes", "personal_issues", "confidentiality_breach"] 
        predicted_class = class_names[predicted_class_id]
        
        print(f"Predicted category: {predicted_class}")
        return predicted_class
    except Exception as e:
        print(f"Error during prediction: {e}")
        return 'Uncategorized'