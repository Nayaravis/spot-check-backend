import json
import os

from dotenv import load_dotenv
from flask_restful import Resource
from flask import request, make_response
import requests

from models import db, User, Place, Review, UserFavorite

load_dotenv(".env")

user_excludes = ("-reviews", "-favorites")

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

        new_user = User(
            email=request_body["email"],
            username=request_body["username"],
            first_name=request_body["first_name"],
            last_name=request_body["last_name"],
            profile_picture_url=request_body["profile_picture_url"],
            password_hash="vfnusdifn8934upldcae"    
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
                if val is not None or val.strip() != '':
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
                "latitude": -1.3005153,   ####
                "longitude": 36.7844783}, ####    to be replaced with browser location data
              "radius": 500.0
            }
          }
        }

        response = requests.post("https://places.googleapis.com/v1/places:searchNearby", json=request_obj, headers={
            "Content-Type": "applicaiton/json",
            "X-Goog-FieldMask": "places.displayName",
            "X-Goog-Api-Key": SECRET_KEY,
            "X-Goog-FieldMask": "places.displayName,places.postalAddress,places.id,places.iconBackgroundColor,places.googleMapsUri,places.nationalPhoneNumber,places.priceLevel,places.types,places.websiteUri,places.photos"
        })

        return make_response(
            json.loads(response.content),
            200
        )

    def post(self):
        request_body = request.get_json()
        reviewed_place = Place(
            google_place_id=request["google_place_id"],
            name=request_body["name"],
            address=request_body["address"],
            phone=request_body["phone"],
            website=request_body["website"],
            category=request_body["category"],
            latitude=request_body["latitude"],
            longitude=request_body["longitude"],
            rating=request_body["rating"],
            price_level=request_body["price_level"],
            photo_reference=request_body["photo_reference"]
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
            new_review = Review(
                user_id=request_body["user_id"],
                place_id=place_id,
                rating=request_body["rating"],
                title=request_body["title"],
                content=request_body["content"],
                visit_date=request_body["visit_date"],
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