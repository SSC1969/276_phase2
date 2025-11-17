from nicegui import ui
from nicegui.testing import User

pytest_plugins = ["nicegui.testing.user_plugin"]


async def test_layout(user: User) -> None:
    await user.open("/")

    await user.should_see(marker="timer")
    await user.should_see(ui.table)
    await user.should_see("Guess")
    await user.should_see("Submit")

    await user.should_not_see(ui.dialog)


async def test_typing(user: User) -> None:
    await user.open("/")

    user.find("Guess").type("asdf")
    await user.should_not_see("Not a valid country!")
    await user.should_not_see("Already guessed!")


async def test_invalid_country(user: User) -> None:
    await user.open("/")

    user.find("Guess").type("wrong")
    user.find("Submit").click()
    await user.should_see("Not a valid country!")


async def test_valid_entry(user: User) -> None:
    await user.open("/")

    guess = user.find("Guess")
    guess.type("Canada").trigger("keydown.enter")

    await user.should_see(ui.table)
    table = user.find(ui.table).elements.pop()
    print(table.rows[0]["name"])
    assert table.rows[0]["name"] == "Canada"


async def test_repeat_guess(user: User) -> None:
    await user.open("/")

    guess = user.find("Guess")
    guess.type("Canada").trigger("keydown.enter")

    guess.type("Canada").trigger("keydown.enter")
    await user.should_see("Already guessed!")


async def test_win_game(user: User) -> None:
    await user.open("/")

    guess = user.find("Guess")
    guess.type("Canada").trigger("keydown.enter")

    # TODO: Test that the game results display correctly for wins
    assert True


async def test_lose_game(user: User) -> None:
    await user.open("/")

    await user.should_see(ui.table)

    guesses = ["Canada", "Germany", "Ireland", "India", "China", "Japan"]
    guess = user.find("Guess")
    for i in range(6):
        guess.type(guesses[i]).trigger("keydown.enter")

    await user.should_see(ui.dialog)
    await user.should_see("Too bad!")
