from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import json
import hashlib
import secrets
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Simple in-memory user storage (in production, use a proper database)
USERS = {
    'admin@college.edu': {
        'username': 'admin',
        'email': 'admin@college.edu',
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'firstName': 'Admin',
        'lastName': 'User',
        'userType': 'admin',
        'created_at': datetime.now().isoformat()
    },
    'faculty@college.edu': {
        'username': 'faculty',
        'email': 'faculty@college.edu',
        'password': hashlib.sha256('faculty123'.encode()).hexdigest(),
        'firstName': 'Faculty',
        'lastName': 'Member',
        'userType': 'faculty',
        'created_at': datetime.now().isoformat()
    },
    'student@college.edu': {
        'username': 'student',
        'email': 'student@college.edu',
        'password': hashlib.sha256('student123'.encode()).hexdigest(),
        'firstName': 'Student',
        'lastName': 'User',
        'userType': 'student',
        'created_at': datetime.now().isoformat()
    }
}

# College knowledge base with predefined Q&A pairs
COLLEGE_KB = {
    "courses offered": {
        "response": "Our college offers the following programs:\n\n• Computer Science Engineering (B.Tech)\n• Information Technology (B.Tech)\n• Electronics & Communication Engineering (B.Tech)\n• Mechanical Engineering (B.Tech)\n• Civil Engineering (B.Tech)\n• Business Administration (MBA)\n• Computer Applications (MCA)\n• Bachelor of Commerce (B.Com)\n• Bachelor of Arts (BA)\n• Master of Arts (MA)",
        "keywords": ["courses", "programs", "departments", "degree", "bachelor", "master", "engineering", "commerce", "arts"]
    },
    "head of department": {
        "response": "Here are our department heads:\n\n• Computer Science: Dr. Sarah Johnson\n• Information Technology: Prof. Michael Chen\n• Electronics & Communication: Dr. Emily Rodriguez\n• Mechanical Engineering: Prof. David Kumar\n• Civil Engineering: Dr. Lisa Wang\n• Business Administration: Prof. Robert Singh\n• Commerce: Dr. Anita Patel\n• Arts & Humanities: Prof. James Thompson",
        "keywords": ["hod", "head", "department head", "director", "chairman", "dean", "principal"]
    },
    "exam timetable": {
        "response": "The current exam timetable is:\n\n📅 Mid-Term Exams: March 15-25, 2024\n📅 Final Exams: May 10-25, 2024\n📅 Practical Exams: May 26-30, 2024\n📅 Results Declaration: June 15, 2024\n\nFor detailed subject-wise timetable, please visit the college website or contact the examination department.",
        "keywords": ["exam", "timetable", "schedule", "dates", "when", "examination", "tests", "results"]
    },
    "library location": {
        "response": "📍 Central Library Location:\n\n• Building: Block A (Main Academic Building)\n• Floor: Ground Floor & First Floor\n• Timings: 8:00 AM - 8:00 PM (Monday to Friday)\n• Saturday: 9:00 AM - 5:00 PM\n• Sunday: Closed\n\n• Reference Section: Ground Floor\n• Digital Library: First Floor\n• Reading Halls: Both floors available\n\nFor more information, contact: +91-XXX-XXXXXXX",
        "keywords": ["library", "location", "where", "address", "books", "study", "reference"]
    },
    "office timings": {
        "response": "🕒 College Office Timings:\n\n📋 Administrative Office:\n• Monday to Friday: 9:00 AM - 5:00 PM\n• Saturday: 9:00 AM - 1:00 PM\n• Sunday: Closed\n\n📚 Academic Office:\n• Monday to Friday: 9:30 AM - 4:30 PM\n• Lunch Break: 1:00 PM - 2:00 PM\n• Saturday: 10:00 AM - 12:30 PM\n\n💰 Accounts Office:\n• Monday to Friday: 10:00 AM - 4:00 PM\n• Saturday: 10:00 AM - 12:00 PM",
        "keywords": ["office", "timings", "hours", "when", "open", "closed", "working hours", "administrative"]
    },
    "admission process": {
        "response": "🎓 Admission Process:\n\n1. **Application Submission**: Online applications available on college website\n2. **Entrance Exam**: Based on course requirements\n3. **Merit List**: Published after entrance exam results\n4. **Document Verification**: Required certificates and mark sheets\n5. **Fee Payment**: As per fee structure\n6. **Orientation**: For new students\n\n📞 Admission Helpline: +91-XXX-XXXXXXX\n📧 Email: admissions@college.edu",
        "keywords": ["admission", "apply", "how to join", "enrollment", "application", "process", "requirements"]
    },
    "fee structure": {
        "response": "💰 Fee Structure (Annual):\n\n🔧 Engineering Courses (B.Tech):\n• Tuition Fee: ₹1,20,000\n• Development Fee: ₹15,000\n• Other Charges: ₹10,000\n\n💼 Management (MBA):\n• Tuition Fee: ₹1,50,000\n• Development Fee: ₹20,000\n• Other Charges: ₹12,000\n\n🎨 Arts & Commerce:\n• Tuition Fee: ₹80,000\n• Development Fee: ₹10,000\n• Other Charges: ₹8,000\n\n*Fees are subject to change. For exact details, contact the accounts office.",
        "keywords": ["fee", "fees", "cost", "price", "payment", "tuition", "charges", "money"]
    },
    "facilities": {
        "response": "🏫 College Facilities:\n\n• 🏛️ Central Library with Digital Resources\n• 💻 Computer Labs with Latest Technology\n• 🧪 Well-equipped Science Laboratories\n• 🏃 Sports Complex & Gymnasium\n• 🍽️ Cafeteria & Food Court\n• 🚗 Parking Facilities\n• 🏥 Medical Center\n• 🏠 Hostel Accommodation\n• 📡 Wi-Fi Campus\n• 🎭 Cultural & Sports Clubs\n• 🚌 Transportation Services",
        "keywords": ["facilities", "amenities", "infrastructure", "labs", "library", "sports", "hostel", "cafeteria"]
    },
    "hello":{
        "response": "Hello:Sir/Madam What Can I Help You For Today",
        "keywords": ["Hello Sir What Can I Help You Today!"]
    }
}

# Authentication helper functions
def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session

def get_current_user():
    """Get current user information"""
    if not is_logged_in():
        return None
    user_id = session['user_id']
    return USERS.get(user_id)

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def find_best_response(user_message):
    """Find the best response based on user message keywords"""
    user_message = user_message.lower().strip()
    
    # Check for exact matches first
    for key, data in COLLEGE_KB.items():
        if any(keyword in user_message for keyword in data["keywords"]):
            return data["response"]
    
    # Check for partial matches
    for key, data in COLLEGE_KB.items():
        if any(word in user_message for word in key.split()):
            return data["response"]
    
    # Default response for unrecognized queries
    return "I'm sorry, I don't have information about that. Here are some topics I can help you with:\n\n• Courses offered\n• Department heads\n• Exam timetable\n• Library location\n• Office timings\n• Admission process\n• Fee structure\n• College facilities\n\nPlease ask me about any of these topics!"

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and authentication"""
    if request.method == 'GET':
        # If already logged in, redirect to home
        if is_logged_in():
            return redirect(url_for('home'))
        return render_template('login.html')
    
    # Handle POST request
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    remember = request.form.get('remember') == 'on'
    
    # Validate input
    if not username or not password:
        return render_template('login.html', error='Please fill in all fields')
    
    # Check if user exists
    user = None
    user_email = None
    for email, user_data in USERS.items():
        if user_data['username'] == username or email == username:
            user = user_data
            user_email = email
            break
    
    if not user or not verify_password(password, user['password']):
        return render_template('login.html', error='Invalid username or password')
    
    # Login successful
    session['user_id'] = user_email
    session['username'] = user['username']
    session['user_type'] = user['userType']
    
    if remember:
        session.permanent = True
    
    # Redirect to home page
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'GET':
        return render_template('register.html')
    
    # Handle POST request
    firstName = request.form.get('firstName', '').strip()
    lastName = request.form.get('lastName', '').strip()
    email = request.form.get('email', '').strip().lower()
    username = request.form.get('username', '').strip()
    userType = request.form.get('userType', '')
    password = request.form.get('password', '')
    confirmPassword = request.form.get('confirmPassword', '')
    agreeTerms = request.form.get('agreeTerms') == 'on'
    
    # Validate input
    errors = []
    
    if not firstName:
        errors.append('First name is required')
    if not lastName:
        errors.append('Last name is required')
    if not email:
        errors.append('Email is required')
    elif '@' not in email:
        errors.append('Invalid email format')
    elif email in USERS:
        errors.append('Email already registered')
    
    if not username:
        errors.append('Username is required')
    elif len(username) < 3:
        errors.append('Username must be at least 3 characters')
    else:
        # Check if username already exists
        for user_data in USERS.values():
            if user_data['username'] == username:
                errors.append('Username already taken')
                break
    
    if not userType:
        errors.append('Please select a user type')
    if not password:
        errors.append('Password is required')
    elif len(password) < 6:
        errors.append('Password must be at least 6 characters')
    if password != confirmPassword:
        errors.append('Passwords do not match')
    if not agreeTerms:
        errors.append('You must agree to the terms and conditions')
    
    if errors:
        return render_template('register.html', error='; '.join(errors))
    
    # Create new user
    USERS[email] = {
        'username': username,
        'email': email,
        'password': hash_password(password),
        'firstName': firstName,
        'lastName': lastName,
        'userType': userType,
        'created_at': datetime.now().isoformat()
    }
    
    return render_template('register.html', success='Account created successfully! Please log in.')

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@require_auth
def home():
    """Render the homepage with chatbot interface"""
    user = get_current_user()
    return render_template('index.html', user=user)

@app.route('/chat', methods=['POST'])
@require_auth
def chat():
    """Handle chat messages from the frontend"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': 'Please enter a message'
            }), 400
        
        # Get bot response
        bot_response = find_best_response(user_message)
        
        # Return response
        return jsonify({
            'status': 'success',
            'message': bot_response,
            'timestamp': datetime.now().strftime('%H:%M')
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Sorry, something went wrong. Please try again.'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
