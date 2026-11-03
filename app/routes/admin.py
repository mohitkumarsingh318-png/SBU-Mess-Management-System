from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file, make_response
from flask_login import login_required, current_user
from app import db
from app.models import User, Menu, MealBooking, Payment, Feedback, InventoryItem, Announcement, MealPlan
from app.routes.auth import role_required
from app.utils import generate_daily_report_pdf, generate_monthly_report_pdf
from datetime import datetime, date, timedelta
from sqlalchemy import func
import secrets

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    """Admin dashboard with analytics"""
    today = date.today()
    
    # Total active students
    total_students = User.query.filter_by(role='student', is_active=True).count()
    
    # Today's meal counts
    today_breakfast = MealBooking.query.filter(
        MealBooking.booking_date == today,
        MealBooking.meal_type == 'breakfast',
        MealBooking.status.in_(['booked', 'consumed'])
    ).count()
    
    today_lunch = MealBooking.query.filter(
        MealBooking.booking_date == today,
        MealBooking.meal_type == 'lunch',
        MealBooking.status.in_(['booked', 'consumed'])
    ).count()
    
    today_dinner = MealBooking.query.filter(
        MealBooking.booking_date == today,
        MealBooking.meal_type == 'dinner',
        MealBooking.status.in_(['booked', 'consumed'])
    ).count()
    
    # This month's revenue
    current_month = today.strftime('%B')
    current_year = today.year
    
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.month == current_month,
        Payment.year == current_year,
        Payment.status == 'completed'
    ).scalar() or 0
    
    # Low stock items count
    low_stock_count = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.min_threshold
    ).count()
    
    # Average feedback rating
    avg_rating = db.session.query(func.avg(Feedback.rating)).filter(
        Feedback.rating != None
    ).scalar() or 0
    
    # Recent feedback
    recent_feedback = Feedback.query.filter_by(status='pending')\
        .order_by(Feedback.created_at.desc()).limit(5).all()
    
    # Low stock items
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.min_threshold
    ).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         today_breakfast=today_breakfast,
                         today_lunch=today_lunch,
                         today_dinner=today_dinner,
                         monthly_revenue=monthly_revenue,
                         low_stock_count=low_stock_count,
                         avg_rating=round(avg_rating, 2),
                         recent_feedback=recent_feedback,
                         low_stock_items=low_stock_items)

# Menu Management
@admin_bp.route('/menu')
@login_required
@role_required('admin')
def menu_management():
    """View and manage menus"""
    week = request.args.get('week', 0, type=int)
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week)
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
    
    return render_template('admin/menu_management.html', 
                         menu_dict=menu_dict,
                         week_start=week_start,
                         week_end=week_end,
                         current_week=week,
                         week_dates=week_dates)

@admin_bp.route('/menu/add', methods=['POST'])
@login_required
@role_required('admin')
def add_menu():
    """Add menu item"""
    menu_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    meal_type = request.form.get('meal_type')
    items = request.form.get('items')
    special_note = request.form.get('special_note', '')
    is_special = request.form.get('is_special') == 'on'
    
    # Check if menu already exists
    existing = Menu.query.filter_by(date=menu_date, meal_type=meal_type).first()
    
    if existing:
        # Update existing menu
        existing.items = items
        existing.special_note = special_note
        existing.is_special = is_special
        flash('Menu updated successfully!', 'success')
    else:
        # Create new menu
        menu = Menu(
            date=menu_date,
            meal_type=meal_type,
            items=items,
            special_note=special_note,
            is_special=is_special
        )
        db.session.add(menu)
        flash('Menu added successfully!', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.menu_management'))

@admin_bp.route('/menu/delete/<int:menu_id>')
@login_required
@role_required('admin')
def delete_menu(menu_id):
    """Delete menu item"""
    menu = Menu.query.get_or_404(menu_id)
    db.session.delete(menu)
    db.session.commit()
    flash('Menu deleted successfully!', 'success')
    return redirect(url_for('admin.menu_management'))

# User Management
@admin_bp.route('/users')
@login_required
@role_required('admin')
def user_management():
    """Manage users"""
    role_filter = request.args.get('role', 'all')
    if role_filter not in ('all', 'student', 'staff', 'admin'):
        role_filter = 'all'
    search = request.args.get('search', '')
    
    query = User.query
    
    if role_filter != 'all':
        query = query.filter_by(role=role_filter)
    
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.full_name.contains(search),
                User.email.contains(search),
                User.roll_number.contains(search)
            )
        )
    
    users = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/user_management.html', users=users, role_filter=role_filter, search=search)

@admin_bp.route('/users/add', methods=['POST'])
@login_required
@role_required('admin')
def add_user():
    """Add a student or staff account."""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    roll_number = request.form.get('roll_number', '').strip() or None
    role = request.form.get('role', '')

    if role not in ('student', 'staff') or not all((username, email, full_name)):
        flash('Enter a name, username, email, and a valid student or staff role.', 'danger')
        return redirect(url_for('admin.user_management'))
    if len(password) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return redirect(url_for('admin.user_management'))
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('admin.user_management'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'danger')
        return redirect(url_for('admin.user_management'))
    if roll_number and User.query.filter_by(roll_number=roll_number).first():
        flash('Roll number already exists.', 'danger')
        return redirect(url_for('admin.user_management'))

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        phone=phone,
        roll_number=roll_number,
        role=role
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    flash(f'{role.capitalize()} user created successfully!', 'success')
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/users/update/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def update_user(user_id):
    """Update a student or staff account."""
    user = User.query.get_or_404(user_id)
    if user.role not in ('student', 'staff'):
        flash('Administrator accounts cannot be edited here.', 'warning')
        return redirect(url_for('admin.user_management'))

    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    roll_number = request.form.get('roll_number', '').strip() or None
    role = request.form.get('role', '')
    if not full_name or not email or role not in ('student', 'staff'):
        flash('Name, email, and a valid role are required.', 'danger')
        return redirect(url_for('admin.user_management'))

    duplicate_email = User.query.filter(User.email == email, User.id != user.id).first()
    duplicate_roll = User.query.filter(
        User.roll_number == roll_number,
        User.id != user.id
    ).first() if roll_number else None
    if duplicate_email:
        flash('Email already belongs to another account.', 'danger')
        return redirect(url_for('admin.user_management'))
    if duplicate_roll:
        flash('Roll number already belongs to another account.', 'danger')
        return redirect(url_for('admin.user_management'))

    user.full_name = full_name
    user.email = email
    user.phone = phone or None
    user.roll_number = roll_number
    user.role = role
    db.session.commit()
    flash(f'{role.capitalize()} account updated successfully.', 'success')
    return redirect(url_for('admin.user_management', role=role))

@admin_bp.route('/users/toggle-active/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user_active(user_id):
    """Toggle user active status."""
    user = User.query.get_or_404(user_id)
    if user.role not in ('student', 'staff'):
        flash('Administrator accounts cannot be deactivated here.', 'warning')
        return redirect(url_for('admin.user_management'))
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.user_management'))

    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} {status} successfully!', 'success')
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    """Delete an account only when it has no related history."""
    user = User.query.get_or_404(user_id)
    if user.role not in ('student', 'staff'):
        flash('Administrator accounts cannot be deleted here.', 'warning')
        return redirect(url_for('admin.user_management'))

    has_history = any((
        MealBooking.query.filter_by(user_id=user.id).first(),
        MealBooking.query.filter_by(verified_by=user.id).first(),
        Payment.query.filter_by(user_id=user.id).first(),
        Feedback.query.filter_by(user_id=user.id).first(),
        InventoryItem.query.filter_by(updated_by=user.id).first(),
        Announcement.query.filter_by(created_by=user.id).first()
    ))
    if has_history:
        flash('This account has booking, payment, or feedback history. Deactivate it to preserve records.', 'warning')
        return redirect(url_for('admin.user_management', role=user.role))

    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} deleted successfully!', 'success')
    return redirect(url_for('admin.user_management'))

# Bookings Management
@admin_bp.route('/bookings')
@login_required
@role_required('admin')
def bookings():
    """View all bookings"""
    booking_date = request.args.get('date')
    meal_type = request.args.get('meal_type', 'all')
    status = request.args.get('status', 'all')
    
    query = MealBooking.query
    
    if booking_date:
        query = query.filter_by(booking_date=datetime.strptime(booking_date, '%Y-%m-%d').date())
    
    if meal_type != 'all':
        query = query.filter_by(meal_type=meal_type)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    bookings = query.order_by(MealBooking.booking_date.desc()).limit(100).all()
    
    return render_template('admin/bookings.html', 
                         bookings=bookings,
                         booking_date=booking_date,
                         meal_type=meal_type,
                         status=status)

# Payment Management
@admin_bp.route('/payments')
@login_required
@role_required('admin')
def payments():
    """View and manage payments"""
    month_filter = request.args.get('month', datetime.now().strftime('%B'))
    year_filter = request.args.get('year', datetime.now().year, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Payment.query
    
    if month_filter != 'all':
        query = query.filter_by(month=month_filter)
    
    if year_filter:
        query = query.filter_by(year=year_filter)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    payments = query.order_by(Payment.created_at.desc()).all()
    
    total_amount = sum([p.amount for p in payments if p.status == 'completed'])
    
    return render_template('admin/payments.html',
                         payments=payments,
                         total_amount=total_amount,
                         month_filter=month_filter,
                         year_filter=year_filter,
                         status_filter=status_filter)

@admin_bp.route('/payments/add', methods=['POST'])
@login_required
@role_required('admin')
def add_payment():
    """Record a payment"""
    user_id = request.form.get('user_id', type=int)
    amount = request.form.get('amount', type=float)
    payment_type = request.form.get('payment_type')
    payment_method = request.form.get('payment_method')
    month = request.form.get('month')
    year = request.form.get('year', type=int)
    notes = request.form.get('notes', '')
    
    payment = Payment(
        user_id=user_id,
        amount=amount,
        payment_type=payment_type,
        payment_method=payment_method,
        transaction_id=f'TXN{secrets.token_hex(8).upper()}',
        status='completed',
        month=month,
        year=year,
        notes=notes
    )
    
    db.session.add(payment)
    db.session.commit()
    
    flash('Payment recorded successfully!', 'success')
    return redirect(url_for('admin.payments'))

# Feedback Management
@admin_bp.route('/feedback')
@login_required
@role_required('admin')
def feedback_management():
    """View and manage feedback"""
    status_filter = request.args.get('status', 'all')
    feedback_type = request.args.get('type', 'all')
    
    query = Feedback.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if feedback_type != 'all':
        query = query.filter_by(feedback_type=feedback_type)
    
    feedbacks = query.order_by(Feedback.created_at.desc()).all()
    
    return render_template('admin/feedback_management.html',
                         feedbacks=feedbacks,
                         status_filter=status_filter,
                         feedback_type=feedback_type)

@admin_bp.route('/feedback/respond/<int:feedback_id>', methods=['POST'])
@login_required
@role_required('admin')
def respond_feedback(feedback_id):
    """Respond to feedback"""
    feedback = Feedback.query.get_or_404(feedback_id)
    
    response = request.form.get('response')
    new_status = request.form.get('status')
    
    feedback.admin_response = response
    feedback.status = new_status
    
    if new_status == 'resolved':
        feedback.resolved_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Feedback updated successfully!', 'success')
    return redirect(url_for('admin.feedback_management'))

# Inventory Management
@admin_bp.route('/inventory')
@login_required
@role_required('admin')
def inventory_management():
    """Manage inventory"""
    category_filter = request.args.get('category', 'all')
    
    query = InventoryItem.query
    
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    items = query.order_by(InventoryItem.category, InventoryItem.name).all()
    
    # Get unique categories
    categories = db.session.query(InventoryItem.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('admin/inventory_management.html',
                         items=items,
                         categories=categories,
                         category_filter=category_filter)

@admin_bp.route('/inventory/add', methods=['POST'])
@login_required
@role_required('admin')
def add_inventory_item():
    """Add inventory item"""
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    quantity = request.form.get('quantity', type=float)
    unit = request.form.get('unit', '').strip()
    min_threshold = request.form.get('min_threshold', type=float)
    unit_price = request.form.get('unit_price', default=0, type=float)
    if not name or not category or not unit or quantity is None or min_threshold is None or unit_price is None:
        flash('Complete all required fields with valid numbers.', 'danger')
        return redirect(url_for('admin.inventory_management'))
    if min(quantity, min_threshold, unit_price) < 0:
        flash('Quantity, threshold, and unit price cannot be negative.', 'danger')
        return redirect(url_for('admin.inventory_management'))
    
    item = InventoryItem(
        name=name,
        category=category,
        quantity=quantity,
        unit=unit,
        min_threshold=min_threshold,
        unit_price=unit_price,
        updated_by=current_user.id
    )
    
    db.session.add(item)
    db.session.commit()
    
    flash('Inventory item added successfully!', 'success')
    return redirect(url_for('admin.inventory_management'))

@admin_bp.route('/inventory/update/<int:item_id>', methods=['POST'])
@login_required
@role_required('admin')
def update_inventory_item(item_id):
    """Update inventory item"""
    item = InventoryItem.query.get_or_404(item_id)

    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    quantity = request.form.get('quantity', type=float)
    unit = request.form.get('unit', '').strip()
    min_threshold = request.form.get('min_threshold', type=float)
    unit_price = request.form.get('unit_price', default=0, type=float)
    if not name or not category or not unit or quantity is None or min_threshold is None or unit_price is None:
        flash('Complete all required fields with valid numbers.', 'danger')
        return redirect(url_for('admin.inventory_management'))
    if min(quantity, min_threshold, unit_price) < 0:
        flash('Quantity, threshold, and unit price cannot be negative.', 'danger')
        return redirect(url_for('admin.inventory_management'))

    item.name = name
    item.category = category
    item.quantity = quantity
    item.unit = unit
    item.min_threshold = min_threshold
    item.unit_price = unit_price
    item.updated_by = current_user.id
    item.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    flash('Inventory item updated successfully!', 'success')
    return redirect(url_for('admin.inventory_management'))

@admin_bp.route('/inventory/delete/<int:item_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_inventory_item(item_id):
    """Delete inventory item"""
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    flash('Inventory item deleted successfully!', 'success')
    return redirect(url_for('admin.inventory_management'))

# Announcements Management
@admin_bp.route('/announcements')
@login_required
@role_required('admin')
def announcements():
    """Manage announcements"""
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=announcements)

@admin_bp.route('/announcements/add', methods=['POST'])
@login_required
@role_required('admin')
def add_announcement():
    """Add announcement"""
    title = request.form.get('title')
    content = request.form.get('content')
    priority = request.form.get('priority')
    target_role = request.form.get('target_role')
    expires_at_str = request.form.get('expires_at')
    
    expires_at = None
    if expires_at_str:
        expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d')
    
    announcement = Announcement(
        title=title,
        content=content,
        priority=priority,
        target_role=target_role,
        expires_at=expires_at,
        is_active=True,
        created_by=current_user.id
    )
    
    db.session.add(announcement)
    db.session.commit()
    
    flash('Announcement created successfully!', 'success')
    return redirect(url_for('admin.announcements'))

@admin_bp.route('/announcements/toggle/<int:announcement_id>')
@login_required
@role_required('admin')
def toggle_announcement(announcement_id):
    """Toggle announcement active status"""
    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = not announcement.is_active
    db.session.commit()
    
    status = 'activated' if announcement.is_active else 'deactivated'
    flash(f'Announcement {status} successfully!', 'success')
    return redirect(url_for('admin.announcements'))

@admin_bp.route('/announcements/delete/<int:announcement_id>')
@login_required
@role_required('admin')
def delete_announcement(announcement_id):
    """Delete announcement"""
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    
    flash('Announcement deleted successfully!', 'success')
    return redirect(url_for('admin.announcements'))

@admin_bp.route('/contact')
@login_required
@role_required('admin')
def contact():
    """Admin contact information"""
    support_contact = {
        'name': 'Mess Administrator',
        'email': 'mess-admin@example.com',
        'phone': '+91-9876543210',
        'office': 'Mess Office, Hostel Block A',
        'working_hours': 'Monday - Friday, 09:00 AM - 05:00 PM',
        'note': 'For urgent issues, please call the mess office during working hours.'
    }
    return render_template('admin/contact.html', support_contact=support_contact)

# Reports
@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
    """Generate reports"""
    report_type = request.args.get('type', 'daily')
    report_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    
    target_date = datetime.strptime(report_date, '%Y-%m-%d').date()
    
    if report_type == 'daily':
        bookings = MealBooking.query.filter_by(booking_date=target_date).all()
        
        stats = {
            'date': target_date,
            'total_bookings': len(bookings),
            'breakfast': len([b for b in bookings if b.meal_type == 'breakfast']),
            'lunch': len([b for b in bookings if b.meal_type == 'lunch']),
            'dinner': len([b for b in bookings if b.meal_type == 'dinner']),
            'consumed': len([b for b in bookings if b.status == 'consumed']),
            'cancelled': len([b for b in bookings if b.status == 'cancelled']),
            'pending': len([b for b in bookings if b.status == 'booked'])
        }
        
        return render_template('admin/daily_report.html', stats=stats, report_date=report_date)
    
    elif report_type == 'monthly':
        month = target_date.month
        year = target_date.year
        
        bookings = MealBooking.query.filter(
            func.strftime('%Y', MealBooking.booking_date) == str(year),
            func.strftime('%m', MealBooking.booking_date) == f'{month:02d}'
        ).all()
        
        payments = Payment.query.filter_by(
            month=target_date.strftime('%B'),
            year=year,
            status='completed'
        ).all()
        
        stats = {
            'month': target_date.strftime('%B %Y'),
            'total_bookings': len(bookings),
            'total_revenue': sum([p.amount for p in payments]),
            'total_students': User.query.filter_by(role='student', is_active=True).count()
        }
        
        return render_template('admin/monthly_report.html', stats=stats, report_date=report_date)
    
    return render_template('admin/reports.html')

@admin_bp.route('/reports/download-daily-pdf')
@login_required
@role_required('admin')
def download_daily_pdf():
    """Download daily report as PDF"""
    report_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    target_date = datetime.strptime(report_date, '%Y-%m-%d').date()
    
    bookings = MealBooking.query.filter_by(booking_date=target_date).all()
    
    stats = {
        'date': target_date,
        'total_bookings': len(bookings),
        'breakfast': len([b for b in bookings if b.meal_type == 'breakfast']),
        'lunch': len([b for b in bookings if b.meal_type == 'lunch']),
        'dinner': len([b for b in bookings if b.meal_type == 'dinner']),
        'consumed': len([b for b in bookings if b.status == 'consumed']),
        'cancelled': len([b for b in bookings if b.status == 'cancelled']),
        'pending': len([b for b in bookings if b.status == 'booked'])
    }
    
    # Generate PDF
    pdf_buffer = generate_daily_report_pdf(stats, report_date)
    
    # Create response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=daily_report_{report_date}.pdf'
    
    return response

@admin_bp.route('/reports/download-monthly-pdf')
@login_required
@role_required('admin')
def download_monthly_pdf():
    """Download monthly report as PDF"""
    report_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    target_date = datetime.strptime(report_date, '%Y-%m-%d').date()
    
    month = target_date.month
    year = target_date.year
    
    bookings = MealBooking.query.filter(
        func.strftime('%Y', MealBooking.booking_date) == str(year),
        func.strftime('%m', MealBooking.booking_date) == f'{month:02d}'
    ).all()
    
    payments = Payment.query.filter_by(
        month=target_date.strftime('%B'),
        year=year,
        status='completed'
    ).all()
    
    stats = {
        'month': target_date.strftime('%B %Y'),
        'total_bookings': len(bookings),
        'total_revenue': sum([p.amount for p in payments]),
        'total_students': User.query.filter_by(role='student', is_active=True).count()
    }
    
    # Generate PDF
    pdf_buffer = generate_monthly_report_pdf(stats, report_date)
    
    # Create response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=monthly_report_{target_date.strftime("%B_%Y")}.pdf'
    
    return response
