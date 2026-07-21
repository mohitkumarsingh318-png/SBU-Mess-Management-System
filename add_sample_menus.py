from app import create_app, db
from app.models import Menu
from datetime import date, timedelta

app = create_app()

with app.app_context():
    # Add sample menus for the missing dates (Nov 24 and 25)
    missing_dates = [date(2025, 11, 24), date(2025, 11, 25)]
    meal_types = ['breakfast', 'lunch', 'dinner']
    
    # Sample menu items for each meal type
    sample_menus = {
        'breakfast': 'Poha, Tea, Banana',
        'lunch': 'Rice, Dal, Roti, Sabji, Salad',
        'dinner': 'Rice, Dal, Roti, Sabji'
    }
    
    added_count = 0
    
    for menu_date in missing_dates:
        for meal_type in meal_types:
            # Check if menu already exists
            existing = Menu.query.filter_by(date=menu_date, meal_type=meal_type).first()
            
            if not existing:
                # Create new menu
                menu = Menu(
                    date=menu_date,
                    meal_type=meal_type,
                    items=sample_menus[meal_type]
                )
                db.session.add(menu)
                added_count += 1
                print(f"Added menu for {menu_date} - {meal_type}")
    
    if added_count > 0:
        db.session.commit()
        print(f"\nSuccessfully added {added_count} sample menus!")
    else:
        print("No new menus needed - all dates already have menu data.")