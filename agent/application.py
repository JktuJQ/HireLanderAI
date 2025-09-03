from agent.web_rtc import WebRTCClient
from asyncio import sleep


async def run():
    """Runs AI agent on the backend socket."""

    client = await WebRTCClient.connect_to_socket("AI Agent", 0)
    # await client.create_offer()
    while True:
        await sleep(1)
    # await client.close()
