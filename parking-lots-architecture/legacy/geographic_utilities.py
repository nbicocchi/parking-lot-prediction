from math import asin, sin, cos, atan2, pi, radians, degrees, sqrt, pow
from statistics import mean

import pandas as pd
import requests

from data_management.database_utilities import get_db_connection


def compute_bbox(lat, lon, distance):
    lat = radians(lat)
    lon = radians(lon)
    distance *= sqrt(2)
    r = 6378.1
    lats, lons = list(), list()
    # compute latitude and longitude of two opposite vertices of a square centered in lat and lon with a 2*distance side
    for theta in [pi / 4, 5 / 4 * pi]:
        lat_tmp = asin(sin(lat) * cos(distance / r) + cos(lat) * sin(distance / r) * cos(theta))
        lon_tmp = lon + atan2(sin(theta) * sin(distance / r) * cos(lat), cos(distance / r) - sin(lat) * sin(lat_tmp))
        lats.append(lat_tmp)
        lons.append(lon_tmp)
    # bounding box in OpenStreetMap style
    bbox = (degrees(min(lats)), degrees(min(lons)), degrees(max(lats)), degrees(max(lons)))
    return bbox


def get_coords(cityname):
    nominatim_url = 'https://nominatim.openstreetmap.org/search'
    response = requests.get(nominatim_url, params={'city': cityname, 'limit': 1, 'format': 'json'}).json()
    if response and 'lat' in response[0].keys() and 'lon' in response[0].keys():
        return float(response[0]['lat']), float(response[0]['lon'])
    return None


def get_parkings_from_server(bbox):
    where_string = 'WHERE latitude >= {} AND longitude >= {} AND latitude <= {} and longitude <= {}'.format(*bbox)
    with get_db_connection().begin() as connection:
        parkings = pd.read_sql_query('SELECT * FROM parcheggio {}'.format(where_string), connection)
    return parkings


def get_parkings(bbox):
    overpass_url = 'http://overpass-api.de/api/interpreter'
    overpass_query = '[bbox:{},{},{},{}][out:json];'.format(*bbox)
    overpass_query += '(node["amenity"="parking"];way["amenity"="parking"];relation["amenity"="parking"];);out center;'
    response = requests.get(overpass_url, params={'data': overpass_query}).json()['elements']
    parking_coords = list()
    for p in response:
        if 'lat' in p.keys() and 'lon' in p.keys():
            parking_coords.append((p['lat'], p['lon']))
        elif 'center' in p.keys():
            parking_coords.append((p['center']['lat'], p['center']['lon']))
    center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    parking_list = sorted(parking_coords, key=lambda point: compute_distance(center, point))
    return dict(enumerate(parking_list))


def compute_distance(center, point):
    lat_center, lon_center = center
    lat_point, lon_point = point
    return sqrt(pow(lat_center - lat_point, 2) + pow(lon_center - lon_point, 2))


def parkings_map(coords):
    import plotly.graph_objs as go
    ids = coords.keys()
    lats = list(map(lambda c: c[0], coords.values()))
    lons = list(map(lambda c: c[1], coords.values()))
    fig = go.Figure(
        go.Scattermapbox(
            lat=lats,
            lon=lons,
            marker=dict(size=13),
            text=['{}: {} {}'.format(park_id, lat, lon) for park_id, lat, lon in zip(ids, lats, lons)]
        ))
    fig.update_layout(
        mapbox_style="open-street-map",
        autosize=True,
        hovermode='closest',
        mapbox=dict(center=dict(lat=mean(lats), lon=mean(lons)), zoom=13)
    )
    fig.show()
