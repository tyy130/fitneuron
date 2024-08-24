import os
from flask import Flask, render_template, request, redirect, url_for, flash, Markup, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate 
from datetime import datetime, timedelta, timezone
import openai
import json
import logging
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fitneuron.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.logger.setLevel(logging.INFO)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

openai.api_key = os.environ.get('OPENAI_API_KEY')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    workouts = db.relationship('Workout', backref='user', lazy='dynamic')

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    fitness_level = db.Column(db.String(20))
    goals = db.Column(db.String(200))
    equipment_access = db.Column(db.String(50))
    gym_name = db.Column(db.String(100))
    workout_frequency = db.Column(db.String(50))
    medical_conditions = db.Column(db.String(200))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    use_metric = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    workout_plan = db.Column(db.Text)
    exercises = db.relationship('ExerciseLog', backref='workout', lazy='dynamic')

class ExerciseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'))
    exercise_name = db.Column(db.String(100))
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    weight = db.Column(db.Float)
    feedback = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def make_aware(naive_datetime):
    if naive_datetime is None:
        return None
    return naive_datetime.replace(tzinfo=timezone.utc) if naive_datetime.tzinfo is None else naive_datetime

@app.route('/')
def index():
    if current_user.is_authenticated:
        recent_activities = get_recent_activities(current_user.id)
        return render_template('index.html', recent_activities=recent_activities)
    return render_template('index.html')

def get_recent_activities(user_id):
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    activities = []
    
    recent_workouts = Workout.query.filter(Workout.user_id == user_id, Workout.date >= thirty_days_ago).order_by(Workout.date.desc()).limit(5).all()
    for workout in recent_workouts:
        activities.append({
            "description": f"Completed a workout",
            "date": workout.date
        })
    
    profile_updates = UserProfile.query.filter(UserProfile.user_id == user_id, UserProfile.updated_at >= thirty_days_ago).order_by(UserProfile.updated_at.desc()).limit(5).all()
    for update in profile_updates:
        activities.append({
            "description": f"Updated profile information",
            "date": update.updated_at
        })
    
    activities.sort(key=lambda x: x['date'], reverse=True)
    
    return activities[:5]

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_password = generate_password_hash(request.form.get('password'))
        new_user = User(username=request.form.get('username'),
                        email=request.form.get('email'),
                        password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
        
        profile.fitness_level = request.form.get('fitness_level')
        profile.goals = request.form.get('goals')
        profile.equipment_access = request.form.get('equipment_access')
        profile.gym_name = request.form.get('gym_name')
        profile.workout_frequency = request.form.get('workout_frequency')
        profile.medical_conditions = request.form.get('medical_conditions')
        
        height_feet = request.form.get('height_feet')
        height_inches = request.form.get('height_inches')
        if height_feet and height_inches:
            profile.height = int(height_feet) * 12 + int(height_inches)
        
        weight = request.form.get('weight')
        if weight:
            profile.weight = float(weight)
        
        profile.use_metric = 'use_metric' in request.form
        
        db.session.add(profile)
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('index'))
    return render_template('profile.html', profile=current_user.profile)

@app.route('/generate_workout')
@login_required
def generate_workout():
    profile = current_user.profile
    if not profile:
        flash('Please complete your profile first')
        return redirect(url_for('profile'))
    
    prompt = f"""
    Generate a personalized workout for a user with the following profile:
    Fitness level: {profile.fitness_level}
    Goals: {profile.goals}
    Equipment access: {profile.equipment_access}
    Workout frequency: {profile.workout_frequency}
    Medical conditions: {profile.medical_conditions}

    The workout should include:
    1. Warm-up exercises (2-3 exercises)
    2. Main workout routine (4-6 exercises)
    3. Cool-down stretches (2-3 exercises)

    For each exercise, provide:
    - Name of the exercise
    - Number of sets and reps or duration
    - Weight in pounds (if applicable)
    - Any special instructions or form tips

    Use imperial units (pounds, feet, inches) for all measurements.

    Format the response as a JSON object with the following structure:
    {{
        "warm_up": [
            {{"name": "Exercise name", "duration": "Duration or reps", "instructions": "Instructions"}}
        ],
        "main_workout": [
            {{"name": "Exercise name", "sets": "Number of sets", "reps": "Number of reps", "weight": "Weight in lbs", "instructions": "Form tips or instructions"}}
        ],
        "cool_down": [
            {{"name": "Exercise name", "duration": "Duration or reps", "instructions": "Instructions"}}
        ]
    }}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional fitness trainer specializing in personalized workout plans. Respond with a JSON object containing the workout plan."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message['content']
        
        # Remove any markdown formatting
        content = content.replace('```json\n', '').replace('\n```', '')
        
        workout_json = json.loads(content)

        # Generate workout intro
        intro = generate_workout_intro(current_user)
        workout_json['intro'] = intro

        # Save the workout to the database
        new_workout = Workout(user_id=current_user.id, date=datetime.now(timezone.utc), workout_plan=json.dumps(workout_json))
        db.session.add(new_workout)
        db.session.commit()

        return render_template('workout.html', workout=workout_json, workout_id=new_workout.id)

    except json.JSONDecodeError as e:
        app.logger.error(f"JSON decode error: {str(e)}")
        return jsonify({"error": "Failed to parse JSON", "raw_content": content}), 500
    except Exception as e:
        app.logger.error(f"Error generating workout: {str(e)}")
        return jsonify({"error": "Failed to generate workout. Please try again later."}), 500

@app.route('/workout/<int:workout_id>')
@login_required
def view_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if workout.user_id != current_user.id:
        abort(403)
    workout_json = json.loads(workout.workout_plan)
    return render_template('workout.html', workout=workout_json, workout_id=workout_id)

@app.route('/log_exercise', methods=['POST'])
@login_required
def log_exercise():
    data = request.json
    exercise_log = ExerciseLog(
        workout_id=data['workout_id'],
        exercise_name=data['exercise_name'],
        sets=data['sets'],
        reps=data['reps'],
        weight=data['weight'],
        feedback=data['feedback']
    )
    db.session.add(exercise_log)
    db.session.commit()
    return jsonify({"status": "success"})
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def generate_workout_intro(user):
    last_workout = Workout.query.filter_by(user_id=user.id).order_by(Workout.date.desc()).first()
    now = datetime.now(timezone.utc)
    if last_workout:
        last_workout_date = make_aware(last_workout.date)
        days_since = (now - last_workout_date).days
        return f"Welcome back! It's been {days_since} days since your last workout. Today, we'll focus on building upon your progress and pushing your limits."
    else:
        return "Welcome to your first workout with FitNeuron! Today, we'll start with a balanced routine to assess your current fitness level and set a baseline for your future workouts."

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)