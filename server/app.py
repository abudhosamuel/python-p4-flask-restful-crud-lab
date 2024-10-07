from flask import Flask, jsonify, request, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Plant

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = True

# Initialize migration and db
migrate = Migrate(app, db)
db.init_app(app)

# Initialize Flask-RESTful API
api = Api(app)

# Custom error handler for 404
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

# Plants resource to handle GET (list all plants) and POST (add new plant)
class Plants(Resource):
    def get(self):
        plants = Plant.query.all()
        plant_list = [plant.to_dict() for plant in plants]
        return make_response(jsonify(plant_list), 200)

    def post(self):
        data = request.get_json()

        # Validate that all required fields are present
        if not all(key in data for key in ['name', 'image', 'price']):
            return make_response(jsonify({"error": "Missing required fields"}), 400)

        try:
            # Create a new Plant instance
            new_plant = Plant(
                name=data['name'],
                image=data['image'],
                price=data['price'],
                is_in_stock=data.get('is_in_stock', True)  # Default to True if not provided
            )
            db.session.add(new_plant)
            db.session.commit()

            return make_response(jsonify(new_plant.to_dict()), 201)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

# PlantByID resource to handle GET, PATCH, and DELETE for individual plants by id
class PlantByID(Resource):
    def get(self, id):
        # Use db.session.get() to replace the deprecated Query.get() method
        plant = db.session.get(Plant, id)
        if not plant:
            return make_response(jsonify({"error": "Plant not found"}), 404)
        return make_response(jsonify(plant.to_dict()), 200)

    def patch(self, id):
        plant = db.session.get(Plant, id)
        if not plant:
            return make_response(jsonify({"error": "Plant not found"}), 404)
        
        data = request.get_json()

        # Only update the fields that are provided
        try:
            if 'is_in_stock' in data:
                plant.is_in_stock = data['is_in_stock']
            if 'name' in data:
                plant.name = data['name']
            if 'image' in data:
                plant.image = data['image']
            if 'price' in data:
                plant.price = data['price']

            db.session.commit()
            return make_response(jsonify(plant.to_dict()), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

    def delete(self, id):
        plant = db.session.get(Plant, id)
        if not plant:
            return make_response(jsonify({"error": "Plant not found"}), 404)
        
        try:
            db.session.delete(plant)
            db.session.commit()
            return make_response('', 204)  # No content response
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

# Add resources to API with specified endpoints
api.add_resource(Plants, '/plants')  # Index and Create routes
api.add_resource(PlantByID, '/plants/<int:id>')  # Show, Update (PATCH), and Delete routes

if __name__ == '__main__':
    app.run(port=5555, debug=True)
