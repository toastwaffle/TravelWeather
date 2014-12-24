#!/usr/bin/env python2
"""Calculate weather along a driven route in the UK.

Makes use of the Google Maps Directions API, and the Met Office DataPoint API.
"""

import collections
import datetime
import urllib

import MySQLdb
import requests
from MySQLdb import cursors

class TravelWeatherException(Exception):
    """General case parent exception for this script."""

class FailedGoogleApiException(TravelWeatherException):
    """Exception for when calls to the Google Maps Directions API fail."""

class FailedMetOfficeApiException(TravelWeatherException):
    """Exception for when calls to the Met Office API fail."""

# Get from http://www.metoffice.gov.uk/datapoint/API
API_KEY = ''

DB = MySQLdb.connect(
    host='',
    user='',
    passwd='',
    db='',
    cursorclass=cursors.DictCursor
)

VISIBILITIES = {
    'UN': 'Unknown',
    'VP': 'Very poor - Less than 1 km',
    'PO': 'Poor - Between 1-4 km',
    'MO': 'Moderate - Between 4-10 km',
    'GO': 'Good - Between 10-20 km',
    'VG': 'Very good - Between 20-40 km',
    'EX': 'Excellent - More than 40 km'
}

WEATHERS = {
    'NA': 'Not available',
    '0': 'Clear night',
    '1': 'Sunny day',
    '2': 'Partly cloudy (night)',
    '3': 'Partly cloudy (day)',
    '4': 'Not used',
    '5': 'Mist',
    '6': 'Fog',
    '7': 'Cloudy',
    '8': 'Overcast',
    '9': 'Light rain shower (night)',
    '10': 'Light rain shower (day)',
    '11': 'Drizzle',
    '12': 'Light rain',
    '13': 'Heavy rain shower (night)',
    '14': 'Heavy rain shower (day)',
    '15': 'Heavy rain',
    '16': 'Sleet shower (night)',
    '17': 'Sleet shower (day)',
    '18': 'Sleet',
    '19': 'Hail shower (night)',
    '20': 'Hail shower (day)',
    '21': 'Hail',
    '22': 'Light snow shower (night)',
    '23': 'Light snow shower (day)',
    '24': 'Light snow',
    '25': 'Heavy snow shower (night)',
    '26': 'Heavy snow shower (day)',
    '27': 'Heavy snow',
    '28': 'Thunder shower (night)',
    '29': 'Thunder shower (day)',
    '30': 'Thunder'
}

CURSOR = DB.cursor()

WEATHER_STATION_SQL = (
    "SELECT "
    "    id, name, latitude, longitude, directions_lat, directions_long, time, "
    "    ("
    "        6378.10 * "
    "        ACOS("
    "            ("
    "                COS(RADIANS(directions_lat)) * "
    "                COS(RADIANS(latitude)) * "
    "                COS(RADIANS(directions_long) - RADIANS(longitude))"
    "            ) + ("
    "                SIN(RADIANS(directions_lat)) * "
    "                SIN(RADIANS(latitude))"
    "            )"
    "        )"
    "    ) AS distance_in_km "
    "FROM locations "
    "JOIN ("
    "    SELECT "
    "        {point.latitude} AS directions_lat,"
    "        {point.longitude} AS directions_long, "
    "        {point.time} AS time"
    ") AS p "
    "ORDER BY distance_in_km "
    "LIMIT 1"
)

_Point = collections.namedtuple("Point", ["latitude", "longitude", "time"])

class Point(_Point):
    """Type for storing points on a route to get weather information for.

    Attributes:
        latitude (float): Interpolated latitude of the point
        longitude (float): Interpolated longitude of the point
        time (int): Time in minutes since start of journey
    """

_WeatherStation = collections.namedtuple("WeatherStation",
                                         ["station_id", "name", "time"])

class WeatherStation(_WeatherStation):
    """Type for storing the nearest weather station to the points on the route

    Attributes:
        station_id (string): The Met Office ID for this station
        name (string): The name of the station
        time (int): Time in minutes since start of journey
    """

def get_directions(origin, destination):
    """Retrieves directions from origin to destination.

    Args:
        origin (str): Starting point of the route
        destination (str): Ending point of the route
    """
    query = urllib.urlencode(
        {
            'origin': origin,
            'destination': destination,
            'sensor': 'false',
            'region': 'uk'
        }
    )

    url = 'http://maps.googleapis.com/maps/api/directions/json?' + query

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()

    raise FailedGoogleApiException(
        "Could not retrieve directions: status {0}".format(response.status_code)
    )

def get_half_hourly_points(directions):
    """Get interpolated points at each half-hour along the route.

    Args:
        directions (dict): Parsed JSON response from the Google Maps API

    Yields:
        a Point object for each point along the route
    """
    yield Point(
        latitude=directions['routes'][0]['legs'][0]['start_location']['lat'],
        longitude=directions['routes'][0]['legs'][0]['start_location']['lng'],
        time=0
    )

    time = 0
    point_time = 30

    for step in directions['routes'][0]['legs'][0]['steps']:
        duration = step['duration']['value']
        jumpcount = 1

        while (time + duration) > 1800:
            ratio = (
                (
                    (
                        jumpcount *
                        1800
                    ) -
                    time
                ) /
                float(step['duration']['value'])
            )

            latitude = (
                step['start_location']['lat'] +
                (
                    ratio *
                    (
                        step['end_location']['lat'] -
                        step['start_location']['lat']
                    )
                )
            )

            longitude = (
                step['start_location']['lng'] +
                (
                    ratio *
                    (
                        step['end_location']['lng'] -
                        step['start_location']['lng']
                    )
                )
            )

            yield Point(
                latitude=latitude,
                longitude=longitude,
                time=point_time
            )

            duration = duration - 1800
            jumpcount = jumpcount + 1
            point_time = point_time + 30

        time = (time + duration) % 1800

    final_time = directions['routes'][0]['legs'][0]['duration']['value'] / 60

    if final_time % 30 != 0:
        yield Point(
            latitude=directions['routes'][0]['legs'][0]['end_location']['lat'],
            longitude=directions['routes'][0]['legs'][0]['end_location']['lng'],
            time=final_time
        )

def get_weather_stations(directions):
    """Determines the nearest weather station to each point along the route.

    Points are calculated at every half an hour, and interpolated between the
    endpoints of each leg.

    Args:
        directions (dict): Parsed JSON response from the Google Maps API

    Yields:
        a WeatherStation object for each point along the route
    """
    for point in get_half_hourly_points(directions):
        CURSOR.execute(WEATHER_STATION_SQL.format(point=point))

        station = CURSOR.fetchone()

        yield WeatherStation(station_id=station["id"],
                             name=station["name"],
                             time=station["time"])

def get_forecast(station, time):
    """Retrieves the forecast for the given station at the given time.

    Args:
        station (WeatherStation): The station to retrieve the forecast for
        time (datetime.datetime): The time to retrieve the forecast for. This
            must have 0 values for the minutes, seconds and microseconds, and
            the hour value must be a multiple of 3

    Returns:
        (dict) A dictionary of forecast data as per the API specification
    """
    query = urllib.urlencode(
        {
            'res': '3hourly',
            'time': time.strftime('%Y-%m-%dT%HZ'),
            'key': API_KEY
        }
    )

    url = (
        'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs'
        '/all/json/{0}?{1}'
    ).format(
        station.station_id,
        query
    )

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()['SiteRep']['DV']['Location']['Period']['Rep']

    raise FailedMetOfficeApiException(
        "Could not get forecast: status {0}".format(response.status_code)
    )

def print_forecast(station, time):
    """Print out a forecast for the given station at the given time.

    Normalises the time to fit the standard needed for the API, retrieves the
    forecast and prints a neat representation.

    Args:
        station (WeatherStation): The station to retrieve the forecast for
        time (datetime.datetime): The time to retrieve the forecast for.
    """
    try:
        forecasttime = datetime.datetime(
            time.year,
            time.month,
            time.day,
            (time.hour / 3) * 3
        )

        forecast = get_forecast(station, forecasttime)

        forecastendtime = forecasttime + datetime.timedelta(minutes=180)

        print (
            'Forecast for time {0}-{1} : {2}\n'
            '    Temperature {3} celsius (feels like {4} celsius)\n'
            '    Wind {5}mph from {6}, gusting {7}mph\n'
            '    Precipitation: {8}% probability\n'
            '    Humidity: {9}%\n'
            '    Visibility: {10}\n'
            '    UV Index: {11}'
        ).format(
            forecasttime.strftime('%H%p'),
            forecastendtime.strftime('%H%p'),
            WEATHERS[forecast['W']],
            forecast['T'],
            forecast['F'],
            forecast['S'],
            forecast['D'],
            forecast['G'],
            forecast['Pp'],
            forecast['H'],
            VISIBILITIES[forecast['V']],
            forecast['U']
        )
    except FailedMetOfficeApiException as exception:
        print "No Forecast Available ({0})".format(exception)

def main():
    """Do all the work."""
    origin = raw_input('Enter Starting Address: ')
    destination = raw_input('Enter Destination Address: ')
    starttime = datetime.datetime.strptime(
        raw_input('Enter Departure Date/Time (YYYY-MM-DD HH:MM): '),
        '%Y-%m-%d %H:%M'
    )

    directions = get_directions(origin, destination)

    for index, station in enumerate(get_weather_stations(directions)):
        time = starttime + datetime.timedelta(minutes=station.time)

        print ''

        print 'Point {0}, Weather Station {1}, Time {2} ({3}hr{4})'.format(
            index + 1,
            station.name,
            time.strftime('%H:%M'),
            station.time / 60,
            station.time % 60
        )

        print_forecast(station, time)

        print ''

if __name__ == '__main__':
    main()
