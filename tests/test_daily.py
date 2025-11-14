from datetime import timedelta
from unittest.mock import patch

import pytest

from game.daily import RoundStats, get_daily_country, handle_guess
from phase2.country import Country


class TempCountry(Country):
    def __init__(self, name):
        self.name = name
        self.population = 0
        self.size = 0.0
        self.region = ""
        self.languages = []
        self.currencies = []
        self.timezones = []


@pytest.fixture
def round_stats() -> RoundStats:
    return RoundStats()


@pytest.fixture
def mocked_get_daily_country():
    patcher = patch("game.daily.get_daily_country")
    mock = patcher.start()
    mock.return_value = TempCountry("Canada")
    yield mock
    patcher.stop()


@pytest.fixture
def mocked_compare_countries():
    patcher = patch("game.daily.compare_countries")
    mock = patcher.start()
    mock
    yield mock
    patcher.stop()


def test_get_daily_country_same_country_for_same_day():
    first_call = get_daily_country()
    second_call = get_daily_country()

    assert isinstance(first_call, Country)
    assert first_call.name == second_call.name


def test_handle_guess_correct(round_stats, mocked_get_daily_country, mocked_compare_countries):
    user_guess = TempCountry("Canada")

    mocked_compare_countries.return_value = True
    handle_guess(user_guess.name, round_stats)

    assert round_stats.guesses == 1
    assert round_stats.round_time  # game ended


def test_handle_guess_incorrect(round_stats, mocked_get_daily_country, mocked_compare_countries):
    user_guess = TempCountry("United States")

    mocked_compare_countries.return_value = False
    handle_guess(user_guess.name, round_stats)

    assert round_stats.guesses == 1
    assert round_stats.round_time == timedelta()  # game not ended


def test_handle_guess_max_guesses(round_stats, mocked_get_daily_country, mocked_compare_countries):
    round_stats.guesses = round_stats.max_guesses - 1

    mocked_compare_countries.return_value = False
    user_guess = TempCountry("United States")

    handle_guess(user_guess.name, round_stats)

    assert round_stats.guesses == round_stats.max_guesses
    assert round_stats.round_time
