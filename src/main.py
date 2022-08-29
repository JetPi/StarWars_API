"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import email
import json
import os
import re
from shutil import ExecError
from flask import Flask, request, jsonify, url_for
from itsdangerous import exc
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Favorites, Character, Planet
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
db_url = os.getenv('DATABASE_URL')
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

def filter_character(items):
    result = []
    for item in items:
        current = item.serialize() 
        if current["nature"] == "character":
            result.append(current)
    return result

def filter_planet(items):
    result = []
    for item in items:
        current = item.serialize() 
        if current["nature"] == "planets":
            result.append(current)
    return result

# User methods, CRUD complete
# Works fine, gets users from database
@app.route('/users', methods=['GET'])
@app.route('/users/<int:user_id>', methods=['GET'])
def handle_user(user_id = None):
    if request.method == 'GET':
        if user_id is None:
            users = User()
            users = users.query.all()

            return jsonify(list(map(lambda item: item.serialize(), users))), 200
        else:
            user = User()
            user = user.query.get(user_id)

            if user:
                return jsonify(user.serialize()), 200
                
        return jsonify({"message": "Not found"}), 404

# Works fine, even if the id is in the middle for some. Adds a user to the database
@app.route('/users', methods=['POST'])
def add_new_user():
    if request.method == 'POST':
        body = request.json

        if body.get("username") is None:
            return jsonify({"message": "Error, property bad"}), 400 
        elif body.get("email") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("password") is None:
            return jsonify({"message": "Error, property bad"}), 400

        new_user = User(username=body.get("username"), email=body.get("email"), password=body.get("password"))
        db.session.add(new_user)

        try:
            db.session.commit()
            return jsonify(new_user.serialize()), 201
        except Exception as error:
            print(error.args)
            db.session.rollback()
            return jsonify({"message": f"Error {error.args}"}), 500

# Works fine, allows to update the data of an already existing user
@app.route('/users', methods=['PUT'])
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id = None):
    if request.method == 'PUT':
        body = request.json

        if user_id is None:
            return jsonify({"message": "Error, bad request"}), 400
        elif user_id is not None:
            update_user = User.query.get(user_id)
            if update_user is None:
                return jsonify({"message": "Error, user not found"}), 404
            else:
                update_user.username = body.get("username")
                update_user.email = body.get("email")

                try:
                    db.session.commit()
                    return jsonify(update_user.serialize()), 201
                except Exception as error:
                    print(error.args)
                    return jsonify({"message": f"Error {error.args}"}), 500

# Works fine, allows to delete a user
@app.route('/users', methods=['DELETE'])
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id = None):
    if request.method == 'DELETE':
        if user_id is None:
            return jsonify({"message": "Error, bad request"}), 400
        elif user_id is not None:
            deleted_user = User.query.get(user_id)
            if deleted_user is None:
                return jsonify({"message": "Error, couldn't find user"}), 404
            else:
                db.session.delete(deleted_user)

            try:
                db.session.commit()
                return jsonify([]), 204
            except Exception as error:
                print(error.args)
                db.session.rollback()
                return jsonify({"message": f"Error {error.args}"})

# Favorite Methods
# Works as intended? Need to test with actual data

# Questions
# How do I relate the user to the favorite table from here
# How do I use Enums to validate data from here
# How do I serialize Enums

# Maybe use Enums as filter list, instead of comparators?

# Why is there a serialize error in the second get but not the first
# Why did the POST work with a character that doesn't exist


@app.route("/users/<int:user_id>/favorites", methods=['GET'])
@app.route("/users/<int:user_id>/favorites/<string:nature>/", methods=['GET'])
@app.route("/users/<int:user_id>/favorites/<string:nature>/<int:favorite_id>", methods=['GET'])
def get_favorite(user_id = None, nature = None, favorite_id=None):
    if request.method == 'GET':
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"message": "Error, couldn't find user"}), 404
        elif user is not None:
            if nature is None:
                favorites = Favorites()
                favorites = Favorites.query.all()
                return jsonify(list(map(lambda items: items.serialize(), favorites))), 200
                
            elif nature is not None:    
                if nature != 'character' and nature != 'planet':
                    return jsonify({"message": "Error, bad request"}), 400
                else:
                    if nature == 'character' and favorite_id is None:
                        favorites = Favorites.query.all()
                        favorite_character = filter_character(favorites)
                        return jsonify(favorite_character), 200

                    elif nature == 'character' and favorite_id is not None:
                        favorite = Favorites.query.get(favorite_id)
                        if favorite is None:
                            return jsonify({"message": "Error, couldn't find character"}), 404
                        elif favorite is not None:
                            if favorite.serialize()["nature"] != "character":
                                return jsonify({"message": "Error, favorite isn't a character"}), 406
                            else:
                                return jsonify(favorite.serialize()), 200

                    elif nature == 'planet' and favorite_id is None:
                        favorites = Favorites.query.all()
                        favorite_planet = filter_planet(favorites)
                        return jsonify(favorite_planet), 200

                    elif nature == 'planet' and favorite_id is not None:
                        favorite = Favorites.query.get(favorite_id)
                        if favorite is None:
                            return jsonify({"message": "Error, couldn't find planet"}), 404
                        elif favorite is not None:
                            if favorite.serialize()["nature"] != "planets":
                                return jsonify({"message": "Error, favorite isn't a planet"}), 406
                            else:
                                return jsonify(favorite.serialize()), 200

# Work in Progress, POST method
@app.route("/users/<int:user_id>/favorites", methods=['POST'])
def handle_favorites(user_id = None):
    if request.method == 'POST':
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"message":"Error, couldn't find user"}), 404
        elif user is not None:

            body = request.json
            if body.get("nature") != "character" and body["nature"] != "planet" :
                return jsonify({"message":"Error, bad property"}), 400
            elif body.get("name") is None:
                return jsonify({"message":"Error, bad property"}), 400
            elif body.get("nature_id") is None :
                return jsonify({"message":"Error, bad property"}), 400

            new_favorite = Favorites(name=body.get("name"), nature=body.get("nature"), nature_id=body.get("nature_id"), user_id=user_id)
            
            db.session.add(new_favorite)

            try:
                db.session.commit()
                return jsonify(new_favorite.serialize()), 201
            except Exception as error:
                print(error.args)
                db.session.rollback()
                return jsonify({"message": f"Error {error.args}"}), 500

# Work in Progress, PUT method
@app.route("/users/<int:user_id>/favorites/<string:nature>/<int:favorite_id>", methods=['PUT'])
def update_favorite(user_id = None, nature = None, favorite_id=None):
    if request.method == 'PUT':
        body = request.json
        if user_id is None:
            return jsonify({"message": "Error, couldn't find user"}), 404
        else:
            if nature is None and nature != "character" and nature != "planet":
                return jsonify({"message": "Error, invalid or missing nature"}), 406
            else:
                updated_favorite = Favorites.query.get(favorite_id)
                if updated_favorite is None:
                    return jsonify({"message": "Error, couldn't find favorite"}), 404
                else:
                    updated_favorite.name = body.get("name")
                    updated_favorite.nature = body.get("nature")
                    updated_favorite.nature_id = body.get("nature_id")

                    try:
                        db.session.commit()
                        return jsonify([]), 201
                    except Exception as error:
                        print(error.args)
                        db.session.rollback()
                        return jsonify({"message": f"Error {error.args}"})

# Work Done, DELETE method
@app.route("/users/<int:user_id>/favorites/<string:nature>/<int:favorite_id>", methods=['DELETE'])
def delete_favorite(user_id = None, nature = None, favorite_id = None):
    if request.method == 'DELETE':
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"message": "Error, couldn't find user"}), 404
        elif user is not None:
            if nature is None and nature != "character" and nature != "planet":
                return jsonify({"message": "Error, invalid or missing nature"}), 406
            else:
                if favorite_id is None:
                    return jsonify({"message": "Error, missing favorite id"}), 400
                elif favorite_id is not None:
                    deleted_favorite = Favorites.query.get(favorite_id)
                    if deleted_favorite is None:
                        return jsonify({"message": "Error, couldn't find favorite"}), 404
                    elif deleted_favorite is not None:
                        db.session.delete(deleted_favorite)

                        try:
                            db.session.commit()
                            return jsonify([]), 204
                        except Exception as error:
                            print(error.args)
                            db.session.rollback()
                            return jsonify({"message": f"Error {error.args}"})

# Can unify these GETs, can call other databases from a function

# Planet methods, CRUD complete
# Works fine, gets planets from database
@app.route('/planets', methods=['GET'])
@app.route('/planets/<int:planet_id>', methods=['GET'])
def handle_planets(planet_id = None):
    if request.method == 'GET':
        if planet_id is None:
            planets = Planet()
            planets = planets.query.all()

            return jsonify(list(map(lambda item: item.serialize(), planets))), 200
        else:
            planet = Planet()
            planet = planet.query.get(planet_id)

            if planet:
                return jsonify(planet.serialize()), 200

        return jsonify({"message": "Not found"}), 404

# Works as intended, id also serializes second. Adds a planet to the database
@app.route('/planets', methods=['POST'])
def add_new_planet():
    if request.method == 'POST':
        body = request.json

        if body.get("name") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("rotation_period") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("orbital_period") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("terrain") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("diameter") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("population") is None:
            return jsonify({"message": "Error, property bad"}), 400

        new_planet = Planet( 
            name=body.get("name"), 
            rotation_period=body.get("rotation_period"),
            orbital_period=body.get("orbital_period"),
            terrain=body.get("terrain"),
            diameter=body.get("diameter"),
            population=body.get("population"),
        )
        db.session.add(new_planet)

        try:
            db.session.commit()
            return jsonify(new_planet.serialize()), 201
        except Exception as error:
            print(error.args)
            db.session.rollback()
            return jsonify({"message": f"Error {error.args}"}), 500

# Works as intended, allows to update a planet
@app.route('/planets', methods=['PUT'])
@app.route('/planets/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id = None):
    if request.method == 'PUT':
        body = request.json

        if planet_id is None:
            return jsonify({"message":"Error, bad request"}), 400
        elif planet_id is not None:
            update_planet = Planet.query.get(planet_id)
            if update_planet is None:
                return jsonify({"message": "Error, couldn't find planet"}), 404
            else:
                update_planet.name = body.get("name")
                update_planet.orbital_period = body.get("orbital_period")
                update_planet.rotation_period = body.get("rotation_period")
                update_planet.diameter = body.get("diameter")
                update_planet.population = body.get("population")
                update_planet.terrain = body.get("terrain")

                try:
                    db.session.commit()
                    return jsonify(update_planet.serialize()), 201
                except Exception as error:
                    print(error.args)
                    db.session.rollback()
                    return jsonify({"message": f"Error {error.args}"}), 500

# Work as intended, allows to delete a planet
@app.route('/planets', methods=['DELETE'])
@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id = None):
    if request.method == 'DELETE':
        if planet_id is None:
            return jsonify({"message": "Error, bad request"}), 400
        elif planet_id is not None:
            deleted_planet = Planet.query.get(planet_id)
            if deleted_planet is None:
                return jsonify({"message": "Error, couldn't find planet"}), 404
            else:
                db.session.delete(deleted_planet)

            try:
                db.session.commit()
                return jsonify([]), 204
            except Exception as error:
                print(error.args)
                db.session.rollback()
                return jsonify({"message": f"Error {error.args}"})

# Character methods, CRUD complete
# Works fine, gets characters from database
@app.route('/characters', methods=['GET'])
@app.route('/characters/<int:character_id>', methods=['GET'])
def handle_character(character_id = None):
    if request.method == 'GET':
        if character_id is None:
            characters = Character()
            characters = characters.query.all()

            return jsonify(list(map(lambda item: item.serialize(), characters))), 200
        else:
            character = Character()
            character = character.query.get(character_id)

            return jsonify(character.serialize()), 200

# Works fine, but now the id is somehow even lower. Adds a character to the database
@app.route('/characters', methods=['POST'])
def add_new_character():
    if request.method == 'POST':
        body = request.json

        if body.get("name") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("age") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("height") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("eye_color") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("hair_color") is None:
            return jsonify({"message": "Error, property bad"}), 400
        elif body.get("gender") is None:
            return jsonify({"message": "Error, property bad"}), 400

        new_character = Character(
            name=body.get("name"), 
            age=body.get("age"), 
            gender=body.get("gender"),
            height=body.get("height"),
            eye_color=body.get("eye_color"),
            hair_color=body.get("hair_color")
        )
        db.session.add(new_character)

        try:
            db.session.commit(),
            return jsonify(new_character.serialize()), 201
        except Exception as error:
            print(error.args)
            db.session.rollback()
            return jsonify({"message": f"Error {error.args}"}), 500

# Works as intended, allows to update a character
@app.route('/characters', methods=['PUT'])
@app.route('/characters/<int:character_id>', methods=['PUT'])
def update_character(character_id = None):
    if request.method == 'PUT':
        body = request.json
        if character_id is None:
            return jsonify({"message": "Error, bad request"}), 400
        elif character_id is not None:
            update_character = Character.query.get(character_id)

            if update_character is None:
                return jsonify({"message": "Error, couldn't find character"}), 404
            else:
                update_character.name=body.get("name") 
                update_character.age=body.get("age") 
                update_character.gender=body.get("gender")
                update_character.height=body.get("height")
                update_character.eye_color=body.get("eye_color")
                update_character.hair_color=body.get("hair_color")

                try:
                    db.session.commit()
                    return jsonify(update_character.serialize()), 201
                except Exception as error:
                    print(error.args)
                    db.session.rollback()
                    return jsonify({"message": f"Error {error.args}"}), 500

# Works as intended, allows to delete a character
@app.route('/characters', methods=['DELETE'])
@app.route('/characters/<int:character_id>', methods=['DELETE'])
def delete_character(character_id = None):
    if request.method == 'DELETE':
        if character_id is None:
            return jsonify({"message":"Error, bad request"}), 400
        elif character_id is not None:
            deleted_character = Character.query.get(character_id)
            if deleted_character is None:
                return jsonify({"message":"Error, couldn't find character"})
            else:
                db.session.delete(deleted_character)

            try:
                db.session.commit()
                return jsonify([]), 204
            except Exception as error:
                print(error.args)
                db.session.rollback()
                return jsonify({"message": f"Error {error.args}"})

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
