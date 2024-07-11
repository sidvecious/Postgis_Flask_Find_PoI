# PostGIS-Flask Application

This Flask application integrates with PostGIS, h3 JS and Leaflet JS 
to handle geospatial data and test the performance of PostGIS queries 
for finding points of interest in a certain area.

Map based on OpenStreetMap (c) data, OpenStreetMap contributors
## Setup

### Install Requirements

Install the required dependencies:

```sh
pip install -r requirements.txt
python populate.py

flask --app app run --debug
# open http://127.0.0.1:5000
This `README.md` file provides a brief overview of setting up and running your PostGIS-Flask application, focusing on installing dependencies and starting the Flask server.