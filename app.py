from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy.exc import IntegrityError
from utils import generate_quiz
from werkzeug.utils import secure_filename
import os, sqlite3, json

# Set up the Flask app to use the instance folder.
app = Flask(__name__, instance_relative_config=True)
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Use the database file located in the instance folder.
db_path = os.path.join(app.instance_path, 'site.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['JWT_SECRET_KEY'] = 'supersecretkey'
app.config['SECRET_KEY'] = 'another_secret_key'

# Folder for storing uploaded resumes.
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# --------------------------------------------------
# Ensure the database is initialized if missing.
def ensure_db_initialized():
    need_init = False
    if not os.path.exists(db_path):
        need_init = True
    else:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users'")
        if not cursor.fetchone():
            need_init = True
        conn.close()

    if need_init:
        print("Database not properly initialized. Running schema initialization.")
        with open('schema.sql', 'r') as f:
            sql_script = f.read()
        conn = sqlite3.connect(db_path)
        commands = sql_script.split(';')
        for command in commands:
            cmd = command.strip()
            if cmd.lower().startswith("create table sqlite_sequence"):
                print("Skipping sqlite_sequence table creation.")
                continue
            if cmd:
                try:
                    conn.execute(cmd)
                except Exception as e:
                    print(f"Error executing command:\n{cmd}\nError: {e}")
        conn.commit()
        conn.close()


ensure_db_initialized()


# --------------------------------------------------
# SQLAlchemy Models (mapping to our updated schema)
# --------------------------------------------------
class User(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String, nullable=False)  # 'candidate', 'company', 'freelancer'
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)


class Company(db.Model):
    __tablename__ = 'Companies'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String, nullable=False)
    industry = db.Column(db.String)


class JobPosting(db.Model):
    __tablename__ = 'JobPostings'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)  # New column for job description
    required_skills = db.Column(db.Text)
    experience = db.Column(db.String)  # New column for required experience
    status = db.Column(db.String)  # 'Open', 'Closed', 'Draft'


class Application(db.Model):
    __tablename__ = 'Applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, nullable=False)
    candidate_id = db.Column(db.Integer, nullable=False)
    resume_path = db.Column(db.String)  # New column for resume file path
    status = db.Column(db.String)  # 'Pending', 'Accepted', 'Rejected'


# --------------------------------------------------
# Endpoints
# --------------------------------------------------

# Home page shows a professional project summary.
@app.route('/')
def home():
    company_summary = """
    <strong>Project Summary:</strong><br>
    This project aims to develop an AI-powered recruitment platform that streamlines the hiring process for companies and recruiters.
    The platform will enable companies and both technical and non-technical recruiters to register, along with job candidates.
    When a company posts a job vacancy—such as hiring a software engineer—the system will leverage AI-driven assessments to filter 
    and shortlist candidates. The shortlisted candidates will then be interviewed by experienced recruiters registered on the platform.
    <br><br>
    The platform will operate on a <em>B2B model</em>, where companies pay for recruitment services, and recruiters are compensated 
    per interview conducted. AI will be utilized for candidate evaluation, test monitoring, and screening, ensuring an efficient, 
    unbiased, and data-driven hiring process. By automating candidate screening and leveraging experienced recruiters, this solution 
    will significantly reduce the hiring burden on companies while improving recruitment speed and efficiency.
    """
    return render_template('index.html', company_summary=company_summary)


# Signup endpoint with exception handling.
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, password_hash=hashed_password, user_type=user_type)
        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account with this email already exists. Please try signing in.", "danger")
            return redirect(url_for('signup'))
        except Exception as e:
            db.session.rollback()
            if app.debug:
                flash(f"Unexpected error: {str(e)}", "danger")
            else:
                flash("An unexpected error occurred. Please try again later.", "danger")
            return redirect(url_for('signup'))
        flash('User created successfully. Please sign in.', 'success')
        return redirect(url_for('signin'))
    return render_template('signup.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_type'] = user.user_type
            flash('Signed in successfully.', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials.', 'danger')
    return render_template('signin.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))


@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        flash('Please sign in first.', 'warning')
        return redirect(url_for('signin'))
    quiz_data = generate_quiz()
    return render_template('quiz.html', quiz=quiz_data)


@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        flash('Please sign in first.', 'warning')
        return redirect(url_for('signin'))
    answers_json = request.form.get('answers')
    try:
        answers = json.loads(answers_json)
    except Exception:
        answers = []
    score = sum(1 for q in answers if q.get('correct'))
    flash(f'Quiz submitted successfully. Your score: {score}', 'success')
    return redirect(url_for('quiz'))


# Company: Post Job endpoint.
@app.route('/company/post_job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session.get('user_type') != 'company':
        flash("Unauthorized access", "danger")
        return redirect(url_for('signin'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        required_skills = request.form['required_skills']
        experience = request.form['experience']
        job = JobPosting(company_id=session['user_id'], title=title,
                         description=description, required_skills=required_skills,
                         experience=experience, status="Open")
        db.session.add(job)
        db.session.commit()
        flash("Job posted successfully", "success")
        return redirect(url_for('jobs'))
    return render_template('post_job.html')


# Candidate: View Jobs.
@app.route('/jobs')
def jobs():
    jobs_list = JobPosting.query.filter_by(status="Open").all()
    return render_template('jobs.html', jobs=jobs_list)


# Candidate: Apply for a Job.
@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply(job_id):
    if 'user_id' not in session or session.get('user_type') != 'candidate':
        flash("Unauthorized access", "danger")
        return redirect(url_for('signin'))
    job = JobPosting.query.get_or_404(job_id)
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)
        file = request.files['resume']
        if file.filename == '':
            flash("No selected file", "danger")
            return redirect(request.url)
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        application = Application(job_id=job_id, candidate_id=session['user_id'],
                                  resume_path=upload_path, status="Pending")
        db.session.add(application)
        db.session.commit()
        flash("Application submitted successfully", "success")
        return redirect(url_for('applied_jobs'))
    return render_template('apply.html', job=job)


# Candidate: View Applied Jobs.
@app.route('/applied_jobs')
def applied_jobs():
    if 'user_id' not in session or session.get('user_type') != 'candidate':
        flash("Unauthorized access", "danger")
        return redirect(url_for('signin'))
    applications = Application.query.filter_by(candidate_id=session['user_id']).all()
    return render_template('applied_jobs.html', applications=applications)


if __name__ == '__main__':
    app.run(debug=True)
