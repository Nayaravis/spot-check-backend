from datetime import date

from app import app
from models import db, User, Place, Review

with app.app_context():
    # Clear existing data
    User.query.delete()
    Place.query.delete()
    Review.query.delete()
    Review.query.delete()
    
    # Create users
    from werkzeug.security import generate_password_hash
    
    user1 = User(
        email='john@example.com', 
        username='john_doe', 
        first_name='John', 
        last_name='Doe',
        password_hash=generate_password_hash('password123')
    )
    
    user2 = User(
        email='jane@example.com', 
        username='jane_smith', 
        first_name='Jane', 
        last_name='Smith',
        password_hash=generate_password_hash('password123')
    )
    
    db.session.add_all([user1, user2])
    db.session.commit()
    
    # Create places
    place1 = Place(
        google_place_id='place_001',
        display_name='Central Park Cafe',
        address_lines='["123 Park Ave", "New York, NY"]',
        types='["restaurant", "cafe", "food"]',
        latitude=40.7829,
        longitude=-73.9654,
        rating=4.2,
        price_level=2
    )
    
    place2 = Place(
        google_place_id='place_002',
        display_name='Brooklyn Bridge View',
        address_lines='["Brooklyn Bridge", "New York, NY"]',
        types='["tourist_attraction", "landmark", "point_of_interest"]',
        latitude=40.7061,
        longitude=-73.9969,
        rating=4.8,
        price_level=0
    )
    
    place3 = Place(
        google_place_id='place_003',
        display_name='Times Square Deli',
        address_lines='["Times Square", "New York, NY"]',
        types='["restaurant", "food", "deli"]',
        latitude=40.7580,
        longitude=-73.9855,
        rating=3.9,
        price_level=1
    )
    
    db.session.add_all([place1, place2, place3])
    db.session.commit()
    
    # Create reviews
    review1 = Review(
        user_id=user1.id,
        place_id=place1.id,
        rating=5,
        title='Amazing coffee!',
        content='Great atmosphere and excellent coffee. Will definitely come back.',
        visit_date=date(2024, 1, 15)
    )
    
    review2 = Review(
        user_id=user2.id,
        place_id=place1.id,
        rating=4,
        title='Good food',
        content='Nice place for brunch. Service was friendly.',
        visit_date=date(2024, 1, 20)
    )
    
    review3 = Review(
        user_id=user1.id,
        place_id=place2.id,
        rating=5,
        title='Breathtaking views',
        content='Perfect spot for photos. The sunset view is incredible.',
        visit_date=date(2024, 1, 10)
    )
    
    review4 = Review(
        user_id=user2.id,
        place_id=place3.id,
        rating=3,
        title='Average deli',
        content='Food was okay, nothing special. Convenient location though.',
        visit_date=date(2024, 1, 25)
    )
    
    db.session.add_all([review1, review2, review3, review4])
    db.session.commit()
    
    print("Database seeded successfully!")
    print(f"Created {User.query.count()} users")
    print(f"Created {Place.query.count()} places")
    print(f"Created {Review.query.count()} reviews")