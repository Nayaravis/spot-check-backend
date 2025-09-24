from flask_restful import Resource


class Users(Resource):
    def post(self):
        pass


class UserByID(Resource):
    def get(self, id):
        pass

    def patch(self, id):
        pass

    def delete(self, id):
        pass


class Places(Resource):
    def get(self):
        pass

    def post(self):
        pass


class PlaceByID(Resource):
    def get(self):
        pass


class Reviews(Resource):
    def post(self, place_id): # uses the place's ID to append a new 'Review'
        pass


class ReviewByID(Resource):
    def patch(self, id):
        pass

    def delete(self, id):
        pass