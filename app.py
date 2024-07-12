from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from shapely import wkb
import geojson
import os
import time

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


@app.route('/')
def hello():
    return render_template('index.html')


@app.route("/find_location")
def find_location():
    args = request.args
    lat = args.get('lat', 0.0, type=float)
    lng = args.get('lng', 0.0, type=float)

    count = table_count("places")
    t0 = time.time()

    result = db.session.execute(
        text("""
            SELECT data, geom FROM places p 
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
        "duration_us": elapsed * 1_000_000, # microseconds
        "total_num": count
    }

def table_count(table):
    with db.session.begin():
        result = db.session.execute(text(f"SELECT COUNT(*) AS count FROM {table}"))
        count = result.scalar()
    return count


@app.route("/find_poi")
def find_poi():
    args = request.args
    lat = args.get('lat', 0.0, type=float)
    lng = args.get('lng', 0.0, type=float)

    count = table_count("poi")
    radius_in_meters = 100
    t0 = time.time()

    result = db.session.execute(
        text("""
            SELECT data, lng, lat FROM poi p
            WHERE ST_DistanceSphere(p.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) < :radius
        """),
        {'lng': lng, 'lat': lat, 'radius': radius_in_meters}
    ).fetchall()

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


@app.route("/find_position")
def find_position():
    args = request.args
    lat = args.get('lat', 0.0, type=float)
    lng = args.get('lng', 0.0, type=float)

    count = table_count("poi")
    radius_in_meters = 100
    t0 = time.time()

    result = db.session.execute(
        text("""
            SELECT data, lng, lat FROM poi p 
            WHERE ST_DistanceSphere(p.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) < :radius
        """),
        {'lng': lng, 'lat': lat, 'radius': radius_in_meters}
    ).fetchall()

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

def db_query(sql, args):
    t0 = time.time()
    result = db.session.execute(text(sql), args).fetchall()
    elapsed = time.time()-t0
    return (elapsed * 1_000_000, result)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
