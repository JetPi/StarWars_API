from enum import unique
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            # do not serialize the password, its a security breach
        }

# Funky, need to check relations
class Favorites(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    user = db.relationship("User")
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), unique=False)
    character = db.relationship("Character")
    planet_id = db.Column(db.Integer, db.ForeignKey("planet.id"), unique=False)
    planet = db.relationship("Planet")

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user": self.user,
            "character_id": self.character_id,
            "character": self.character,
            "planet_id": self.planet_id,
            "planet": self.planet
        }

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    age = db.Column(db.String(50), nullable=False)
    height = db.Column(db.String(50), nullable=False)
    eye_color = db.Column(db.String(50),  nullable=False)
    hair_color = db.Column(db.String(50),  nullable=False)
    gender = db.Column(db.String(20), nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "height": self.height,
            "eye_color": self.eye_color,
            "hair_color": self.hair_color,
            "gender": self.gender
        }

class Planet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    rotation_period = db.Column(db.String(50), nullable=False)
    orbital_period = db.Column(db.String(50), nullable=False)
    terrain = db.Column(db.String(50), nullable=False)
    diameter = db.Column(db.String(50), nullable=False)
    population = db.Column(db.String(50), nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "rotation_period": self.rotation_period,
            "orbital_period": self.orbital_period,
            "terrain": self.terrain,
            "diameter": self.diameter,
            "population": self.population
        }