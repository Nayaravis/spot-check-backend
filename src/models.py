from flask_sqlalchemy import SQLAlchemy
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
    
    reviews = db.relationship('Review', cascade='all, delete-orphan')
    favorites = db.relationship('UserFavorite', cascade='all, delete-orphan')

    serialize_rules = ("-reviews.place", "-favorites.user", "-reviews.user", "-reviews.place")


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

class Review(db.Model, SerializerMixin):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    visit_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class UserFavorite(db.Model, SerializerMixin):
    __tablename__ = 'user_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    __table_args__ = (db.UniqueConstraint('user_id', 'place_id'),)
