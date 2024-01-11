from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from datetime import datetime
import sqlite3


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "change_to_your_jwt_secret_key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 7200
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


@app.route("/api/create_route", methods=["POST"])
@jwt_required()
def create_route():
    data = request.get_json()
    origin = data.get("origin")
    destination = data.get("destination")

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO routes (origin, destination) VALUES (?, ?)",
            (origin, destination),
        )
        connection.commit()
    return jsonify(message="route created successful"), 201


@app.route("/api/all_routes", methods=["GET"])
@jwt_required()
def routes():
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM routes")
        payments = cursor.fetchall()
        records = []
        for payment in payments:
            records.append(
                {"id": payment[0], "origin": payment[1], "destination": payment[2]}
            )
        return jsonify(records), 200


@app.route("/api/create_payment", methods=["POST"])
@jwt_required()
def create_payment():
    now = datetime.now()
    data = request.get_json()
    plate_number = data.get("plate_number")
    amount = data.get("amount")
    route_id = data.get("route_id")

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO payment (plate_number, amount, route_id, status, date) VALUES (?, ?, ?, ?, ?)",
            (plate_number, amount, route_id, False, now.strftime("%d/%m/%Y %H:%M:%S")),
        )
        connection.commit()
    return jsonify(message="Payment created successful"), 201


@app.route("/api/validate_payment", methods=["POST"])
def check_plate_number():
    plate_number = request.get_json().get("plate_number")
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM payment WHERE plate_number = ? AND status = ?",
            (plate_number, False),
        )
        payment = cursor.fetchone()
        if payment:
            cursor.execute(
                "UPDATE payment SET status = ? WHERE id = ?", (True, payment[0])
            )
            connection.commit()
            return (
                jsonify(
                    payment={
                        "id": payment[0],
                        "plate_number": payment[1],
                        "amount": payment[2],
                        "route_id": payment[3],
                        "status": payment[4],
                        "date": payment[5],
                    },
                    message="successful",
                ),
                200,
            )
        else:
            return jsonify(message="No valid payment available!"), 401


@app.route("/api/all_payments", methods=["GET"])
@jwt_required()
def payments():
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM payment")
        payments = cursor.fetchall()
        records = []
        for payment in payments:
            records.append(
                {
                    "id": payment[0],
                    "plate_number": payment[1],
                    "amount": payment[2],
                    "route_id": payment[3],
                    "status": payment[4],
                    "date": payment[5],
                }
            )
        return jsonify(records), 200


@app.route("/api/delete_payment", methods=["DELETE"])
@jwt_required()
def delete_payment():
    id = request.get_json().get("id")
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM payment WHERE id = ?",
            (id),
        )
        payment = cursor.fetchone()
        if payment:
            cursor.execute("DELETE FROM payment WHERE id = ?", (payment[0],))
            connection.commit()
            return jsonify(message="Payment deleted successfully"), 200
        else:
            return jsonify(message="Payment record not found!"), 404


if __name__ == "__main__":
    app.run(port=5555, debug=True, host="0.0.0.0")
