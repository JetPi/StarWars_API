from enum import Enum, unique
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Nature(Enum):
    character = "character",
    planets = "planet"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)

    favorites = db.relationship("Favorites", backref="user", uselist=True) #Stablishes a relation of one (User) to many (Favorites)

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
    nature = db.Column(db.Enum(Nature), nullable=False)
    name = db.Column(db.String(100))
    
    nature_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
  
    # __table_args__ = (db.UniqueConstraint(), {
    #     "user.id",
    #     "name_favorite"
    # })
   
    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "nature": self.nature.name
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