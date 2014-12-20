#!/usr/bin/env python2

import requests
from urllib import urlencode
import MySQLdb
from MySQLdb.cursors import DictCursor
from datetime import datetime, timedelta

API_KEY = '' # Get from http://www.metoffice.gov.uk/datapoint/API

DB = MySQLdb.connect(
    host='',
    user='',
    passwd='',
    db='',
    cursorclass=DictCursor
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

def main():
    start = raw_input('Enter Starting Address: ')
    dest = raw_input('Enter Destination Address: ')
    starttime = datetime.strptime(
        raw_input('Enter Departure Date/Time (YYYY-MM-DD HH:MM): '),
        '%Y-%m-%d %H:%M'
    )

    query = urlencode(
        {
            'origin': start,
            'destination': dest,
            'sensor': 'false',
            'region': 'uk'
        }
    )

    url = 'http://maps.googleapis.com/maps/api/directions/json?' + query

    r = requests.get(url)

    if r.status_code == 200:
        j = r.json()

        time = 0
        points = [
            (
                j['routes'][0]['legs'][0]['start_location']['lat'],
                j['routes'][0]['legs'][0]['start_location']['lng'],
                0
            )
        ]
        point_time = 30

        for step in j['routes'][0]['legs'][0]['steps']:
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

                points.append((latitude,longitude,point_time))

                duration = duration - 1800
                jumpcount = jumpcount + 1
                point_time = point_time + 30

            time = (time + duration) % 1800

        points.append(
            (
                j['routes'][0]['legs'][0]['end_location']['lat'],
                j['routes'][0]['legs'][0]['end_location']['lng'],
                j['routes'][0]['legs'][0]['duration']['value'] / 60
            )
        )

        sql = (
            "SELECT id, name, latitude, longitude, directions_lat, directions_long, time, "
            "    (6378.10 * ACOS(COS(RADIANS(directions_lat)) "
            "                * COS(RADIANS(latitude)) "
            "                * COS(RADIANS(directions_long) - RADIANS(longitude)) "
            "                + SIN(RADIANS(directions_lat)) "
            "                * SIN(RADIANS(latitude)))) AS distance_in_km "
            "FROM locations "
            "JOIN ( "
            "    SELECT {0} AS directions_lat, {1} AS directions_long, {2} AS time "
            "  ) AS p "
            "ORDER BY distance_in_km "
            "LIMIT 1"
        )

        for index, point in enumerate(points):
            CURSOR.execute(sql.format(*point))

            location = CURSOR.fetchone()

            realtime = starttime + timedelta(minutes=location['time'])

            print ''

            print 'Point {0}, Weather Station {1}, Time {2} ({3}hr{4})'.format(
                index + 1,
                location['name'],
                realtime.strftime('%H:%M'),
                location['time'] / 60,
                location['time'] % 60
            )

            forecasttime = datetime(
                realtime.year,
                realtime.month,
                realtime.day,
                (realtime.hour / 3) * 3
            )

            forecastendtime = forecasttime + timedelta(minutes=180)

            query = urlencode(
                {
                    'res': '3hourly',
                    'time': forecasttime.strftime('%Y-%m-%dT%HZ'),
                    'key': API_KEY
                }
            )

            url = (
                'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs'
                '/all/json/{0}?{1}'
            ).format(
                location['id'],
                query
            )

            r = requests.get(url)

            if r.status_code == 200:
                forecast = r.json()['SiteRep']['DV']['Location']['Period']['Rep']

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
            else:
                print 'No Forecast Available.'

            print ''

if __name__ == '__main__':
    main()
