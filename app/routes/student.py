from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models import Menu, MealBooking, Payment, Feedback, Announcement
from app.routes.auth import role_required
from app.utils import generate_booking_qr
from datetime import datetime, date, timedelta
from sqlalchemy import func

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    """Student dashboard"""
    today = date.today()
    
    # Get today's menu
    todays_menu = Menu.query.filter_by(date=today).all()
    
    # Get upcoming bookings
    upcoming_bookings = MealBooking.query.filter(
        MealBooking.user_id == current_user.id,
        MealBooking.booking_date >= today,
        MealBooking.status == 'booked'
    ).order_by(MealBooking.booking_date).limit(5).all()
    
    # Calculate current month's dues
    current_month = today.strftime('%B')
    current_year = today.year
    
    total_bookings = MealBooking.query.filter(
        MealBooking.user_id == current_user.id,
        func.strftime('%Y', MealBooking.booking_date) == str(current_year),
        func.strftime('%m', MealBooking.booking_date) == today.strftime('%m'),
        MealBooking.status.in_(['booked', 'consumed'])
    ).all()
    
    total_due = sum([booking.price for booking in total_bookings])
    
    total_paid = db.session.query(func.sum(Payment.amount)).filter(
        Payment.user_id == current_user.id,
        Payment.month == current_month,
        Payment.year == current_year,
        Payment.status == 'completed'
    ).scalar() or 0
    
    balance = total_due - total_paid
    
    # Get active announcements
    announcements = Announcement.query.filter(
        Announcement.is_active == True,
        Announcement.target_role.in_(['all', 'student'])
    ).filter(
        db.or_(
            Announcement.expires_at == None,
            Announcement.expires_at > datetime.utcnow()
        )
    ).order_by(Announcement.created_at.desc()).limit(5).all()
    
    return render_template('student/dashboard.html',
                         todays_menu=todays_menu,
                         upcoming_bookings=upcoming_bookings,
                         balance=balance,
                         announcements=announcements)

@student_bp.route('/menu')
@login_required
@role_required('student')
def view_menu():
    """View weekly menu"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    menus = Menu.query.filter(
        Menu.date >= week_start,
        Menu.date <= week_end
    ).order_by(Menu.date, Menu.meal_type).all()
    
    # Organize by date and meal type
    menu_dict = {}
    for menu in menus:
        if menu.date not in menu_dict:
            menu_dict[menu.date] = {}
        menu_dict[menu.date][menu.meal_type] = menu
    
    # Create list of dates for the week
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    
    return render_template('student/menu.html', 
                         menu_dict=menu_dict, 
                         week_start=week_start, 
                         week_end=week_end,
                         week_dates=week_dates)

@student_bp.route('/book-meal', methods=['GET', 'POST'])
@login_required
@role_required('student')
def book_meal():
    """Book a meal"""
    if request.method == 'POST':
        booking_date_str = request.form.get('booking_date')
        meal_type = request.form.get('meal_type')
        
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        
        # Validation
        if booking_date < date.today():
            flash('Cannot book meals for past dates.', 'danger')
            return redirect(url_for('student.book_meal'))
        
        # Check for duplicate booking
        existing_booking = MealBooking.query.filter_by(
            user_id=current_user.id,
            booking_date=booking_date,
            meal_type=meal_type
        ).filter(MealBooking.status.in_(['booked', 'consumed'])).first()
        
        if existing_booking:
            flash('You have already booked this meal.', 'warning')
            return redirect(url_for('student.book_meal'))
        
        # Get menu and price
        menu = Menu.query.filter_by(date=booking_date, meal_type=meal_type).first()
        
        # Default prices
        prices = {'breakfast': 30.0, 'lunch': 50.0, 'dinner': 45.0}
        price = prices.get(meal_type, 40.0)
        
        # Create booking
        booking = MealBooking(
            user_id=current_user.id,
            menu_id=menu.id if menu else None,
            booking_date=booking_date,
            meal_type=meal_type,
            status='booked',
            price=price
        )
        booking.generate_token()
        
        db.session.add(booking)
        db.session.commit()
        
        flash(f'Meal booked successfully! Your token: {booking.token}', 'success')
        return redirect(url_for('student.my_bookings'))
    
    # GET request
    today = date.today()
    next_week = today + timedelta(days=7)
    
    menus = Menu.query.filter(
        Menu.date >= today,
        Menu.date <= next_week
    ).order_by(Menu.date, Menu.meal_type).all()
    
    return render_template('student/book_meal.html', menus=menus, today=today)

@student_bp.route('/my-bookings')
@login_required
@role_required('student')
def my_bookings():
    """View all bookings"""
    page = request.args.get('page', 1, type=int)
    today = date.today()
    
    bookings = MealBooking.query.filter_by(user_id=current_user.id)\
        .order_by(MealBooking.booking_date.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    # Generate QR codes for active bookings
    for booking in bookings.items:
        if booking.status == 'booked' and booking.booking_date >= today:
            booking.qr_code = generate_booking_qr(
                booking.token,
                {
                    'date': booking.booking_date,
                    'meal_type': booking.meal_type,
                    'student': current_user.full_name
                }
            )
        else:
            booking.qr_code = None
    
    return render_template('student/my_bookings.html', bookings=bookings, today=today)

@student_bp.route('/cancel-booking/<int:booking_id>')
@login_required
@role_required('student')
def cancel_booking(booking_id):
    """Cancel a booking"""
    booking = MealBooking.query.get_or_404(booking_id)
    
    # Check ownership
    if booking.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('student.my_bookings'))
    
    # Check if can cancel (at least 1 day before)
    if booking.booking_date <= date.today():
        flash('Cannot cancel meals on or after the booking date.', 'danger')
        return redirect(url_for('student.my_bookings'))
    
    if booking.status != 'booked':
        flash('This booking cannot be cancelled.', 'warning')
        return redirect(url_for('student.my_bookings'))
    
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('student.my_bookings'))

@student_bp.route('/payments')
@login_required
@role_required('student')
def payments():
    """View payment history"""
    page = request.args.get('page', 1, type=int)
    
    payments = Payment.query.filter_by(user_id=current_user.id)\
        .order_by(Payment.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    # Calculate summary
    total_paid = db.session.query(func.sum(Payment.amount)).filter(
        Payment.user_id == current_user.id,
        Payment.status == 'completed'
    ).scalar() or 0
    
    total_bookings = MealBooking.query.filter(
        MealBooking.user_id == current_user.id,
        MealBooking.status.in_(['booked', 'consumed'])
    ).all()
    
    total_due = sum([booking.price for booking in total_bookings])
    balance = total_due - total_paid
    
    return render_template('student/payments.html', 
                         payments=payments,
                         total_paid=total_paid,
                         total_due=total_due,
                         balance=balance)

@student_bp.route('/feedback', methods=['GET', 'POST'])
@login_required
@role_required('student')
def feedback():
    """Submit feedback or view feedback history"""
    if request.method == 'POST':
        feedback_type = request.form.get('feedback_type')
        subject = request.form.get('subject')
        message = request.form.get('message')
        rating = request.form.get('rating', type=int)
        
        new_feedback = Feedback(
            user_id=current_user.id,
            feedback_type=feedback_type,
            subject=subject,
            message=message,
            rating=rating,
            status='pending'
        )
        
        db.session.add(new_feedback)
        db.session.commit()
        
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('student.feedback'))
    
    # GET request - show feedback history
    page = request.args.get('page', 1, type=int)
    
    feedbacks = Feedback.query.filter_by(user_id=current_user.id)\
        .order_by(Feedback.created_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('student/feedback.html', feedbacks=feedbacks)

@student_bp.route('/announcements')
@login_required
@role_required('student')
def announcements():
    """View all active announcements"""
    announcements = Announcement.query.filter(
        Announcement.is_active == True,
        Announcement.target_role.in_(['all', 'student'])
    ).filter(
        db.or_(
            Announcement.expires_at == None,
            Announcement.expires_at > datetime.utcnow()
        )
    ).order_by(Announcement.created_at.desc()).all()
    
    return render_template('student/announcements.html', announcements=announcements)
