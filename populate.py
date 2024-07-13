import os
import psycopg2
import json
import osmium
from urllib.parse import urlparse
from psycopg2 import ProgrammingError
from dotenv import load_dotenv

load_dotenv()

result = urlparse(os.getenv('DATABASE_URL'))

opts = {
    "database": result.path[1:],
    "host": result.hostname,
    "user": result.username,
    "password": result.password,
    "port": result.port
}

conn = psycopg2.connect(**opts)
cursor = conn.cursor()

# postGIS, Execute schema setup
with open('schema.sql', 'r') as file:
    cursor.execute(file.read())

# populate the boundary table with the boundary.json
try:
    with open('boundary.json', 'r') as fp:
        data = json.load(fp)

        for item in data:
            geom = item["geometry"]
            del item["geometry"]

            cursor.execute("INSERT INTO boundary (data, geom) VALUES (%s, %s)",
                           (json.dumps(dict(item)), geom))

    conn.commit()

except FileNotFoundError as e:
    print(f"File not found: {e}")
    conn.rollback()
except ProgrammingError as e:
    print(f"SQL execution error: {e}")
    conn.rollback()
except json.JSONDecodeError as e:
    print(f"Error reading JSON file: {e}")
    conn.rollback()


# Populate the points of interest table from poi.osm.pbf.
class AmenityListHandler(osmium.SimpleHandler):
    def node(self, n):
        lng = n.location.lon
        lat = n.location.lat
        data = json.dumps(dict(n.tags))
        cursor.execute(
            "INSERT INTO poi (lat, lng, data, geom) VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))",
            (lat, lng, data, lng, lat))


handler = AmenityListHandler()
handler.apply_file("poi.osm.pbf")

conn.commit()


