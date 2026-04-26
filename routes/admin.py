"""
routes/admin.py — Admin/Faculty Routes
-----------------------------------------
Handles admin panel functionality:
  - Dashboard with event participation summary (VIEW query)
  - Create event (INSERT)
  - Update event (UPDATE)
  - Delete event (DELETE)
  - View registrations per event (JOIN query)
  - Manage all registered students (SELECT ALL)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.event import Event
from models.registration import Registration
from models.student import Student
from functools import wraps

# Blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator: Ensure user is logged in as a valid admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'faculty':
            flash('Please log in as admin to access the admin panel.', 'error')
            return redirect(url_for('auth.admin_login'))

        # Verify admin still exists in DB (handles stale sessions after DB reset)
        from models.faculty import Faculty
        admin = Faculty.find_by_id(session['user_id'])
        if not admin:
            session.clear()
            flash('Your session has expired. Please log in again.', 'error')
            return redirect(url_for('auth.admin_login'))

        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@admin_required
def dashboard():
    """
    Admin dashboard showing event participation summary.
    Uses the vw_event_participation VIEW (JOIN + GROUP BY).
    """
    # Query the VIEW for participation summary
    summary = Event.get_participation_summary()

    # Get events managed by this faculty
    my_events = Event.get_events_by_faculty(session['user_id'])

    # Get participant counts (GROUP BY query)
    counts = Registration.get_participant_counts()

    # Get total students count
    all_students = Student.get_all()

    return render_template(
        'admin/dashboard.html',
        summary=summary,
        my_events=my_events,
        counts=counts,
        total_students=len(all_students)
    )


@admin_bp.route('/students')
@admin_required
def manage_students():
    """
    View all registered students.
    Admin can see USN, Name, Department, Email for every student.
    """
    students = Student.get_all()
    return render_template('admin/students.html', students=students)


@admin_bp.route('/delete-student/<int:student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    """
    Delete a student account.
    Cascading FK deletes related registrations automatically.
    """
    student = Student.find_by_id(student_id)
    if student:
        Student.delete(student_id)
        flash(f'Student "{student["Name"]}" (USN: {student["USN"]}) removed successfully.', 'info')
    else:
        flash('Student not found.', 'error')

    return redirect(url_for('admin.manage_students'))


@admin_bp.route('/create-event', methods=['GET', 'POST'])
@admin_required
def create_event():
    """
    Create a new event.
    GET: Render create event form.
    POST: INSERT new event into database.
    """
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        date = request.form.get('date', '').strip()
        venue = request.form.get('venue', '').strip()
        max_seats = request.form.get('max_seats', '100').strip()

        # Validation
        if not all([name, date, venue]):
            flash('Event name, date, and venue are required.', 'error')
            return render_template('admin/create_event.html')

        try:
            max_seats = int(max_seats)
            if max_seats < 1:
                raise ValueError
        except ValueError:
            flash('Max seats must be a positive number.', 'error')
            return render_template('admin/create_event.html')

        # INSERT operation
        try:
            event_id = Event.create(
                name=name,
                description=description,
                date=date,
                venue=venue,
                max_seats=max_seats,
                faculty_id=session['user_id']
            )
            flash(f'Event "{name}" created successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            flash('Failed to create event. Please log out and log in again.', 'error')
            return render_template('admin/create_event.html')

    return render_template('admin/create_event.html')


@admin_bp.route('/edit-event/<int:event_id>', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    """
    Edit an existing event.
    GET: Render edit form with current values.
    POST: UPDATE event in database.
    """
    event = Event.find_by_id(event_id)

    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        date = request.form.get('date', '').strip()
        venue = request.form.get('venue', '').strip()
        max_seats = request.form.get('max_seats', '100').strip()

        if not all([name, date, venue]):
            flash('Event name, date, and venue are required.', 'error')
            return render_template('admin/edit_event.html', event=event)

        try:
            max_seats = int(max_seats)
            if max_seats < 1:
                raise ValueError
        except ValueError:
            flash('Max seats must be a positive number.', 'error')
            return render_template('admin/edit_event.html', event=event)

        # UPDATE operation
        Event.update(
            event_id=event_id,
            name=name,
            description=description,
            date=date,
            venue=venue,
            max_seats=max_seats
        )

        flash(f'Event "{name}" updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/edit_event.html', event=event)


@admin_bp.route('/delete-event/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    """
    Delete an event.
    Uses DELETE operation. Cascading FK deletes related registrations.
    """
    event = Event.find_by_id(event_id)
    if event:
        Event.delete(event_id)
        flash(f'Event "{event["Name"]}" deleted successfully.', 'info')
    else:
        flash('Event not found.', 'error')

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/event-registrations/<int:event_id>')
@admin_required
def event_registrations(event_id):
    """
    View all students registered for a specific event.
    Uses JOIN query: REGISTRATION ↔ STUDENT.
    """
    event = Event.find_by_id(event_id)

    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('admin.dashboard'))

    # JOIN query to get registered students
    registrations = Registration.get_event_registrations(event_id)

    return render_template(
        'admin/event_registrations.html',
        event=event,
        registrations=registrations
    )
