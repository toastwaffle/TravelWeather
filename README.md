travel_weather.py
=================

A simple tool to get a weather forecast for a (UK) journey. Uses the Google Maps Directions API and the Met Office DataPoint API.

## Instructions for use

    # git clone https://github.com/toastwaffle/TravelWeather.git
    # virtualenv2 TravelWeather
    # cd TravelWeather
    # source bin/activate
    # pip install -r requirements.txt

 * Create MySQL database and import weather.sql
 * Update travel_weather.py with database config and Met Office API key

`  # ./travel_weather.py`

## Sample Usage

    # ./travel_weather.py

    Enter Starting Address: Manchester
    Enter Destination Address: London
    Enter Departure Date/Time (YYYY-MM-DD HH:MM): 2014-12-20 13:00

    Point 1, Weather Station Manchester, Time 13:00 (0hr0)
    Forecast for time 12PM-15PM : Cloudy
        Temperature 8 celsius (feels like 5 celsius)
        Wind 11mph from W, gusting 29mph
        Precipitation: 5% probability
        Humidity: 78%
        Visibility: Good - Between 10-20 km
        UV Index: 1


    Point 2, Weather Station Knutsford, Time 13:30 (0hr30)
    Forecast for time 12PM-15PM : Cloudy
        Temperature 8 celsius (feels like 4 celsius)
        Wind 16mph from WNW, gusting 29mph
        Precipitation: 19% probability
        Humidity: 84%
        Visibility: Good - Between 10-20 km
        UV Index: 1


    Point 3, Weather Station Stone, Time 14:00 (1hr0)
    Forecast for time 12PM-15PM : Heavy rain
        Temperature 8 celsius (feels like 4 celsius)
        Wind 13mph from WNW, gusting 29mph
        Precipitation: 79% probability
        Humidity: 73%
        Visibility: Moderate - Between 4-10 km
        UV Index: 1


    Point 4, Weather Station Sutton Coldfield, Time 14:30 (1hr30)
    Forecast for time 12PM-15PM : Cloudy
        Temperature 8 celsius (feels like 5 celsius)
        Wind 11mph from WNW, gusting 25mph
        Precipitation: 7% probability
        Humidity: 72%
        Visibility: Good - Between 10-20 km
        UV Index: 1


    Point 5, Weather Station Stanford Hall, Time 15:00 (2hr0)
    Forecast for time 15PM-18PM : Partly cloudy (day)
        Temperature 7 celsius (feels like 3 celsius)
        Wind 16mph from WNW, gusting 27mph
        Precipitation: 1% probability
        Humidity: 72%
        Visibility: Good - Between 10-20 km
        UV Index: 1


    Point 6, Weather Station Linford Wood, Time 15:30 (2hr30)
    Forecast for time 15PM-18PM : Partly cloudy (day)
        Temperature 7 celsius (feels like 4 celsius)
        Wind 13mph from WNW, gusting 22mph
        Precipitation: 4% probability
        Humidity: 70%
        Visibility: Very good - Between 20-40 km
        UV Index: 1


    Point 7, Weather Station Royal National Rose Society Gardens, Time 16:00 (3hr0)
    Forecast for time 15PM-18PM : Partly cloudy (day)
        Temperature 7 celsius (feels like 4 celsius)
        Wind 11mph from WNW, gusting 25mph
        Precipitation: 0% probability
        Humidity: 70%
        Visibility: Very good - Between 20-40 km
        UV Index: 1


    Point 8, Weather Station Hyde Park, Time 16:30 (3hr30)
    Forecast for time 15PM-18PM : Partly cloudy (day)
        Temperature 9 celsius (feels like 6 celsius)
        Wind 13mph from WNW, gusting 25mph
        Precipitation: 3% probability
        Humidity: 63%
        Visibility: Good - Between 10-20 km
        UV Index: 1


    Point 9, Weather Station London, Time 16:34 (3hr34)
    Forecast for time 15PM-18PM : Partly cloudy (day)
        Temperature 9 celsius (feels like 6 celsius)
        Wind 11mph from WNW, gusting 25mph
        Precipitation: 1% probability
        Humidity: 63%
        Visibility: Good - Between 10-20 km
        UV Index: 1
