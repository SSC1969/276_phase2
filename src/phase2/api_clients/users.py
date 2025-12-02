import httpx 

class UserAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.client = httpx.AsyncClient(base_url=base_url)

    async def create(self, name: str, email: str, password: str):
        payload = {
            "name": name,
            "email": email,
            "password": password
        }

        r = await self.client.post("/v2/users/", json=payload)
        return r

    # GET USER BY NAME
    async def get_by_name(self, username: str):
        async with httpx.AsyncClient() as client:           # create async client
            r = await client.get(f"{self.base}/v2/users/name/{username}")  # call endpoint
            if r.status_code == 404:                        # if user not found
                return None                                 # return None for UI
            return r.json()["user"]                         # return user dict

    # GET USER BY ID
    async def get_by_id(self, user_id: int):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base}/v2/users/id/{user_id}")     # call endpoint
            if r.status_code == 404:
                return None
            return r.json()["user"]


