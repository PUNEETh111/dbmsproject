"""
routes/auth.py — Authentication Routes
-----------------------------------------
Handles student and faculty login/register/logout.
Uses Flask sessions for simple session-based authentication.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.student import Student
from models.faculty import Faculty

# Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Student login page.
    GET: Render the login form.
    POST: Verify credentials and create session.
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')

        # Look up student by email
        student = Student.find_by_email(email)

        if student and Student.verify_password(student['Password'], password):
            # Create session
            session['user_id'] = student['Student_ID']
            session['user_name'] = student['Name']
            session['user_type'] = 'student'
            flash(f'Welcome back, {student["Name"]}!', 'success')
            return redirect(url_for('events.list_events'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Student registration page.
    GET: Render the registration form.
    POST: Create new student account with USN.
    """
    if request.method == 'POST':
        usn = request.form.get('usn', '').strip()
        name = request.form.get('name', '').strip()
        dept = request.form.get('dept', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # Validation
        if not all([usn, name, dept, email, password]):
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        # Validate USN format (e.g., 1XX21CS001)
        usn_upper = usn.upper().strip()
        if len(usn_upper) < 5:
            flash('Please enter a valid USN.', 'error')
            return render_template('register.html')

        # Create student (INSERT operation)
        student_id = Student.create(usn_upper, name, dept, email, password)

        if student_id:
            # Auto-login after registration
            session['user_id'] = student_id
            session['user_name'] = name
            session['user_type'] = 'student'
            flash('Account created successfully! Welcome!', 'success')
            return redirect(url_for('events.list_events'))
        else:
            flash('An account with this USN or email already exists.', 'error')

    return render_template('register.html')


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Faculty/Admin login page.
    GET: Render admin login form.
    POST: Verify faculty credentials.
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('admin_login.html')

        faculty = Faculty.find_by_email(email)

        if faculty and Faculty.verify_password(faculty['Password'], password):
            session['user_id'] = faculty['Faculty_ID']
            session['user_name'] = faculty['Name']
            session['user_type'] = 'faculty'
            flash(f'Welcome, {faculty["Name"]}!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('admin_login.html')


@auth_bp.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    """
    Faculty/Admin registration page.
    GET: Render admin registration form.
    POST: Create new faculty account.
    """
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dept = request.form.get('dept', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # Validation
        if not all([name, dept, email, password]):
            flash('Please fill in all fields.', 'error')
            return render_template('admin_register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('admin_register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('admin_register.html')

        # Create faculty (INSERT operation)
        faculty_id = Faculty.create(name, dept, email, password)

        if faculty_id:
            # Auto-login after registration
            session['user_id'] = faculty_id
            session['user_name'] = name
            session['user_type'] = 'faculty'
            flash('Admin account created successfully! Welcome!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('An account with this email already exists.', 'error')

    return render_template('admin_register.html')


@auth_bp.route('/logout')
def logout():
    """Clear the session and redirect to home."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))
