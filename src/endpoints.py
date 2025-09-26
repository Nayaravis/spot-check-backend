import json
import os
from datetime import datetime, date

from dotenv import load_dotenv
from flask_restful import Resource
from flask import request, make_response
import requests

from models import db, User, Place, Review, UserFavorite

load_dotenv(".env")

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

        # Handle optional datetime fields
        created_at = parse_iso_date(request_body.get("created_at"))
        updated_at = parse_iso_date(request_body.get("updated_at"))

        new_user = User(
            email=request_body["email"],
            username=request_body["username"],
            first_name=request_body["first_name"],
            last_name=request_body["last_name"],
            profile_picture_url=request_body["profile_picture_url"],
            password_hash="vfnusdifn8934upldcae",
            created_at=created_at,
            updated_at=updated_at
        )

        # password hashing placeholder
        # new_user.password_hash = "vfnusdifn8934upldcae"

        db.session.add(new_user)
        db.session.commit()

        return make_response(
            new_user.to_dict(rules=user_excludes),
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

    def post(self):
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
    def get(self, user_id):
        user_favorites = UserFavorite.query.filter_by(user_id=user_id).all()

        favorites = [favorite.place.to_dict() for favorite in user_favorites]

        return make_response(
            favorites,
            200
        )


class FavoriteByID(Resource):
    def delete(self, id):
        user_favorite = UserFavorite.query.where(UserFavorite.id == id).first()

        if user_favorite:
            db.session.delete(user_favorite)
            db.session.commit()

            return make_response(
                {"msg": "favorite deleted"},
                200
            )
        
        return favorite_not_found()

class Reviews(Resource):
    def post(self, place_id): # uses the place's ID to append a new 'Review'
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
                user_id=request_body["user_id"],
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
    def patch(self, id):
        review = Review.query.where(Review.id == id).first()
        request_body = request.get_json()

        if review:
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

    def delete(self, id):
        review = Review.query.where(Review.id == id).first()
        request_body = request.get_json()

        if review:
            db.session.delete(review)
            db.session.commit()

            return make_response(
                {"msg": "review deleted successfully"},
                200
            )
        
        return review_not_found()