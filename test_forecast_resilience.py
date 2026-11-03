"""Offline regressions for weather failures and HTTP responsiveness."""

import asyncio
import threading
import time
from unittest.mock import Mock

import httpx
import pandas as pd
import pytest
import requests
from fastapi.testclient import TestClient

from app import app
from shared_code import ml, solar, weatherforecast

INSTALLATION = {
    "date": "23-10-2026",
    "location": {"lat": 45.0, "lng": 9.0},
    "timezone": "UTC",
    "days": 1,
}


@pytest.mark.parametrize("provider", ["openmeteo", "openweathermap"])
@pytest.mark.parametrize(
    "error,status", [(requests.Timeout, 504), (requests.ConnectionError, 502)]
)
def test_weather_failures_are_bounded_and_reported(
    monkeypatch, provider, error, status
):
    get = Mock(side_effect=error("provider unavailable"))
    monkeypatch.setattr(weatherforecast.requests, "get", get)
    response = TestClient(app).post(
        "/forecast", params={"provider": provider}, json=INSTALLATION
    )
    assert response.status_code == status
    assert get.call_args.kwargs["timeout"] == (3, 10)


def test_weather_http_error_is_not_parsed_as_forecast(monkeypatch):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("503")
    monkeypatch.setattr(weatherforecast.requests, "get", Mock(return_value=response))
    result = TestClient(app).post("/forecast", json=INSTALLATION)
    assert result.status_code == 502
    response.json.assert_not_called()


def test_successful_forecast_keeps_response_shape(monkeypatch):
    monkeypatch.setattr(
        weatherforecast,
        "getOpenMeteoData",
        lambda _: pd.DataFrame({"dt": [1], "clear_sky": [0]}),
    )
    monkeypatch.setattr(
        solar, "getClearSky", lambda *args, **kwargs: pd.DataFrame({"clear_sky": [100]})
    )
    monkeypatch.setattr(
        ml, "enrichDataFrameWithPrediction", lambda frame: frame.assign(P_predicted=50)
    )
    response = TestClient(app).post("/forecast", json=INSTALLATION)
    assert response.status_code == 200
    assert response.json() == [{"dt": 1, "clear_sky": 100, "P_predicted": 50}]


def test_waiting_for_weather_does_not_block_other_http_requests(monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def slow_weather(_):
        started.set()
        release.wait(2)
        raise requests.Timeout()

    monkeypatch.setattr(weatherforecast, "getOpenMeteoData", slow_weather)

    async def exercise():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            start = time.monotonic()
            forecast = asyncio.create_task(client.post("/forecast", json=INSTALLATION))
            try:
                while not started.is_set():
                    await asyncio.sleep(0.005)
                probe = await client.get("/openapi.json")
                assert probe.status_code == 200
                assert time.monotonic() - start < 1
            finally:
                release.set()
                response = await forecast
            assert response.status_code == 504

    asyncio.run(exercise())
