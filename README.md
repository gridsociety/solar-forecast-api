[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build & deploy to Azure Web App](https://github.com/tribp/solar-forecast-api/actions/workflows/main_solar-forecast-api.yml/badge.svg?branch=main)](https://github.com/tribp/solar-forecast-api/actions/workflows/main_solar-forecast-api.yml)
[![Build & deploy Azure Web App - Dev](https://github.com/tribp/solar-forecast-api/actions/workflows/dev_solar-forecast-api-dev.yml/badge.svg?branch=dev)](https://github.com/tribp/solar-forecast-api/actions/workflows/dev_solar-forecast-api-dev.yml)

# solar-forecast-api

# Solar - Forecast

OC:

1. Intro
2. Concept
3. Architecture

## 1. Intro

**Goal:** Calculating the power production of your solar installation and predicting your solar energy for the next 7 days, also available as an API for integration with a HEMS (Home Energy Management System) like Home Assistant or others.

**Calculating:**

- `clear sky` Power (Watt) for any given time of day
- `clear sky` Energy(kWh) for any given day
- `Typical real Energy` (kWh) per month and `Total`per year

**Predicting:**

- `Power Prediction` (Watt) for any given time for the next 7 days (or 48h)
- `Energy Prediction` (kWh) for the next 7 days (or 48h)
- `Typical Prediction` (kWh) per month and `Total`per year

<img src= "./img/solar-forecast_UI_browser.jpg" width="600px">

## 2. Concept

There are 2 parts:

**API:**

[api.solar-forecast.org](https://api.solar-forecast.org) is the main part, typically used as a service for a HEMS (Home Energy Management System). The API gets the `installation data` in the body of a POST request and provides a response for the `clear sky` or `prediction`. You can optionaly specify a "weather provider" (open-meteo or openweathermap) by adding a "query" parameter `provider` in the POST request.

See [details](https://api.solar-forecast.org/docs) or `perform tests` in the `swagger` documentation.

**Example:**

```
curl -X 'POST' \
  'https://api.solar-forecast.org/forecast?provider=openmeteo' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "date": "21-01-2023",
  "location": {
    "lat": 51,
    "lng": 3.11
  },
  "altitude": 70,
  "tilt": 44,
  "azimuth": 170,
  "totalWattPeak": 7400,
  "wattInvertor": 5040,
  "timezone": "UTC"
}'

```

**UI - User Inreface:**

This is a web application [www.solar-forecast.org](https://solar-forecast.org) for visualizing the prediction or as aid for calculating your PV installation or exploring different orientations, dimensions, tilts or seasonal influences like winter and summer.

<img src= "./img/project.png" width="800px">

## 2. Architecture

<img src= "./img/solar-forecast-Architecture-Overall.jpg" width="800px">

## CI/CD

[Devop guidlines](./DEVOPS.md)

### Weather failures and responsiveness

Weather requests use a 3-second connect timeout and a 10-second read inactivity
timeout. These are not a total forecast deadline. Provider timeouts return HTTP
504; connection and HTTP failures return 502. The synchronous forecast handler
runs in FastAPI's worker pool so weather I/O does not block the HTTP event loop.

The image health check probes `/openapi.json` locally. It detects an unresponsive
HTTP server; it does not check forecast freshness or automatically restart an
unhealthy container. Deploy the rebuilt image to replace a currently stuck
process, then verify a real forecast and the planner's fallback behaviour.

Run the offline regression tests with:

```sh
pip install -r requirements-test.txt
python -m pytest test_forecast_resilience.py
```

The older `test_api.py` forecast tests call live weather providers and are not
part of this offline check.
