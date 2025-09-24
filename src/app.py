from endpoints import (
    Users, UserByID,
    Places, PlaceByID
)
from flask import Flask
from flask_restful import Api
from models import db

app = Flask(__name__)
app.comfig["SQLALCHEMY_DATABASE_URI"] = "sqlite:///spotcheck.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = True
db.init_app(app)

api = Api(app)


api.add_resource(Users, "/users")
api.add_resource(UserByID, "/users/<int:id>")
api.add_resource(Places, "/places")
api.add_resource(PlaceByID, "/places/<int:id>")
