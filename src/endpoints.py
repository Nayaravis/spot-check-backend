import json
import os
from datetime import datetime, date, timedelta
import jwt

from dotenv import load_dotenv
from flask_restful import Resource
from flask import request, make_response, current_app
import requests

from models import db, User, Place, Review, UserFavorite

load_dotenv("../.env")

user_excludes = ("-reviews", "-favorites")

def parse_iso_date(date_string):
    """
    Convert ISO date string to Python date/datetime object.
    Handles both date (YYYY-MM-DD) and datetime (YYYY-MM-DDTHH:MM:SS) formats.
    """
    if not date_string:
        return None
    
    try:
        # Try parsing as datetime first (ISO format with time)
        if 'T' in date_string:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        else:
            # Parse as date only
            return datetime.fromisoformat(date_string).date()
    except ValueError:
        # If ISO parsing fails, try other common formats
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ValueError(f"Unable to parse date: {date_string}")

def generate_jwt_token(user_id):
    """Generate a JWT token for the given user ID"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7),  # Token expires in 7 days
        'iat': datetime.utcnow()  # Issued at
    }
    
    # Get secret key from environment or use a default
    secret_key = os.getenv('JWT_SECRET_KEY', 'id0nth@ve1navisayara@gmail.com')
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

def verify_jwt_token(token):
    """Verify and decode a JWT token"""
    try:
        secret_key = os.getenv('JWT_SECRET_KEY', 'id0nth@ve1navisayara@gmail.com')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user():
    """Get the current user from the JWT token in the request headers"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        # Extract token from "Bearer <token>" format
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        return User.query.get(user_id)
    except (IndexError, AttributeError):
        return None

def require_auth(f):
    """Decorator to require authentication for endpoints"""
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return make_response(
                {"error": "Authentication required. Please provide a valid JWT token."},
                401
            )
        # Add current user to kwargs so the endpoint can access it
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated_function

def user_not_found():
    return make_response(
        {"error": "user not found"},
        404
    )

def place_not_found():
    return make_response(
        {"error": "place not found"},
        404
    )

def favorite_not_found():
    return make_response(
        {"error": "favorite not found"},
        404
    )

def review_not_found():
    return make_response(
        {"error": "review not found"},
        404
    )

class Users(Resource):
    def post(self):
        request_body = request.get_json()

        # Validate required fields
        required_fields = ["email", "username", "password", "first_name", "last_name"]
        for field in required_fields:
            if field not in request_body or not request_body[field]:
                return make_response(
                    {"error": f"{field} is required"},
                    400
                )

        # Handle optional datetime fields
        created_at = parse_iso_date(request_body.get("created_at"))
        updated_at = parse_iso_date(request_body.get("updated_at"))

        new_user = User(
            email=request_body["email"],
            username=request_body["username"],
            first_name=request_body["first_name"],
            last_name=request_body["last_name"],
            profile_picture_url=request_body.get("profile_picture_url"),
            created_at=created_at,
            updated_at=updated_at
        )

        # Hash the password using the User model method
        try:
            new_user.set_password(request_body["password"])
        except ValueError as e:
            return make_response(
                {"error": str(e)},
                400
            )

        db.session.add(new_user)
        db.session.commit()

        # Generate JWT token for the new user
        token = generate_jwt_token(new_user.id)

        return make_response(
            {
                "user": new_user.to_dict(rules=user_excludes),
                "token": token,
                "message": "User created successfully"
            },
            201
        )


class UserByID(Resource):
    def get(self, id):
        user = User.query.where(User.id == id).first()

        if user:
            response_body = user.to_dict()

            return make_response(
                response_body,
                200
            )
        
        return user_not_found()

    def patch(self, id):
        user = User.query.where(User.id == id).first()
        request_body = request.get_json()

        if user:
            for prop, val in request_body.items():
                if val is not None:
                    # Handle datetime fields
                    if prop in ['created_at', 'updated_at']:
                        parsed_date = parse_iso_date(val)
                        if parsed_date:
                            setattr(user, prop, parsed_date)
                    else:
                        # Handle string fields
                        if isinstance(val, str) and val.strip() != '':
                            setattr(user, prop, val)
                        elif not isinstance(val, str):
                            setattr(user, prop, val)
        
            return make_response(
                user.to_dict(rules=user_excludes),
                200
            )
        return user_not_found()

    def delete(self, id):
        user = User.query.where(User.id == id).first()
        
        if user:
            db.session.delete(user)
            db.session.commit()

            return make_response(
                {"msg": "user deleted successfully"},
                200
            )
        
        return user_not_found()


class Login(Resource):
    def post(self):
        request_body = request.get_json()
        
        # Validate required fields
        if not request_body.get("email") or not request_body.get("password"):
            return make_response(
                {"error": "Email and password are required"},
                400
            )
        
        # Find user by email
        user = User.query.filter_by(email=request_body["email"]).first()
        
        if not user:
            return make_response(
                {"error": "Invalid email or password"},
                401
            )
        
        # Check password
        if not user.check_password(request_body["password"]):
            return make_response(
                {"error": "Invalid email or password"},
                401
            )
        
        # Generate JWT token
        token = generate_jwt_token(user.id)
        
        return make_response(
            {
                "user": user.to_dict(rules=user_excludes),
                "token": token,
                "message": "Login successful"
            },
            200
        )


class Places(Resource):
    # implement fetching place data from the Google Places API
    def get(self):
        SECRET_KEY=os.getenv("GOOGLE_CLOUD_API_KEY")
        request_obj = {
          "includedTypes": ["restaurant"],
          "maxResultCount": 10,
          "locationRestriction": {
            "circle": {
              "center": {
                "latitude": float(request.args.get("latitude")),   
                "longitude": float(request.args.get("longitude"))}, 
              "radius": 10000.0
            }
          }
        }

        response = requests.post("https://places.googleapis.com/v1/places:searchNearby", json=request_obj, headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": SECRET_KEY,
            "X-Goog-FieldMask": "places.displayName,places.postalAddress,places.id,places.iconBackgroundColor,places.googleMapsUri,places.nationalPhoneNumber,places.priceLevel,places.types,places.websiteUri,places.photos"
        })

        return make_response(
            json.loads(response.content),
            200
        )

    def post(self, current_user=None):
        request_body = request.get_json()
        
        # Extract data from Google Places API response structure
        place_data = request_body.get('place', request_body)  # Handle both direct place data and nested structure
        
        # Check if place already exists
        google_place_id = place_data.get('id')
        existing_place = Place.query.filter_by(google_place_id=google_place_id).first()
        
        if existing_place:
            # Place already exists, return it
            return make_response(
                existing_place.to_dict(),
                200
            )
        
        display_name_obj = place_data.get('displayName', {})
        display_name = display_name_obj.get('text', '') if isinstance(display_name_obj, dict) else str(display_name_obj)
        
        postal_address = place_data.get('postalAddress', {})
        address_lines = json.dumps(postal_address.get('addressLines', [])) if postal_address.get('addressLines') else None
        postal_code = postal_address.get('postalCode')
        region_code = postal_address.get('regionCode')
        
        types = json.dumps(place_data.get('types', [])) if place_data.get('types') else None
        photos = json.dumps(place_data.get('photos', [])) if place_data.get('photos') else None
        
        # Handle optional datetime fields
        created_at = parse_iso_date(request_body.get('created_at'))
        updated_at = parse_iso_date(request_body.get('updated_at'))
        
        reviewed_place = Place(
            google_place_id=google_place_id,
            display_name=display_name,
            google_maps_uri=place_data.get('googleMapsUri'),
            icon_background_color=place_data.get('iconBackgroundColor'),
            national_phone_number=place_data.get('nationalPhoneNumber'),
            website_uri=place_data.get('websiteUri'),
            postal_code=postal_code,
            region_code=region_code,
            address_lines=address_lines,
            types=types,
            photos=photos,
            latitude=request_body.get('latitude'),  # These might come from separate location data
            longitude=request_body.get('longitude'),
            rating=request_body.get('rating'),
            price_level=place_data.get('priceLevel'),
            created_at=created_at,
            updated_at=updated_at
        )

        db.session.add(reviewed_place)
        db.session.commit()

        return make_response(
            reviewed_place.to_dict(),
            201
        )


class PlaceByID(Resource):
    def get(self, id):
        place = Place.query.where(Place.id == id).first()

        if place:
            return make_response(
                place.to_dict(),
                200
            )
        
        return place_not_found()

class Favorites(Resource):
    @require_auth
    def get(self, current_user=None):
        user_favorites = UserFavorite.query.filter_by(user_id=current_user.id).all()

        favorites = [favorite.place.to_dict() for favorite in user_favorites]

        return make_response(
            favorites,
            200
        )

    @require_auth
    def post(self, current_user=None):
        data = request.get_json()
        place_id = data.get("place_id")

        # Validate input
        if not place_id:
            return make_response({"error": "place_id is required"}, 400)

        # Ensure place exists
        place = Place.query.where(Place.id == place_id).first()
        if not place:
            return place_not_found()

        # Prevent duplicates (also enforced by unique constraint)
        existing = UserFavorite.query.filter_by(user_id=current_user.id, place_id=place_id).first()
        if existing:
            return make_response(
                {
                    "message": "Place already in favorites",
                    "favorite": existing.to_dict(),
                    "place": place.to_dict(),
                },
                200,
            )

        # Create favorite
        favorite = UserFavorite(user_id=current_user.id, place_id=place_id)
        db.session.add(favorite)
        db.session.commit()

        return make_response(
            {
                "favorite": favorite.to_dict(),
                "place": place.to_dict(),
                "message": "Added to favorites",
            },
            201,
        )


class FavoriteByID(Resource):
    @require_auth
    def delete(self, id, current_user=None):
        user_favorite = UserFavorite.query.where(UserFavorite.id == id).first()

        if user_favorite:
            # Check if the favorite belongs to the current user
            if user_favorite.user_id != current_user.id:
                return make_response(
                    {"error": "You can only delete your own favorites"},
                    403
                )
            
            db.session.delete(user_favorite)
            db.session.commit()

            return make_response(
                {"msg": "favorite deleted"},
                200
            )
        
        return favorite_not_found()

class Reviews(Resource):
    @require_auth
    def post(self, place_id, current_user=None): # uses the place's ID to append a new 'Review'
        place = Place.query.where(Place.id == place_id).first()
        request_body = request.get_json()

        if place:
            # Handle visit_date conversion from ISO format
            visit_date = parse_iso_date(request_body["visit_date"])
            if not visit_date:
                return make_response(
                    {"error": "Invalid visit_date format. Use ISO format (YYYY-MM-DD)"},
                    400
                )
            
            new_review = Review(
                user_id=current_user.id,  # Use authenticated user
                place_id=place_id,
                rating=request_body["rating"],
                title=request_body["title"],
                content=request_body["content"],
                visit_date=visit_date,
            )

            place.reviews.append(new_review)
            db.session.commit()
        
            return make_response(
                new_review.to_dict(),
                201
            )


class ReviewByID(Resource):
    @require_auth
    def patch(self, id, current_user=None):
        review = Review.query.where(Review.id == id).first()
        request_body = request.get_json()

        if review:
            # Check if the review belongs to the current user
            if review.user_id != current_user.id:
                return make_response(
                    {"error": "You can only edit your own reviews"},
                    403
                )
            
            for prop, val in request_body.items():
                if val is not None:
                    # Handle datetime fields
                    if prop in ['visit_date', 'created_at', 'updated_at']:
                        parsed_date = parse_iso_date(val)
                        if parsed_date:
                            setattr(review, prop, parsed_date)
                    else:
                        # Handle string fields
                        if isinstance(val, str) and val.strip() != '':
                            setattr(review, prop, val)
                        elif not isinstance(val, str):
                            setattr(review, prop, val)

            return make_response(
                review.to_dict(),
                200
            )
        
        return review_not_found()

    @require_auth
    def delete(self, id, current_user=None):
        review = Review.query.where(Review.id == id).first()

        if review:
            # Check if the review belongs to the current user
            if review.user_id != current_user.id:
                return make_response(
                    {"error": "You can only delete your own reviews"},
                    403
                )
            
            db.session.delete(review)
            db.session.commit()

            return make_response(
                {"msg": "review deleted successfully"},
                200
            )
        
        return review_not_found()