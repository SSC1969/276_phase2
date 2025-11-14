import random
from datetime import date, datetime, timedelta, timezone

from nicegui import Event

from phase2.country import Country, get_country, get_random_country

MAX_GUESSES = 5


class RoundStats:
    guesses: int = 0
    max_guesses: int
    round_start: datetime
    guess_graded: Event[str]
    game_ended: Event[bool]
    round_time: timedelta

    def __init__(self):
        self.guesses = 0
        self.max_guesses = MAX_GUESSES
        self.round_start = datetime.now(timezone.utc)

        # TODO: Replace with data type containing actual guess feedback
        self.guess_graded = Event[str]()
        self.game_ended = Event[bool]()
        self.round_time = timedelta()

    def end_round(self):
        self.round_time = datetime.now(timezone.utc) - self.round_start


def get_daily_country() -> Country:
    """
    Gets a country for today's date, deterministically
    """
    today_str = date.today().isoformat()
    random.seed(today_str)  # seed random with date (every daily country is the same)
    return get_random_country()


def handle_guess(input: str, round_stats: RoundStats):
    """
    Assumes input str is a valid country string

    Processes the given input. Ends the game if either end condition is reached
    (reached max guesses or guessed correctly)
    """
    round_stats.guesses += 1
    country = get_country(input)
    daily_country = get_daily_country()

    if compare_countries(country, daily_country):
        end_game(True, round_stats)
        round_stats.end_round()
    elif round_stats.guesses >= MAX_GUESSES:
        end_game(False, round_stats)
        round_stats.end_round()

    # TODO: Pass the comparison result from compare_countries to this call
    round_stats.guess_graded.emit(input)


def compare_countries(guess: Country, answer: Country):
    """
    Check if the two countries, match.
    If not, compare the following statistics for two countries:
    - Population
    - Geographical Size
    - Currencies
    - Languages
    - Timezones
    - Region
    """
    pass


def end_game(won: bool, round_stats: RoundStats):
    """
    End the game in either a win or a loss, and pass this game's statistics
    on to be processed in statistics.py, and show a breakdown of this game's
    stats to the user
    """
    pass
