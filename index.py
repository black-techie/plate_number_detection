from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    make_response,
    redirect,
    url_for,
)
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    decode_token,
)
from datetime import datetime
import sqlite3


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "change_to_your_jwt_secret_key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 7200
jwt = JWTManager(app)


DATABASE = "./storage/database.db"


@app.route("/index")
def index():
    access_token = request.cookies.get("access_token")
    if access_token:
        decoded_token = decode_token(access_token)
        if str(decoded_token["sub"]["id"]) == request.cookies.get("id"):
            with sqlite3.connect(DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM payment")
                payments = cursor.fetchall()
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM administration")
                admins = cursor.fetchall()
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM routes")
                routes = cursor.fetchall()

                earnings = 0
                for data in payments:
                    earnings += data[2]

                return render_template(
                    "index.html",
                    _routes=len(routes),
                    _admins=len(admins),
                    _payments=len(payments),
                    _earnings="{:,}".format(earnings),
                )
        else:
            return redirect("/login")
    else:
        return redirect("/login")


@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")


@app.route("/api/register_", methods=["POST"])
def register_():
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


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/api/login_", methods=["POST"])
def login_():
    username = request.form.get("username")
    password = request.form.get("password")

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM administration WHERE username = ? AND password =?",
            (username, password),
        )
        user = cursor.fetchone()

        if user and (user[2], password):
            access_token = create_access_token(
                identity={"username": user[1], "id": user[0]}
            )
            response = make_response(redirect(url_for("index")))
            response.set_cookie("access_token", access_token)
            response.set_cookie("id", str(user[0]))
            return response
        else:
            return redirect("/login")


@app.route("/create_route", methods=["GET"])
def routes_():
    access_token = request.cookies.get("access_token")
    if access_token:
        decoded_token = decode_token(access_token)
        if str(decoded_token["sub"]["id"]) == request.cookies.get("id"):
            return render_template("route.html")
        else:
            return redirect("/login")
    else:
        return redirect("/login")


@app.route("/api/create_routes", methods=["POST"])
def create_route():
    origin = request.form.get("origin")
    destination = request.form.get("destination")

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO routes (origin, destination) VALUES (?, ?)",
            (origin, destination),
        )
        connection.commit()
    return redirect("/index")


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


@app.route("/create_payment", methods=["GET"])
def payment_():
    access_token = request.cookies.get("access_token")
    if access_token:
        decoded_token = decode_token(access_token)
        if str(decoded_token["sub"]["id"]) == request.cookies.get("id"):
            with sqlite3.connect(DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM routes")
                routes = []
                for route in cursor.fetchall():
                    routes.append(
                        {"id": route[0], "location": route[1] + ", " + route[2]}
                    )
                print(routes)
            return render_template("pay.html", routes=routes)
        else:
            return redirect("/login")
    else:
        return redirect("/login")


@app.route("/api/create_payment", methods=["POST"])
def create_payment():
    now = datetime.now()
    plate_number = request.form.get("plate_number")
    amount = request.form.get("amount")
    route_id = int(request.form.get("route"))

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO payment (plate_number, amount, route_id, status, date) VALUES (?, ?, ?, ?, ?)",
            (plate_number, amount, route_id, False, now.strftime("%d/%m/%Y %H:%M:%S")),
        )
        connection.commit()
    return redirect("/index")


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
