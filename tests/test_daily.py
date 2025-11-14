import datetime
from io import StringIO
from unittest.mock import patch

from game import daily
from game.daily import compare_countries
from phase2.country import Country, get_country, get_random_country


class TempCountry(Country):
        def __init__(self, name):
            self.name = name
            self.population = 0
            self.size = 0.0
            self.region = ""
            self.languages = []
            self.currencies = []
            self.timezones = []


# temp methods for compare_countries and end_game
def temp_compare_countries(guess, answer):
    return guess.name == answer.name

def temp_end_game(won):
    global end_game_called
    end_game_called = won

daily.compare_countries = temp_compare_countries
daily.end_game = temp_end_game

def test_get_daily_country_same_country_for_same_day(): 
    first_call = daily.get_daily_country()
    second_call = daily.get_daily_country()

    assert isinstance(first_call, Country)
    assert first_call.name == second_call.name


def test_handle_guess_correct():
    global end_game_called
    end_game_called = None
    daily.guesses = 0

    daily_country = TempCountry("Canada")
    user_guess = TempCountry("Canada")

    daily.get_daily_country = lambda: daily_country

    result = daily.handle_guess(user_guess.name)
    assert result is True
    assert daily.guesses == 1
    assert end_game_called is True  # game ended


def test_handle_guess_incorrect():
    global end_game_called
    end_game_called = None
    daily.guesses = 0

    daily_country = TempCountry("Canada")
    user_guess = TempCountry("United States")

    daily.get_daily_country = lambda: daily_country

    result = daily.handle_guess(user_guess.name)
    assert result is False
    assert daily.guesses == 1
    assert end_game_called is None  # game not ended


def test_handle_guess_max_guesses():
    global end_game_called
    end_game_called = None
    daily.guesses = daily.MAX_GUESSES - 1

    daily_country = TempCountry("Canada")
    user_guess = TempCountry("United States")

    daily.get_daily_country = lambda: daily_country

    result = daily.handle_guess(user_guess.name)
    assert result is False
    assert daily.guesses == daily.MAX_GUESSES
    assert end_game_called is False

# ---------------- NAME CHECKS ----------------

def test_returns_true_when_names_match():
    """Returns True when names match exactly."""
    c1 = Country("X", 1000000, 100000.0, "R1", ["L1"], ["C1"], ["UTC+0"])
    c2 = Country("X", 1000000, 100000.0, "R", ["L"], ["C"], ["UTC+0"])
    assert compare_countries(c1, c2) is True


def test_case_insensitive_name_comparison():
    """Returns True even if case differs."""
    c1 = Country("abc", 1000000, 100000.0, "R", ["L"], ["C"], ["UTC+0"])
    c2 = Country("ABC", 2000000, 100000.0, "R", ["L"], ["C"], ["UTC+0"])
    assert compare_countries(c1, c2) is True


def test_returns_false_when_names_differ():
    """Returns False when country names differ."""
    c1 = Country("A", 1000000, 100000.0, "R", ["L"], ["C"], ["UTC+0"])
    c2 = Country("B", 1000000, 100000.0, "R", ["L"], ["C"], ["UTC+0"])
    assert compare_countries(c1, c2) is False


# ---------------- POPULATION ----------------

def test_population_ratio_below_half():
    """Hint when guess < half of answer population."""
    g = Country("A", 1_000_000, 100000.0, "R", [], [], [])
    a = Country("B", 3_000_000, 100000.0, "R", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "MORE THAN DOUBLE" in output.getvalue()


def test_population_ratio_below_ninety_percent():
    """Hint when guess is 50–90% of answer population."""
    g = Country("A", 8_000_000, 100000.0, "R", [], [], [])
    a = Country("B", 10_000_000, 100000.0, "R", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "HIGHER population" in output.getvalue()


def test_population_ratio_similar():
    """Hint when guess within ±10% population."""
    g = Country("A", 10_000_000, 100000.0, "R", [], [], [])
    a = Country("B", 10_500_000, 100000.0, "R", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "Very close in population" in output.getvalue()


def test_population_ratio_above_double():
    """Hint when guess > double the answer population."""
    g = Country("A", 30_000_000, 100000.0, "R", [], [], [])
    a = Country("B", 10_000_000, 100000.0, "R", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "LESS THAN HALF" in output.getvalue()


# ---------------- SIZE ----------------

def test_size_ratio_below_half():
    """Hint when guess area < half of answer."""
    g = Country("A", 1_000_000, 100000.0, "R", [], [], [])
    a = Country("B", 1_000_000, 300000.0, "R", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "MORE THAN DOUBLE the area" in output.getvalue()


def test_size_ratio_below_ninety_percent():
    """Hint when guess area is 50–90% of correct answer."""
    g = Country("A", 1_000_000, 80_000.0, "R", [], [], [])
    a = Country("B", 1_000_000, 100_000.0, "R", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "LARGER in area" in output.getvalue()


def test_size_ratio_similar():
    """Hint when guess area within ±10%."""
    g = Country("A", 1_000_000, 100_000.0, "R", [], [], [])
    a = Country("B", 1_000_000, 105_000.0, "R", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "Very close in area" in output.getvalue()


def test_size_ratio_above_double():
    """Hint when guess area > double the answer."""
    g = Country("A", 1_000_000, 300_000.0, "R", [], [], [])
    a = Country("B", 1_000_000, 100_000.0, "R", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "LESS THAN HALF the area" in output.getvalue()


# ---------------- REGION ----------------

def test_region_matches():
    """Hint when both regions are same."""
    g = Country("A", 1000000, 100000.0, "R1", [], [], [])
    a = Country("B", 1000000, 100000.0, "R1", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "Same region" in output.getvalue()


def test_region_differs():
    """Hint when regions differ."""
    g = Country("A", 1000000, 100000.0, "R1", [], [], [])
    a = Country("B", 1000000, 100000.0, "R2", [], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "Different region" in output.getvalue()


# ---------------- CURRENCIES ----------------

def test_currencies_exact_match():
    """Hint when all currencies match exactly."""
    g = Country("A", 1000000, 100000.0, "R", [], ["C1", "C2"], [])
    a = Country("B", 1000000, 100000.0, "R", [], ["C1", "C2"], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "Exact match on all currencies" in output.getvalue()


def test_currencies_partial_match():
    """Hint when some currencies overlap."""
    g = Country("A", 1000000, 100000.0, "R", [], ["C1", "C2"], [])
    a = Country("B", 1000000, 100000.0, "R", [], ["C2"], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "Partial match" in output.getvalue()


def test_currencies_no_match():
    """Hint when currencies don’t overlap."""
    g = Country("A", 1000000, 100000.0, "R", [], ["C1"], [])
    a = Country("B", 1000000, 100000.0, "R", [], ["C2"], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "No matching currencies" in output.getvalue()


# ---------------- LANGUAGES ----------------

def test_languages_exact_match():
    """Hint when all languages match."""
    g = Country("A", 1000000, 100000.0, "R", ["L1", "L2"], [], [])
    a = Country("B", 1000000, 100000.0, "R", ["L1", "L2"], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "Exact match on all languages" in output.getvalue()


def test_languages_partial_match():
    """Hint when some languages overlap."""
    g = Country("A", 1000000, 100000.0, "R", ["L1", "L2"], [], [])
    a = Country("B", 1000000, 100000.0, "R", ["L2"], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "Partial match" in output.getvalue()


def test_languages_no_match():
    """Hint when languages don’t overlap."""
    g = Country("A", 1000000, 100000.0, "R", ["L1"], [], [])
    a = Country("B", 1000000, 100000.0, "R", ["L2"], [], [])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "No matching languages" in output.getvalue()


# ---------------- TIMEZONES ----------------

def test_timezones_exact_match():
    """Hint when all timezones match."""
    g = Country("A", 1000000, 100000.0, "R", [], [], ["UTC+1"])
    a = Country("B", 1000000, 100000.0, "R", [], [], ["UTC+1"])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "Exact match on all timezones" in output.getvalue()


def test_timezones_partial_match():
    """Hint when some timezones overlap."""
    g = Country("A", 1000000, 100000.0, "R", [], [], ["UTC+1", "UTC+2"])
    a = Country("B", 1000000, 100000.0, "R", [], [], ["UTC+1"])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "overlap" in output.getvalue()


def test_timezones_no_match():
    """Hint when timezones differ completely."""
    g = Country("A", 1000000, 100000.0, "R", [], [], ["UTC+1"])
    a = Country("B", 1000000, 100000.0, "R", [], [], ["UTC-5"])
    with patch('sys.stdout', new=StringIO()) as output:
        compare_countries(g, a)
        assert "No matching timezones" in output.getvalue()


