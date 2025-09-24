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

    