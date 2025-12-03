import io
import time
from pathlib import Path

import bcrypt
from nicegui import APIRouter, app, events, ui
from PIL import Image, ImageOps

from game import repos

DEFAULT_AVATAR = Path("avatars/default.jpg")
AVATAR_DIR = Path("avatars")
AVATAR_DIR.mkdir(exist_ok=True)
app.add_static_files("/avatars", str(AVATAR_DIR))

MAX_AVATAR_SIZE = (256, 256)

TEST = False

SESSION_STORAGE_NAME = "user_session"

router = APIRouter(prefix="/account")


async def local_authenticate(user_repo, username: str, password: str):
    """
    Authenticate a user using LocalUserRepo.
    Returns the LocalUser object if valid, otherwise None.
    """
    user = await user_repo.get_by_name(username)
    if not user:
        return None

    if bcrypt.checkpw(password.encode(), user.password.encode()):
        return user

    return None


async def save_avatar(file_path: Path, uploaded_file):
    content = await uploaded_file.read()

    with Image.open(io.BytesIO(content)) as img:
        img = img.convert("RGB")
        img = ImageOps.fit(img, MAX_AVATAR_SIZE, Image.Resampling.LANCZOS)
        img.save(file_path, format="JPEG", quality=85)


def avatar_static_url(path: Path) -> str:
    """Converts path to string"""
    filename = path.name
    return f"/avatars/{filename}?t={int(time.time())}"


def get_avatar_path(user_id: int) -> Path:
    """Return the user's avatar path or default path if user has no avatar"""
    avatar_path = AVATAR_DIR / f"{user_id}.jpg"
    return avatar_path if avatar_path.exists() else DEFAULT_AVATAR


""" ACCOUNT UI """


async def ensure_authenticated():
    auth_repo = repos["auth_repo"]
    if TEST:
        return True

    user = app.storage.user.get(SESSION_STORAGE_NAME + "_user", False)
    token = app.storage.user.get(SESSION_STORAGE_NAME + "_token", False)

    if not user or not token:
        ui.navigate.to("/account/login")
        return False

    valid = await auth_repo.validate(token)
    if not valid:
        app.storage.user.pop(SESSION_STORAGE_NAME + "_user")
        app.storage.user.pop(SESSION_STORAGE_NAME + "_token")
        ui.navigate.to("/account/login")
        return False

    return True


""" LOGIN PAGE """


@router.page("/login")
def login_page():
    user_repo = repos["user_repo"]
    auth_repo = repos["auth_repo"]

    with ui.card().classes("absolute-center w-96 p-6 gap-3"):
        ui.label("Login").classes("text-2xl font-bold mb-2")

        username = ui.input("Username")
        password = ui.input("Password", password=True)

        async def try_login():
            user = await local_authenticate(user_repo, username.value, password.value)
            if not user:
                ui.notify("Invalid credentials", color="red")
                return

            token = await auth_repo.create(user.id)
            app.storage.user[SESSION_STORAGE_NAME + "_user"] = user.id
            app.storage.user[SESSION_STORAGE_NAME + "_token"] = token
            ui.navigate.to("/account")

        ui.button("Login", on_click=try_login).classes("w-full")
        ui.button("Create Account", on_click=lambda: ui.navigate.to("/account/register")).classes(
            "w-full mt-2"
        )
        ui.button("Back to Game", on_click=lambda: ui.navigate.to("/")).classes("w-full mt-4")


""" REGISTER PAGE """


@router.page("/register")
def register_page():
    with ui.card().classes("absolute-center w-96 p-6 gap-3"):
        ui.label("Create Account").classes("text-2xl font-bold mb-2")

        user_repo = repos["user_repo"]
        auth_repo = repos["auth_repo"]

        username = ui.input("Username")
        email = ui.input("Email")
        password = ui.input("Password", password=True)

        async def try_create():
            new_user = await user_repo.create(username.value, email.value, password.value)
            if not new_user:
                ui.notify("Username or email already exists", color="red")
                return

            token = await auth_repo.create(new_user.id)
            app.storage.user[SESSION_STORAGE_NAME + "_user"] = new_user.id
            app.storage.user[SESSION_STORAGE_NAME + "_token"] = token
            ui.navigate.to("/account")

        ui.button("Register", on_click=try_create).classes("w-full")
        ui.button("Back", on_click=lambda: ui.navigate.to("/account/login")).classes("w-full mt-2")


""" 
ACCOUNT DASHBOARD 

shows profile, friends, statistics
"""


@router.page("/")
async def dashboard_page():
    if not await ensure_authenticated():
        return

    user_id = app.storage.user.get(SESSION_STORAGE_NAME + "_user")

    user_repo = repos["user_repo"]
    auth_repo = repos["auth_repo"]

    user = await user_repo.get_by_id(user_id)

    async def logout():
        if user:
            await auth_repo.delete(user.id)

        app.storage.user.pop(SESSION_STORAGE_NAME + "_user")
        app.storage.user.pop(SESSION_STORAGE_NAME + "_token")

        ui.navigate.to("/login")

    avatar_path = get_avatar_path(user.id)

    with ui.row().classes("absolute-center gap-10"):
        with ui.card().classes("w-80 p-4 gap-2"):
            ui.label(f"Welcome, {user.name}!").classes("text-xl font-bold mb-3")
            ui.image(avatar_static_url(avatar_path)).classes("w-32 h-32 rounded-full mx-auto")

            ui.button(
                "Profile / Avatar", on_click=lambda: ui.navigate.to("/account/profile")
            ).classes("w-full")
            ui.button("Friends", on_click=lambda: ui.navigate.to("/account/friends")).classes(
                "w-full"
            )
            ui.button("Statistics", on_click=lambda: ui.navigate.to("/account/stats")).classes(
                "w-full"
            )
            ui.button("Logout", on_click=logout).classes("w-full mt-2")
            ui.button("Back to Game", on_click=lambda: ui.navigate.to("/")).classes("w-full mt-2")


""" 
PROFILE PAGE 

edit name, email, password, avatar
"""


@router.page("/profile")
async def profile_page():
    if not await ensure_authenticated():
        return

    user_id = app.storage.user.get(SESSION_STORAGE_NAME + "_user")
    user_repo = repos["user_repo"]

    user = await user_repo.get_by_id(user_id)

    with ui.card().classes("absolute-center w-96 p-5 gap-4"):
        ui.label("Edit Profile").classes("text-2xl font-bold text-center")

        avatar_component = ui.image(avatar_static_url(get_avatar_path(user.id))).classes(
            "w-32 h-32 rounded-full mx-auto"
        )

        name_input = ui.input("Display Name", value=user.name)
        email_input = ui.input("Email", value=user.email)
        pw_input = ui.input("New Password (optional)", password=True)

        async def save_profile():
            await user_repo.update_user(
                user.id,
                name=name_input.value,
                email=email_input.value,
                new_password=pw_input.value or None,
            )

            user.name = name_input.value
            user.email = email_input.value

            ui.notify("Profile updated!", color="green")
            ui.navigate.to("/account")

        ui.label("Upload New Avatar:")

        async def handle_upload(e: events.UploadEventArguments):
            avatar_path = get_avatar_path(user.id)
            content = await e.file.read()

            with Image.open(io.BytesIO(content)) as img:
                img = img.convert("RGB")
                img = ImageOps.fit(img, MAX_AVATAR_SIZE, Image.Resampling.LANCZOS)
                img.save(avatar_path, format="JPEG", quality=85)

            avatar_component.set_source(avatar_static_url(avatar_path))
            avatar_component.update()

            ui.notify("Avatar updated!", color="green")

        ui.upload(on_upload=handle_upload, label="Upload Avatar").classes("w-full")

        ui.button("Save Profile", on_click=save_profile).classes("w-full mt-2")
        ui.button("Back", on_click=lambda: ui.navigate.to("/account")).classes("w-full mt-2")
        ui.button("Back to Game", on_click=lambda: ui.navigate.to("/")).classes("w-full")


""" 
FRIEND PAGE

view friend requests, view friends, send requests  
"""


@router.page("/friends")
async def friends_page():
    if not await ensure_authenticated():
        return

    user_id = app.storage.user.get(SESSION_STORAGE_NAME + "_user")
    user_repo = repos["user_repo"]
    friends_repo = repos["friendship_repo"]

    user = await user_repo.get_by_id(user_id)

    with ui.card().classes("absolute-center w-96 p-6 gap-4"):
        ui.label("Friends").classes("text-2xl font-bold text-center")

        ui.label("Add Friend:")
        friend_name_input = ui.input("Friend username")

        async def send_request():
            target = await user_repo.get_by_name(friend_name_input.value)
            if not target:
                ui.notify("User not found.", color="red")
                return

            ok = await friends_repo.send_request(user.id, target.id)
            if ok:
                ui.notify("Friend request sent!", color="green")
            else:
                ui.notify("User not found or already friends.", color="red")

        ui.button("Send Request", on_click=send_request).classes("w-full")

        ui.label("Incoming Requests:").classes("mt-4 font-bold")

        requests = await friends_repo.get_requests(user.id)
        if not requests:
            ui.label("No pending requests.")

        for req in requests:
            requestor = await user_repo.get_by_id(req.requestor_id)
            with ui.row().classes("w-full justify-between"):
                ui.label(requestor.name)
                with ui.row():
                    ui.button("Accept", on_click=lambda r=req: friends_repo.accept_request(r.id))
                    ui.button("Reject", on_click=lambda r=req: friends_repo.reject_request(r.id))

        ui.label("Your Friends:").classes("mt-4 font-bold")

        friends = await friends_repo.list_friends(user.id)
        if not friends:
            ui.label("You have no friends yet.")
        else:
            for fr in friends:
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label(fr.name)
                    ui.button(
                        "Remove",
                        on_click=lambda: friends_repo.delete_friendship(user.id, fr.id),
                        color="red",
                    )

        ui.button("Back", on_click=lambda: ui.navigate.to("/account")).classes("w-full mt-4")
        ui.button("Back to Game", on_click=lambda: ui.navigate.to("/")).classes("w-full")


"""
STATISTICS PAGE

show user statistics
"""


@router.page("/stats")
async def stats_page():
    if not await ensure_authenticated():
        return

    stats_repo = repos["stats_repo"]
    user_repo = repos["user_repo"]

    user_id = app.storage.user.get(SESSION_STORAGE_NAME + "_user")

    user = await user_repo.get_by_id(user_id)

    stats = stats_repo.get_leaderboard_stats_for_user(user.id)

    with ui.card().classes("absolute-center w-128 p-6 gap-4"):
        ui.label("Your Statistics").classes("text-3xl font-bold mb-4 text-center")

        if not stats:
            ui.label("You have no game statistics yet.").classes("text-lg")
        else:
            ui.label(f"Daily Streak: {stats.daily_streak}").classes("text-lg")
            ui.label(f"Longest Daily Streak: {stats.longest_daily_streak}").classes("text-lg")
            ui.label(f"Average Daily Guesses: {stats.average_daily_guesses:.2f}").classes("text-lg")
            ui.label(f"Average Daily Time: {stats.average_daily_time}").classes("text-lg")
            ui.label(f"Longest Survival Streak: {stats.longest_survival_streak}").classes("text-lg")

            ui.separator()
            ui.label(f"Overall Score: {stats.score}").classes("text-xl font-bold")

        ui.button("Back", on_click=lambda: ui.navigate.to("/account")).classes("w-full mt-4")
        ui.button("Back to Game", on_click=lambda: ui.navigate.to("/")).classes("w-full")
