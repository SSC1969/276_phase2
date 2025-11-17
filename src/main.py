from nicegui import ui

from game import game_ui


@ui.page("/")
def index_page():
    game_ui.content()


ui.run(title="CMPT276 Project", dark=None)
