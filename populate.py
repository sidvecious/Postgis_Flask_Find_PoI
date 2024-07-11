import psycopg2
import json
import osmium

opts = {
    "database": "Postgis-flask-find-points",
    "host": "localhost",
    "user": "postgres",
    "password": "postgres",
    "port": "5432"
}

conn = psycopg2.connect(**opts)
cursor = conn.cursor()

# POSTGIS
cursor.execute(open('schema.sql', 'r').read())

# PLACES
try:
    with open('places.json', 'r') as fp:
        data = json.load(fp)

        for item in data:
            geom = item["geometry"]
            del item["geometry"]

            cursor.execute("INSERT INTO places (data, geom) VALUES (%s, %s)",
                           (json.dumps(dict(item)), geom))

    conn.commit()


except Exception as e:
    conn.rollback()
    print("Error inserting into places:", e)

# POI


class AmenityListHandler(osmium.SimpleHandler):
    def node(self, n):
        lng = n.location.lon
        lat = n.location.lat
        data = json.dumps(dict(n.tags))
        cursor.execute(
            "INSERT INTO poi (lat, lng, data, geom) VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))", (lat, lng, data, lng, lat))


handler = AmenityListHandler()
handler.apply_file("poi.osm.pbf")

conn.commit()