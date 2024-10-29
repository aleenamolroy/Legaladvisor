import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

# Load your training data
data = pd.read_csv('training_data.csv')
X = data['text']
y = data['label']

# Vectorization
vectorizer = CountVectorizer()
X_vectorized = vectorizer.fit_transform(X)

# Training the model
model = MultinomialNB()
model.fit(X_vectorized, y)

# Save the model and vectorizer
joblib.dump(model, 'C:\\Legal_advisor_mini\\Legal_advisor\\home\\document_classifier.pkl')
joblib.dump(vectorizer, 'C:\\Legal_advisor_mini\\Legal_advisor\\home\\vectorizer.pkl')

print("Model training complete and files saved.")
