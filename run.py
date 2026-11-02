import click
from app import create_app, db
from app.models import (
    Announcement,
    Feedback,
    InventoryItem,
    MealBooking,
    MealPlan,
    Menu,
    Payment,
    User,
)

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
        'Announcement': Announcement,
    }


@app.cli.command()
def init_db():
    """Create database tables without adding demo accounts."""
    db.create_all()
    click.echo("Database tables are ready.")


@app.cli.command()
def create_admin():
    """Interactively create an administrator account."""
    username = click.prompt("Admin username").strip()
    email = click.prompt("Admin email").strip()
    full_name = click.prompt("Admin full name").strip()

    if not username or not email or not full_name:
        raise click.ClickException("Username, email, and full name are required.")
    if User.query.filter_by(username=username).first():
        raise click.ClickException("That username is already in use.")
    if User.query.filter_by(email=email).first():
        raise click.ClickException("That email is already in use.")

    password = click.prompt(
        "Admin password (minimum 12 characters)",
        hide_input=True,
        confirmation_prompt=True,
    )
    if len(password) < 12:
        raise click.ClickException("Admin password must be at least 12 characters.")

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        role='admin',
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo("Administrator account created.")


@app.cli.command()
def disable_demo_accounts():
    """Deactivate legacy demo accounts without deleting their associated data."""
    demo_accounts = [
        ('admin', 'admin@example.com', 'System Administrator', 'admin'),
        ('staff', 'staff@example.com', 'Mess Staff', 'staff'),
    ]
    demo_accounts.extend(
        (
            f'student{number}',
            f'student{number}@example.com',
            f'Student {number}',
            'student',
        )
        for number in range(1, 11)
    )

    deactivated = 0
    for username, email, full_name, role in demo_accounts:
        user = User.query.filter_by(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
        ).first()
        if user and user.is_active:
            user.is_active = False
            deactivated += 1

    db.session.commit()
    click.echo(f"Deactivated {deactivated} legacy demo account(s).")


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
