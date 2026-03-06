import asyncio
import json
from contextlib import asynccontextmanager

import aiomqtt
import httpx
from decouple import config
from fastapi import FastAPI

TOKEN_URL = "https://api.openf1.org/token"
mqtt_username = config("OPENF1_USERNAME")
mqtt_password = config("OPENF1_PASSWORD")

location_queue: asyncio.Queue = asyncio.Queue()
sessions_queue: asyncio.Queue = asyncio.Queue()
laps_queue: asyncio.Queue = asyncio.Queue()


async def get_access_token() -> tuple[str, int]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={"username": mqtt_username, "password": mqtt_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"], int(token_data["expires_in"])


async def mqtt_listener():
    while True:
        try:
            access_token, expires_in = await get_access_token()
            print(f"Token obtained, valid for {expires_in} seconds")

            # Reconnect a bit before the token actually expires
            refresh_at = expires_in - 60

            async with aiomqtt.Client(
                hostname="mqtt.openf1.org",
                port=8084,
                username=mqtt_username,
                password=access_token,
                transport="websockets",
                websocket_path="/mqtt",
                tls_params=aiomqtt.TLSParameters(),
            ) as client:
                async with client.messages() as messages:
                    await client.subscribe("v1/sessions")
                    await client.subscribe("v1/location")
                    await client.subscribe("v1/laps")

                    # Race between incoming messages and token expiry
                    refresh_task = asyncio.create_task(asyncio.sleep(refresh_at))

                    async for message in messages:
                        if message.topic.matches("v1/sessions"):
                            await sessions_queue.put(message.payload.decode())
                        elif message.topic.matches("v1/location"):
                            await location_queue.put(message.payload.decode())
                        elif message.topic.matches("v1/laps"):
                            await laps_queue.put(message.payload.decode())

                        print(
                            f"Topic: {message.topic} | Payload: {message.payload.decode()}"
                        )

                        if refresh_task.done():
                            print("Token expiring soon, reconnecting...")
                            break

        except httpx.HTTPError as e:
            print(f"Failed to obtain token: {e}, retrying in 10 seconds...")
            await asyncio.sleep(10)

        except aiomqtt.MqttError as e:
            print(f"MQTT connection error: {e}, retrying in 5 seconds...")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(mqtt_listener())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/location")
async def get_location():
    messages = []
    while not location_queue.empty():
        messages.append(json.loads(location_queue.get_nowait()))
    return messages


@app.get("/laps")
async def get_laps():
    messages = []
    while not laps_queue.empty():
        messages.append(json.loads(laps_queue.get_nowait()))
    return messages


@app.get("/sessions")
async def get_sessions():
    messages = []
    while not sessions_queue.empty():
        messages.append(json.loads(sessions_queue.get_nowait()))
    return messages
