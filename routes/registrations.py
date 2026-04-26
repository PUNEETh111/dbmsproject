"""
routes/registrations.py — Registration Routes
------------------------------------------------
Handles student event registration:
  - Register for an event (with TRANSACTION)
  - Unregister from an event
  - View my registrations (JOIN query)
"""

from flask import Blueprint, redirect, url_for, session, flash
from models.registration import Registration
from functools import wraps

# Blueprint for registration routes
registrations_bp = Blueprint('registrations', __name__)


def login_required(f):
    """Decorator: Ensure user is logged in as a student."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'student':
            flash('Please log in as a student to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@registrations_bp.route('/register-event/<int:event_id>', methods=['POST'])
@login_required
def register_for_event(event_id):
    """
    Register the current student for an event.

    Uses a TRANSACTION (BEGIN → INSERT → COMMIT/ROLLBACK).
    The trg_prevent_overbooking TRIGGER fires during INSERT.
    UNIQUE constraint prevents duplicate registration.
    """
    student_id = session['user_id']
    result = Registration.register(student_id, event_id)

    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')

    return redirect(url_for('events.event_detail', event_id=event_id))


@registrations_bp.route('/unregister-event/<int:event_id>', methods=['POST'])
@login_required
def unregister_from_event(event_id):
    """
    Unregister the current student from an event.
    Uses DELETE operation.
    """
    student_id = session['user_id']
    success = Registration.unregister(student_id, event_id)

    if success:
        flash('Successfully unregistered from the event.', 'info')
    else:
        flash('You are not registered for this event.', 'error')

    return redirect(url_for('registrations.my_registrations'))


@registrations_bp.route('/my-registrations')
@login_required
def my_registrations():
    """
    Display all events the current student is registered for.
    Uses JOIN query: REGISTRATION ↔ EVENT ↔ FACULTY.
    """
    from flask import render_template
    student_id = session['user_id']
    registrations = Registration.get_student_registrations(student_id)

    return render_template('my_registrations.html', registrations=registrations)
