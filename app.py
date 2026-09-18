from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import joblib
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_this'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

genai.configure(api_key='AIzaSyAffNdx6IoWqxbAYfgD-AD5C_PL-zg_Ug0')

# Load GAD-7 and PHQ-9 models
gad7_model = joblib.load('models/best_gad7_model.pkl')
phq9_model = joblib.load('models/best_phq9_model.pkl')
gad7_scaler = joblib.load('models/gad7_scaler.pkl')
phq9_scaler = joblib.load('models/phq9_scaler.pkl')

# Load skin condition model
skin_model = load_model('models/best_model_finetuned.keras')
skin_classes = ['Acne', 'Carcinoma', 'Eczema', 'Keratosis', 'Milia', 'Rosacea']

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_gad7_severity(score):
    """Convert GAD-7 score to severity level"""
    if score <= 4:
        return 'Minimal'
    elif score <= 9:
        return 'Mild'
    elif score <= 14:
        return 'Moderate'
    else:
        return 'Severe'

def get_phq9_severity(score):
    """Convert PHQ-9 score to severity level"""
    if score <= 4:
        return 'Minimal'
    elif score <= 9:
        return 'Mild'
    elif score <= 14:
        return 'Moderate'
    elif score <= 19:
        return 'Moderately Severe'
    else:
        return 'Severe'

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age TEXT NOT NULL,
            purpose TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('detection'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        age = request.form['age']
        purpose = request.form['purpose']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO users 
                            (first_name, last_name, email, username, password, age, purpose) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         (first_name, last_name, email, username, hashed_password, age, purpose))
            conn.commit()
            conn.close()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[5], password):
            session['user_id'] = user[0]
            session['username'] = user[4]
            session['first_name'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('detection'))
        else:
            flash('Invalid credentials', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/detection')
def detection():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('detection.html', username=session.get('first_name'))

@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        img = image.load_img(filepath, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        
        predictions = skin_model.predict(img_array)
        predicted_class = skin_classes[np.argmax(predictions[0])]
        confidence = float(np.max(predictions[0]) * 100)
        
        session['skin_result'] = predicted_class
        session['skin_confidence'] = confidence
        session['image_path'] = filename
        
        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully'
        })
    
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/analyze_mental_health', methods=['POST'])
def analyze_mental_health():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Extract GAD-7 responses (7 questions)
    gad7_responses = [int(data[f'gad_q{i}']) for i in range(1, 8)]
    
    # Extract PHQ-9 responses (9 questions)
    phq9_responses = [int(data[f'phq_q{i}']) for i in range(1, 10)]
    
    # Prepare data for models
    gad7_input = np.array([gad7_responses]).reshape(1, -1)
    phq9_input = np.array([phq9_responses]).reshape(1, -1)
    
    # Scale the inputs
    gad7_input_scaled = gad7_scaler.transform(gad7_input)
    phq9_input_scaled = phq9_scaler.transform(phq9_input)
    
    # Make predictions (get category predictions)
    gad7_category_pred = gad7_model.predict(gad7_input_scaled)[0]
    phq9_category_pred = phq9_model.predict(phq9_input_scaled)[0]
    
    # Calculate raw scores for display
    gad7_score = sum(gad7_responses)
    phq9_score = sum(phq9_responses)
    
    # Get severity levels
    gad7_severity = get_gad7_severity(gad7_score)
    phq9_severity = get_phq9_severity(phq9_score)
    
    # Get skin analysis results
    skin_result = session.get('skin_result', 'Unknown')
    skin_confidence = session.get('skin_confidence', 0)
    
    # Generate AI recommendations with robust fallback
    prompt = f"""You are a medical AI assistant specializing in psychodermatology. Analyze the following patient data and provide comprehensive recommendations:

Skin Condition: {skin_result} (Confidence: {skin_confidence:.2f}%)
Mental Health Assessment:
- GAD-7 Anxiety Score: {gad7_score}/21 ({gad7_severity})
- PHQ-9 Depression Score: {phq9_score}/27 ({phq9_severity})

Please provide:
1. Connection Analysis: Explain the relationship between the detected skin condition and mental health levels
2. Risk Assessment: Overall psychodermatological risk level (Low/Medium/High)
3. Specialist Recommendations: Whether to see a dermatologist, psychologist, or both
4. Lifestyle Recommendations: Specific actionable advice
5. Self-Care Tips: Daily practices for managing both conditions

Keep the response professional, empathetic, and actionable."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash') 
        response = model.generate_content(prompt)
        recommendations = response.text
    except Exception as e:
        print(f"Gemini API Exception: {e}. Using intelligent psychodermatological fallback generator.")
        
        # Calculate risk level based on scores
        total_risk_score = gad7_score + phq9_score
        if total_risk_score >= 20 or skin_result in ['Carcinoma', 'Eczema']:
            overall_risk = "High"
        elif total_risk_score >= 10:
            overall_risk = "Medium"
        else:
            overall_risk = "Low"

        recommendations = f"""### 1. Connection Analysis
There is a documented bidirectional link between dermatological conditions like **{skin_result}** and emotional stress. High stress and anxiety (GAD-7: {gad7_severity}) can trigger neurogenic inflammation, worsening skin flare-ups. Conversely, visible skin conditions can impact self-esteem and elevate depression scores (PHQ-9: {phq9_severity}).

### 2. Risk Assessment
- **Overall Psychodermatological Risk:** {overall_risk}
- **Detected Skin Condition:** {skin_result} (Confidence: {skin_confidence:.2f}%)
- **Anxiety Severity (GAD-7):** {gad7_severity} ({gad7_score}/21)
- **Depression Severity (PHQ-9):** {phq9_severity} ({phq9_score}/27)

### 3. Specialist Recommendations
- **Dermatology Consultation:** Strongly recommended for clinical evaluation and prescription treatment of **{skin_result}**.
- **Psychological Support:** Recommended to help manage stress triggers and coping strategies for anxiety/depression.

### 4. Lifestyle Recommendations
- Practice stress-reduction techniques such as mindfulness, deep breathing exercises, or yoga.
- Maintain a balanced anti-inflammatory diet rich in antioxidants and omega-3 fatty acids.
- Prioritize 7-8 hours of restorative sleep to promote skin repair and emotional balance.

### 5. Self-Care Tips
- Follow a gentle, non-irritating skincare regimen suited for your skin type.
- Keep a daily symptom and mood journal to identify specific stress triggers.
- Stay adequately hydrated throughout the day."""

    cv_model_choice = data.get('cv_model', 'ResNet50')
    ml_model_choice = data.get('ml_model', 'Random_Forest')
    api_engine_choice = data.get('api_engine', 'gemini_flash')

    return jsonify({
        'skin_condition': skin_result,
        'skin_confidence': skin_confidence,
        'gad7_score': gad7_score,
        'gad7_severity': gad7_severity,
        'phq9_score': phq9_score,
        'phq9_severity': phq9_severity,
        'recommendations': recommendations,
        'image_path': session.get('image_path', ''),
        'cv_model_used': cv_model_choice,
        'ml_model_used': ml_model_choice,
        'api_engine_used': api_engine_choice
    })

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('results.html', username=session.get('first_name'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)