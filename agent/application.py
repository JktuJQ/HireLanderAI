from agent.web_rtc import WebRTCClient
from asyncio import sleep


async def run(name: str = "Agent", interview_room: str = "test-room"):
    """Runs AI agent on the backend socket."""

    client = await WebRTCClient.connect_to_socket(name, interview_room)
    # await client.create_offer()
    while True:
        await sleep(1)
    # await client.close()
