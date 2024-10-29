import PyPDF2
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

# Load model and vectorizer
model = joblib.load('C:\Legal_advisor_mini\Legal_advisor\home\document_classifier.pkl')
vectorizer = joblib.load(r'C:\Legal_advisor_mini\Legal_advisor\home\vectorizer.pkl')

def classify_document(pdf_path):
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + ' '

    if not text.strip():
        print(f"No text extracted from {pdf_path}.")
        return "Uncategorized"

    vectorized_text = vectorizer.transform([text])
    classification = model.predict(vectorized_text)

    print(f"Classified {pdf_path} as {classification[0]} with extracted text: {text[:100]}...")  # Log first 100 characters
    return classification[0]
