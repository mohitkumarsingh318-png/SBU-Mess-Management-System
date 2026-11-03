from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models import Menu, MealBooking, InventoryItem, Announcement, User
from app.routes.auth import role_required
from datetime import datetime, date, timedelta
from sqlalchemy import func

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/dashboard')
@login_required
@role_required('staff')
def dashboard():
    """Staff dashboard"""
    today = date.today()
    
    # Get today's meal counts
    breakfast_count = MealBooking.query.filter(
        MealBooking.booking_date == today,
        MealBooking.meal_type == 'breakfast',
        MealBooking.status == 'booked'
    ).count()
    
    lunch_count = MealBooking.query.filter(
        MealBooking.booking_date == today,
        MealBooking.meal_type == 'lunch',
        MealBooking.status == 'booked'
    ).count()
    
    dinner_count = MealBooking.query.filter(
        MealBooking.booking_date == today,
        MealBooking.meal_type == 'dinner',
        MealBooking.status == 'booked'
    ).count()
    
    # Get low stock items
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.min_threshold
    ).all()
    
    # Get today's menu
    todays_menu = Menu.query.filter_by(date=today).all()
    
    return render_template('staff/dashboard.html',
                         breakfast_count=breakfast_count,
                         lunch_count=lunch_count,
                         dinner_count=dinner_count,
                         low_stock_items=low_stock_items,
                         todays_menu=todays_menu)

@staff_bp.route('/verify-meal', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def verify_meal():
    """Verify meal using token"""
    if request.method == 'POST':
        token = request.form.get('token').strip()
        
        booking = MealBooking.query.filter_by(token=token).first()
        
        if not booking:
            flash('Invalid token. Booking not found.', 'danger')
            return redirect(url_for('staff.verify_meal'))
        
        # Check if booking is for today
        if booking.booking_date != date.today():
            flash(f'This booking is for {booking.booking_date.strftime("%Y-%m-%d")}, not today.', 'warning')
            return redirect(url_for('staff.verify_meal'))
        
        # Check booking status
        if booking.status == 'consumed':
            flash('This meal has already been consumed.', 'warning')
            return redirect(url_for('staff.verify_meal'))
        
        if booking.status == 'cancelled':
            flash('This booking has been cancelled.', 'danger')
            return redirect(url_for('staff.verify_meal'))
        
        if booking.status != 'booked':
            flash('Invalid booking status.', 'danger')
            return redirect(url_for('staff.verify_meal'))
        
        # Verify meal
        booking.status = 'consumed'
        booking.verified_at = datetime.utcnow()
        booking.verified_by = current_user.id
        
        db.session.commit()
        
        flash(f'Meal verified successfully for {booking.user.full_name} ({booking.meal_type})!', 'success')
        return redirect(url_for('staff.verify_meal'))
    
    return render_template('staff/verify_meal.html')

@staff_bp.route('/meal-counts')
@login_required
@role_required('staff')
def meal_counts():
    """View meal counts for upcoming days"""
    today = date.today()
    
    # Get counts for next 7 days
    counts = []
    for i in range(7):
        check_date = today + timedelta(days=i)
        
        breakfast = MealBooking.query.filter(
            MealBooking.booking_date == check_date,
            MealBooking.meal_type == 'breakfast',
            MealBooking.status == 'booked'
        ).count()
        
        lunch = MealBooking.query.filter(
            MealBooking.booking_date == check_date,
            MealBooking.meal_type == 'lunch',
            MealBooking.status == 'booked'
        ).count()
        
        dinner = MealBooking.query.filter(
            MealBooking.booking_date == check_date,
            MealBooking.meal_type == 'dinner',
            MealBooking.status == 'booked'
        ).count()
        
        counts.append({
            'date': check_date,
            'breakfast': breakfast,
            'lunch': lunch,
            'dinner': dinner,
            'total': breakfast + lunch + dinner
        })
    
    return render_template('staff/meal_counts.html', counts=counts)

@staff_bp.route('/inventory')
@login_required
@role_required('staff')
def inventory():
    """View inventory"""
    items = InventoryItem.query.order_by(InventoryItem.category, InventoryItem.name).all()
    
    # Group by category
    inventory_by_category = {}
    for item in items:
        category = item.category or 'Uncategorized'
        if category not in inventory_by_category:
            inventory_by_category[category] = []
        inventory_by_category[category].append(item)
    
    return render_template('staff/inventory.html', inventory_by_category=inventory_by_category)

@staff_bp.route('/inventory/update/<int:item_id>', methods=['POST'])
@login_required
@role_required('staff')
def update_inventory(item_id):
    """Update inventory item quantity"""
    item = InventoryItem.query.get_or_404(item_id)

    action = request.form.get('action')
    quantity = request.form.get('quantity', type=float)
    if quantity is None or quantity < 0:
        flash('Enter a valid non-negative quantity.', 'danger')
        return redirect(url_for('staff.inventory'))

    if action == 'add':
        item.quantity += quantity
        flash(f'Added {quantity} {item.unit} to {item.name}', 'success')
    elif action == 'remove':
        if quantity > item.quantity:
            flash(f'Cannot remove {quantity} {item.unit}. Only {item.quantity} {item.unit} available.', 'danger')
            return redirect(url_for('staff.inventory'))
        item.quantity -= quantity
        flash(f'Removed {quantity} {item.unit} from {item.name}', 'success')
    elif action == 'set':
        item.quantity = quantity
        flash(f'Set {item.name} quantity to {quantity} {item.unit}', 'success')
    else:
        flash('Choose a valid stock action.', 'danger')
        return redirect(url_for('staff.inventory'))

    item.last_updated = datetime.utcnow()
    item.updated_by = current_user.id
    
    db.session.commit()

    return redirect(url_for('staff.inventory'))

@staff_bp.route('/inventory/add', methods=['POST'])
@login_required
@role_required('staff')
def add_inventory_item():
    """Create an inventory item."""
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    unit = request.form.get('unit', '').strip()
    quantity = request.form.get('quantity', type=float)
    min_threshold = request.form.get('min_threshold', type=float)
    unit_price = request.form.get('unit_price', default=0, type=float)

    if not name or not category or not unit or quantity is None or min_threshold is None or unit_price is None:
        flash('Complete all required fields with valid numbers.', 'danger')
        return redirect(url_for('staff.inventory'))
    if min(quantity, min_threshold, unit_price) < 0:
        flash('Quantity, threshold, and unit price cannot be negative.', 'danger')
        return redirect(url_for('staff.inventory'))

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
    flash('Inventory item added successfully.', 'success')
    return redirect(url_for('staff.inventory'))

@staff_bp.route('/inventory/edit/<int:item_id>', methods=['POST'])
@login_required
@role_required('staff')
def edit_inventory_item(item_id):
    """Edit inventory item details."""
    item = InventoryItem.query.get_or_404(item_id)
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    unit = request.form.get('unit', '').strip()
    quantity = request.form.get('quantity', type=float)
    min_threshold = request.form.get('min_threshold', type=float)
    unit_price = request.form.get('unit_price', default=0, type=float)

    if not name or not category or not unit or quantity is None or min_threshold is None or unit_price is None:
        flash('Complete all required fields with valid numbers.', 'danger')
        return redirect(url_for('staff.inventory'))
    if min(quantity, min_threshold, unit_price) < 0:
        flash('Quantity, threshold, and unit price cannot be negative.', 'danger')
        return redirect(url_for('staff.inventory'))

    item.name = name
    item.category = category
    item.unit = unit
    item.quantity = quantity
    item.min_threshold = min_threshold
    item.unit_price = unit_price
    item.last_updated = datetime.utcnow()
    item.updated_by = current_user.id
    db.session.commit()
    flash('Inventory item updated successfully.', 'success')
    return redirect(url_for('staff.inventory'))

@staff_bp.route('/inventory/delete/<int:item_id>', methods=['POST'])
@login_required
@role_required('staff')
def delete_inventory_item(item_id):
    """Delete an inventory item."""
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Inventory item deleted successfully.', 'success')
    return redirect(url_for('staff.inventory'))

@staff_bp.route('/announcements')
@login_required
@role_required('staff')
def announcements():
    """View announcements"""
    announcements = Announcement.query.filter(
        Announcement.is_active == True,
        Announcement.target_role.in_(['all', 'staff'])
    ).filter(
        db.or_(
            Announcement.expires_at == None,
            Announcement.expires_at > datetime.utcnow()
        )
    ).order_by(Announcement.created_at.desc()).all()
    
    return render_template('staff/announcements.html', announcements=announcements)

@staff_bp.route('/verified-meals')
@login_required
@role_required('staff')
def verified_meals():
    """View meals verified today"""
    today = date.today()
    
    verified = MealBooking.query.filter(
        MealBooking.booking_date == today,
        MealBooking.status == 'consumed'
    ).order_by(MealBooking.verified_at.desc()).all()
    
    return render_template('staff/verified_meals.html', verified_meals=verified)
