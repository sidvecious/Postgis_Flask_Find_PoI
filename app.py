from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from shapely import wkb
import geojson
import os
import time
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

radius_in_meters = 100

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def home_page():
    return render_template('index.html')

class InvalidCoordinatesError(Exception):
    def __init__(self, message):
        super().__init__(message)

# debugging function for the coordinates
def get_coordinates(args):
    try:
        lat = float(args.get('lat', ''))
        lng = float(args.get('lng', ''))
    except ValueError:
        raise InvalidCoordinatesError("Invalid 'lat' or 'lng' parameter")

    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        raise InvalidCoordinatesError("Invalid latitude values or Invalid longitude values")
    return lat, lng

# finds the boundary to which the searched point belongs
# poi.osm.pbf is focused on Berlin's points of interest.
@app.route("/find_boundary")
def find_boundary():
    try:
        args = request.args
        lat, lng = get_coordinates(args)

        count = table_count("boundary")
        t0 = time.time()

        result = db.session.execute(
            text("""
                SELECT data, geom FROM boundary p 
                WHERE ST_Within(ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), p.geom)
            """),
            {'lng': lng, 'lat': lat}
        ).fetchall()

        elapsed = time.time() - t0

        new_result = []
        for row in result:
            data, geom = row
            polygon = wkb.loads(geom)
            data["geom"] = geojson.Feature(geometry=polygon, properties={})
            new_result.append(data)

        return {
            "result": new_result,
            "duration_us": elapsed * 1_000_000,  # microseconds
            "total_num": count
        }
    except InvalidCoordinatesError as e:
        return jsonify({"error": "Invalid Coordinates", "message": str(e)}), 400
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected error", "message": str(e)}), 500

def table_count(table):
    with db.session.begin():
        result = db.session.execute(text(f"SELECT COUNT(*) AS count FROM {table}"))
        count = result.scalar()
    return count

# finds the point of interest from the selected starting point within a radius of radius_of_meters
# and displays it along with the circumference of interest.
@app.route("/find_poi")
def find_poi():
    try:
        args = request.args
        lat, lng = get_coordinates(args)

        count = table_count("poi")
        t0 = time.time()

        try:
            result = db.session.execute(
                text("""
                    SELECT data, lng, lat FROM poi p
                    WHERE ST_DistanceSphere(p.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) < :radius
                """),
                {'lng': lng, 'lat': lat, 'radius': radius_in_meters}
            ).fetchall()
        except SQLAlchemyError as e:
            return jsonify({"error": "Database error", "message": str(e)}), 500

        elapsed = time.time() - t0

        new_result = []
        for row in result:
            data, lng, lat = row
            data["pos"] = [lng, lat]
            new_result.append(data)

        return {
            "result": new_result,
            "duration_us": elapsed * 1_000_000,  # microseconds
            "total_num": count,
            "radius": radius_in_meters
        }
    except InvalidCoordinatesError as e:
        return jsonify({"error": "Invalid Coordinates", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Unexpected error", "message": str(e)}), 500

# finds the point of interest from the selected starting point within a radius of radius_of_meters
# and shows the openstreetmap data associated with the points in a json
@app.route("/find_position_data")
def find_position_data():
    try:
        args = request.args
        lat, lng = get_coordinates(args)

        count = table_count("poi")
        t0 = time.time()

        try:
            result = db.session.execute(
                text("""
                    SELECT data, lng, lat FROM poi p 
                    WHERE ST_DistanceSphere(p.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) < :radius
                """),
                {'lng': lng, 'lat': lat, 'radius': radius_in_meters}
            ).fetchall()
        except SQLAlchemyError as e:
            return jsonify({"error": "Database error", "message": str(e)}), 500

        elapsed = time.time() - t0

        new_result = []
        for row in result:
            data, lng, lat = row
            data["pos"] = [lng, lat]
            new_result.append(data)

        return {
            "result": new_result,
            "duration_us": elapsed * 1_000_000,
            "total_num": count,
        }
    except InvalidCoordinatesError as e:
        return jsonify({"error": "Invalid Coordinates", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Unexpected error", "message": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
