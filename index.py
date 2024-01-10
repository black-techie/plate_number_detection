from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
import sqlite3

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "change_to_your_jwt_secret_key"
jwt = JWTManager(app)

DATABASE = "./storage/database.db"


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    phone = data.get("phone")

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO administration (username, password, phone) VALUES (?, ?, ?)",
            (username, password, phone),
        )
        connection.commit()

    return jsonify(message="Registration successful"), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM administration WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and (user[2], password):
            access_token = create_access_token(
                identity={"username": user[1], "id": user[0]}
            )
            return jsonify(access_token=access_token, message="successful"), 200
        else:
            return jsonify(message="Invalid username or password"), 401


@app.route("/api/check_number_plate", methods=["POST"])
def check_number_plate():
    number_plate = request.get_json().get("number_plate")
    return number_plate


@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


if __name__ == "__main__":
    app.run(port=5555, debug=True, host="0.0.0.0")
