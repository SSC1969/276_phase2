import json
from datetime import datetime, timezone

from nicegui import ui

from game.daily import RoundStats, handle_guess

# NiceGUI elements go here

# display the game (guess input, guess feedback, timer, # of guesses, etc.)
"""
game

    - guess entry box
    - guess button
    - guess feedback

    - win/loss popup
"""


def content():
    round_stats = RoundStats()

    options = []
    with open("src/game/countries.json") as file:
        options = json.load(file)

    def is_guess_valid(guess: str) -> str | None:
        """
        Validates the given guess, either returning an error
        message if it's invalid, or None if it's valid.
        """
        if guess.lower() not in options:
            return "Not a valid country!"
        guessed_names = [d.get("name") for d in feedback.rows]
        if guess.capitalize() in guessed_names:
            return "Already guessed!"
        return None

    def try_guess():
        """
        Validates an inputted guess and passes it into the guess handler
        if it's valid.
        """
        if guess_input.validate():
            handle_guess(guess_input.value, round_stats)
            guess_input.value = ""

            # TODO: Move this emit into game_end()
            if len(feedback.rows) == 6:
                round_stats.game_ended.emit(False)

    # TODO: Add actual feedback instead of placeholder data
    @round_stats.guess_graded.subscribe
    def display_feedback(guess: str):
        """
        Displays the feedback passed as an argument in the feedback table
        """
        row = {
            "name": guess.capitalize(),
            "population": "25",
            "size": "like 2",
            "region": "Azerbaijan",
            "languages": "Evil French, Polish",
            "currencies": "Doubloons",
            "timezones": "UTC, PST, ETC",
        }
        feedback.add_row(row)

    @round_stats.game_ended.subscribe
    def display_results(won: bool):
        """
        Displays the game results pop-up
        """
        if won:
            text = "Congratulaions!"
        else:
            text = "Too bad!"

        with ui.dialog() as dialog, ui.card():
            ui.label(text)
            ui.label(f"Time: {str(round_stats.round_time).split('.')[0]}")
            ui.label(f"Guesses: {round_stats.guesses}")
            ui.button("Close", on_click=dialog.close)

            # TODO: Display leaderboard/player stats here?

            dialog.open()

    with ui.column(align_items="center").classes("mx-auto w-full max-w-md p-4"):
        timer = ui.label().mark("timer")
        ui.timer(
            1.0,
            lambda: timer.set_text(
                f"{str(datetime.now(timezone.utc) - round_stats.round_start).split('.')[0]}"
            ),
        )

        columns = [
            {"name": "name", "label": "Name", "field": "name"},
            {"name": "population", "label": "Population", "field": "population"},
            {"name": "size", "label": "Size", "field": "size"},
            {"name": "region", "label": "Region", "field": "region"},
            {"name": "languages", "label": "Languages", "field": "languages"},
            {"name": "currencies", "label": "Currencies", "field": "currencies"},
            {"name": "timezones", "label": "Timezones", "field": "timezones"},
        ]
        rows = []
        # TODO: Style table
        feedback = ui.table(
            rows=rows, columns=columns, column_defaults={"align": "center"}, row_key="name"
        )

        with ui.card(align_items="center"):
            guess_input = (
                ui.input(
                    label="Guess",
                    placeholder="Enter a country",
                    autocomplete=options,
                    validation=is_guess_valid,
                )
                .without_auto_validation()
                .on("keydown.enter", lambda: try_guess())
            )
            ui.button("Submit", on_click=lambda: try_guess())


# button to display leaderboards
"""
leaderboard

    - by default, display ~250 entries around the user
    - allow switch to friends-only or global leaderboard
    - allow jumping to top-ranked players
"""

# button to open account management menu
"""
account management

    - create account
    - see account stats
    - edit account info (username/password/email)
    - friends/friend requests
"""
