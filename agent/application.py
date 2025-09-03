from web_rtc import WebRTCClient
from asyncio import sleep


async def run():
    client = WebRTCClient(name="python-client", room_id="test-room", uri="ws://127.0.0.1:5000")
    await client.connect_to_socketio()
    # await client.create_offer()
    while True:
        await sleep(1)
    # await client.close()
