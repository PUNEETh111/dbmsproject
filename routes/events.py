"""
routes/events.py — Event Routes
---------------------------------
Handles public-facing event pages:
  - Event listing with search/filter
  - Event detail view
"""

from flask import Blueprint, render_template, request, session
from models.event import Event
from models.registration import Registration

# Blueprint for event routes
events_bp = Blueprint('events', __name__)


@events_bp.route('/events')
def list_events():
    """
    Display all events with search functionality.
    Uses JOIN query (EVENT ↔ FACULTY) and subquery for participant count.
    """
    search_query = request.args.get('search', '').strip()

    if search_query:
        events = Event.search(search_query)
    else:
        events = Event.get_all()

    # Check which events the current student is registered for
    registered_event_ids = set()
    if session.get('user_type') == 'student':
        student_regs = Registration.get_student_registrations(session['user_id'])
        registered_event_ids = {reg['Event_ID'] for reg in student_regs}

    return render_template(
        'events.html',
        events=events,
        search_query=search_query,
        registered_event_ids=registered_event_ids
    )


@events_bp.route('/events/<int:event_id>')
def event_detail(event_id):
    """
    Display detailed view of a single event.
    Uses JOIN query to fetch event with faculty name.
    """
    event = Event.find_by_id(event_id)

    if not event:
        return render_template('404.html', message='Event not found.'), 404

    # Check if current student is registered
    is_registered = False
    if session.get('user_type') == 'student':
        is_registered = Registration.is_registered(session['user_id'], event_id)

    return render_template(
        'event_detail.html',
        event=event,
        is_registered=is_registered
    )
