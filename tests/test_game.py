from nicegui.testing import User


async def test_layout(user: User):
    await user.open("/")

    await user.should_see("Guess")
    await user.should_see("Submit")


async def test_typing(user: User):
    await user.open("/")

    user.find("Guess").type("asdf")
    await user.should_not_see("Not a valid country!")


async def test_invalid_entry(user: User):
    await user.open("/")

    user.find("Guess").type("wrong")
    user.find("Submit").click()
    await user.should_see("Not a valid country!")


async def test_valid_entry(user: User):
    await user.open("/")

    user.find("Guess").type("Canada")
    user.find("Submit").click()
    await user.should_not_see("Not a valid country!")

    # TODO: Test that the guess feedback is displayed on the screen


# TODO: Test that the game results display correctly for both wins and losses
async def test_win_game(user: User):
    assert False


async def test_lose_game(user: User):
    assert False
