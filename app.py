from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from textblob import TextBlob
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Retrieve the API key from the .env file
api_key = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=api_key)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for session management

# Setup SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.Text, nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Initialize the chat session globally
chat_session = None

def start_gemini_chat():
    global chat_session
    try:
        # Instantiate the model and start a chat session
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        chat_session = model.start_chat()
    except Exception as e:
        print(f"Error starting chat: {str(e)}")

def get_gemini_response(prompt):
    global chat_session
    try:
        # If the chat session has not been initialized, start it
        if chat_session is None:
            start_gemini_chat()
        
        # Send a message and get a response
        response = chat_session.send_message(prompt)
        return response.text if response else "No response from the model."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    feedback_text = request.form.get('feedback')
    if feedback_text:
        # Store the feedback in the database
        feedback_entry = Feedback(feedback=feedback_text)
        db.session.add(feedback_entry)
        db.session.commit()
        # Pass a flag to show the thank you message
        return render_template('submit_feedback.html', thank_you=True)
    return render_template('submit_feedback.html', thank_you=False)

@app.route('/sentiment_analysis_result')
def sentiment_analysis_result():
    # Retrieve the latest feedback from the database
    feedback_entry = Feedback.query.order_by(Feedback.id.desc()).first()
    if feedback_entry:
        # Perform sentiment analysis on the feedback
        analysis = TextBlob(feedback_entry.feedback)
        sentiment = "Positive" if analysis.sentiment.polarity > 0 else "Negative" if analysis.sentiment.polarity < 0 else "Neutral"
        return render_template('sentiment_analysis_result.html', feedback=feedback_entry.feedback, result=sentiment)
    
    # No feedback found, display a "No feedback provided" message
    return render_template('sentiment_analysis_result.html', feedback=None, result=None)

@app.route('/insight_advisor', methods=['POST'])
def insight_advisor():
    return render_template('Insight Advisor.html')

@app.route('/financial_news', methods=['POST'])
def financial_news():
    return render_template('Financial News.html')

@app.route('/live_chat', methods=['POST'])
def chatbot():
    user_input = request.form.get('user_input')
    chatbot_response = None
    if user_input:
        chatbot_response = get_gemini_response(user_input)
    return render_template('Live Chat.html', chatbot_response=chatbot_response)

if __name__ == "__main__":
    start_gemini_chat()  # Initialize the chat session when the app starts
    app.run(debug=True)
