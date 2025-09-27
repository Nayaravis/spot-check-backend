import re
import bcrypt

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin

db = SQLAlchemy()

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    profile_picture_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    reviews = db.relationship('Review',  cascade='all, delete-orphan')
    favorites = db.relationship('UserFavorite', back_populates="user", cascade='all, delete-orphan')

    serialize_rules = ("-favorites.user", "-reviews.user", "-reviews.place")
    
    @validates('email')
    def validate_email(self, key, email):
        if not email or not email.strip():
            raise ValueError('Email is required')
        if len(email) > 255:
            raise ValueError('Email must be 255 characters or less')
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValueError('Invalid email format')
        return email.strip()
    
    @validates('username')
    def validate_username(self, key, username):
        if not username or not username.strip():
            raise ValueError('Username is required')
        if len(username) > 100:
            raise ValueError('Username must be 100 characters or less')
        return username.strip()
    
    @validates('password_hash')
    def validate_password_hash(self, key, password_hash):
        if not password_hash:
            raise ValueError('Password hash is required')
        return password_hash
    
    @validates('first_name', 'last_name')
    def validate_names(self, key, name):
        if name and len(name) > 100:
            raise ValueError(f'{key} must be 100 characters or less')
        return name.strip() if name else name
    
    @validates('profile_picture_url')
    def validate_profile_picture_url(self, key, url):
        if url and not re.match(r'^https?://', url):
            raise ValueError('Profile picture URL must be a valid URL')
        return url
    
    def set_password(self, password):
        """Hash and set the user's password"""
        if not password:
            raise ValueError('Password is required')
        if len(password) < 6:
            raise ValueError('Password must be at least 6 characters long')
        
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        if not password or not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class Place(db.Model, SerializerMixin):
    __tablename__ = 'places'
    
    id = db.Column(db.Integer, primary_key=True)
    google_place_id = db.Column(db.String(255), unique=True, nullable=False)
    display_name = db.Column(db.String(255), nullable=False)  # from displayName.text
    google_maps_uri = db.Column(db.String(1000))  # from googleMapsUri
    icon_background_color = db.Column(db.String(20))  # from iconBackgroundColor
    national_phone_number = db.Column(db.String(50))  # from nationalPhoneNumber
    website_uri = db.Column(db.String(500))  # from websiteUri
    postal_code = db.Column(db.String(20))  # from postalAddress.postalCode
    region_code = db.Column(db.String(10))  # from postalAddress.regionCode
    address_lines = db.Column(db.Text)  # from postalAddress.addressLines (JSON string)
    types = db.Column(db.Text)  # from types array (JSON string)
    photos = db.Column(db.Text)  # from photos array (JSON string)
    # Keep existing fields that are still useful
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    rating = db.Column(db.Integer)
    price_level = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    reviews = db.relationship('Review', backref='place', cascade='all, delete-orphan')

    serialize_rules = ("-reviews.place",)
    
    @validates('google_place_id')
    def validate_google_place_id(self, key, place_id):
        if not place_id or not place_id.strip():
            raise ValueError('Google place ID is required')
        return place_id.strip()
    
    @validates('name')
    def validate_name(self, key, name):
        if not name or not name.strip():
            raise ValueError('Name is required')
        return name.strip()
    
    @validates('phone')
    def validate_phone(self, key, phone):
        if phone and not re.match(r'^[\d\s\-\+\(\)]+$', phone):
            raise ValueError('Invalid phone number format')
        return phone
    
    @validates('website')
    def validate_website(self, key, website):
        if website and not re.match(r'^https?://', website):
            raise ValueError('Website must be a valid URL')
        return website
    
    @validates('latitude')
    def validate_latitude(self, key, latitude):
        if latitude is not None and (latitude < -90 or latitude > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return latitude
    
    @validates('longitude')
    def validate_longitude(self, key, longitude):
        if longitude is not None and (longitude < -180 or longitude > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return longitude
    
    @validates('rating')
    def validate_rating(self, key, rating):
        if rating is not None and (rating < 0 or rating > 5):
            raise ValueError('Rating must be between 0 and 5')
        return rating
    
    @validates('price_level')
    def validate_price_level(self, key, price_level):
        if price_level is not None and (int(price_level) < 1 or int(price_level) > 4):
            raise ValueError('Price level must be between 1 and 4')
        return price_level
    
    @validates('photo_reference')
    def validate_photo_reference(self, key, photo_ref):
        if photo_ref and not photo_ref.strip():
            raise ValueError('Photo reference cannot be empty string')
        return photo_ref.strip() if photo_ref else photo_ref

class Review(db.Model, SerializerMixin):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    visit_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    @validates('rating')
    def validate_rating(self, key, rating):
        if rating is None or rating < 1 or rating > 5:
            raise ValueError('Rating must be between 1 and 5')
        return rating
    
    @validates('title')
    def validate_title(self, key, title):
        if not title or not title.strip():
            raise ValueError('Title is required')
        return title.strip()
    
    @validates('visit_date')
    def validate_visit_date(self, key, visit_date):
        if not visit_date:
            raise ValueError('Visit date is required')
        return visit_date


class UserFavorite(db.Model, SerializerMixin):
    __tablename__ = 'user_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    place = db.relationship('Place', backref='user_favorites')
    user = db.relationship('User', back_populates="favorites")

    serialize_rules = ("-place.user_favorites", "-user.favorites")
    
    __table_args__ = (db.UniqueConstraint('user_id', 'place_id'),)
