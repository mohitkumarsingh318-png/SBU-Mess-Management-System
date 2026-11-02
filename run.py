from app import create_app, db
from app.models import User, MealPlan, Menu, MealBooking, Payment, Feedback, InventoryItem, Announcement
from datetime import datetime, date, timedelta
import secrets

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'MealPlan': MealPlan,
        'Menu': Menu,
        'MealBooking': MealBooking,
        'Payment': Payment,
        'Feedback': Feedback,
        'InventoryItem': InventoryItem,
        'Announcement': Announcement
    }

@app.cli.command()
def init_db():
    """Initialize the database with sample data."""
    print("Initializing database...")
    
    # Create tables
    db.create_all()
    
    # Check if data already exists
    if User.query.first():
        print("Database already initialized!")
        return
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        full_name='System Administrator',
        role='admin',
        phone='9876543210'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create staff user
    staff = User(
        username='staff',
        email='staff@example.com',
        full_name='Mess Staff',
        role='staff',
        phone='9876543211'
    )
    staff.set_password('staff123')
    db.session.add(staff)
    
    # Create sample students
    students = []
    for i in range(1, 11):
        student = User(
            username=f'student{i}',
            email=f'student{i}@example.com',
            full_name=f'Student {i}',
            roll_number=f'STUDENT2024{i:03d}',
            role='student',
            phone=f'98765432{i:02d}'
        )
        student.set_password('student123')
        students.append(student)
        db.session.add(student)
    
    db.session.commit()
    print("Users created!")
    
    # Create meal plan
    plan = MealPlan(
        name='Standard Meal Plan',
        description='Includes breakfast, lunch, and dinner',
        breakfast_price=30.0,
        lunch_price=50.0,
        dinner_price=45.0,
        monthly_price=3000.0,
        is_active=True
    )
    db.session.add(plan)
    db.session.commit()
    print("Meal plan created!")
    
    # Create menus for the next 7 days
    today = date.today()
    meal_items = {
        'breakfast': [
            'Poha, Tea, Banana',
            'Upma, Coffee, Orange',
            'Paratha, Curd, Tea',
            'Idli, Sambar, Chutney, Coffee',
            'Bread, Butter, Jam, Tea',
            'Dosa, Sambar, Chutney, Coffee',
            'Aloo Paratha, Curd, Tea'
        ],
        'lunch': [
            'Rice, Dal, Roti, Sabji, Salad',
            'Rice, Rajma, Roti, Aloo Gobi, Salad',
            'Rice, Sambar, Roti, Paneer, Salad',
            'Pulao, Dal, Roti, Mix Veg, Raita',
            'Rice, Chole, Roti, Bhindi, Salad',
            'Biryani, Raita, Salad',
            'Rice, Dal Makhani, Roti, Paneer Butter Masala, Salad'
        ],
        'dinner': [
            'Rice, Dal, Roti, Sabji',
            'Rice, Kadhi, Roti, Aloo Matar',
            'Rice, Dal, Roti, Palak Paneer',
            'Rice, Rajma, Roti, Cabbage',
            'Rice, Dal, Roti, Egg Curry',
            'Rice, Dal, Roti, Mixed Veg',
            'Rice, Dal, Roti, Chicken Curry'
        ]
    }
    
    for i in range(7):
        menu_date = today + timedelta(days=i)
        day_index = i % 7
        
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            menu = Menu(
                date=menu_date,
                meal_type=meal_type,
                items=meal_items[meal_type][day_index],
                is_special=(i == 6 and meal_type == 'lunch')  # Sunday lunch is special
            )
            db.session.add(menu)
    
    db.session.commit()
    print("Menus created!")
    
    # Create sample bookings for students
    for student in students[:5]:  # First 5 students
        for i in range(3):
            booking_date = today + timedelta(days=i)
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                menu = Menu.query.filter_by(date=booking_date, meal_type=meal_type).first()
                prices = {'breakfast': 30.0, 'lunch': 50.0, 'dinner': 45.0}
                
                booking = MealBooking(
                    user_id=student.id,
                    menu_id=menu.id if menu else None,
                    booking_date=booking_date,
                    meal_type=meal_type,
                    status='booked',
                    price=prices[meal_type]
                )
                booking.generate_token()
                db.session.add(booking)
    
    db.session.commit()
    print("Sample bookings created!")
    
    # Create sample inventory items
    inventory_items = [
        {'name': 'Rice', 'category': 'Grains', 'quantity': 500, 'unit': 'kg', 'min_threshold': 100, 'unit_price': 40},
        {'name': 'Wheat Flour', 'category': 'Grains', 'quantity': 300, 'unit': 'kg', 'min_threshold': 50, 'unit_price': 35},
        {'name': 'Dal (Mixed)', 'category': 'Pulses', 'quantity': 200, 'unit': 'kg', 'min_threshold': 50, 'unit_price': 80},
        {'name': 'Cooking Oil', 'category': 'Oil', 'quantity': 100, 'unit': 'liters', 'min_threshold': 20, 'unit_price': 120},
        {'name': 'Potatoes', 'category': 'Vegetables', 'quantity': 150, 'unit': 'kg', 'min_threshold': 30, 'unit_price': 20},
        {'name': 'Onions', 'category': 'Vegetables', 'quantity': 100, 'unit': 'kg', 'min_threshold': 25, 'unit_price': 30},
        {'name': 'Tomatoes', 'category': 'Vegetables', 'quantity': 80, 'unit': 'kg', 'min_threshold': 20, 'unit_price': 25},
        {'name': 'Milk', 'category': 'Dairy', 'quantity': 50, 'unit': 'liters', 'min_threshold': 20, 'unit_price': 50},
        {'name': 'Paneer', 'category': 'Dairy', 'quantity': 15, 'unit': 'kg', 'min_threshold': 10, 'unit_price': 300},
        {'name': 'Spices (Mixed)', 'category': 'Spices', 'quantity': 5, 'unit': 'kg', 'min_threshold': 5, 'unit_price': 200},
        {'name': 'Salt', 'category': 'Spices', 'quantity': 25, 'unit': 'kg', 'min_threshold': 10, 'unit_price': 10},
        {'name': 'Sugar', 'category': 'Sweeteners', 'quantity': 50, 'unit': 'kg', 'min_threshold': 15, 'unit_price': 45},
    ]
    
    for item_data in inventory_items:
        item = InventoryItem(**item_data, updated_by=admin.id)
        db.session.add(item)
    
    db.session.commit()
    print("Inventory items created!")
    
    # Create sample announcement
    announcement = Announcement(
        title='Welcome to Mess Management System',
        content='This is the new digital mess management system. You can now book meals, view menus, and track payments online. For any issues, please contact the mess administrator.',
        priority='high',
        target_role='all',
        expires_at=datetime.utcnow() + timedelta(days=30),
        is_active=True,
        created_by=admin.id
    )
    db.session.add(announcement)
    
    db.session.commit()
    print("Announcement created!")
    
    print("\n✅ Database initialized successfully!")
    print("\nDemo Credentials:")
    print("Admin: username='admin', password='admin123'")
    print("Staff: username='staff', password='staff123'")
    print("Student: username='student1', password='student123'")

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
