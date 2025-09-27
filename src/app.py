from flask import Flask, make_response
from flask_migrate import Migrate
from flask_restful import Api
from werkzeug.exceptions import NotFound
from flask_cors import CORS

from endpoints import (
    Users, UserByID, Login,
    Places, PlaceByID,
    Reviews, ReviewByID,
    Favorites, FavoriteByID
)
from models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///spotcheck.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = True
db.init_app(app)

CORS(app)

api = Api(app)
migrate = Migrate(app, db)

@app.errorhandler(NotFound)
def handle_not_found(e):
    return make_response(
        "Not Found: The requested resource does not exist.",
        404,
        {"Content-Type": "application/json"}
    )

api.add_resource(Users, "/users")
api.add_resource(UserByID, "/users/<int:id>")
api.add_resource(Login, "/login")
api.add_resource(Places, "/places")
api.add_resource(PlaceByID, "/places/<int:id>")
api.add_resource(Favorites, "/favorites")  # Updated to not require user_id in URL
api.add_resource(FavoriteByID, "/favorites/<int:id>")
api.add_resource(Reviews, "/places/<int:place_id>/add_review") # add a review through a place
api.add_resource(ReviewByID, "/reviews/<int:id>")

