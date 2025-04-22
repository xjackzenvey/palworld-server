from backend import app

if __name__ == '__main__':
    with app.app_context():
        from backend import db
        db.create_all()
        print("Database initialized successfully.")