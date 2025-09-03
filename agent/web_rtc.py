from globals import *

import aiohttp
from socketio import AsyncClient
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration


class P2PConnection:
    """
    Connection between AI agent and peer.
    """

    CONFIGURATION = RTCConfiguration(iceServers=[
        RTCIceServer(urls=[
            "stun:stun.l.google.com:19302",
            "stun:stun1.l.google.com:19302",
            "stun:stun2.l.google.com:19302",
            "stun:stun3.l.google.com:19302",
            "stun:stun4.l.google.com:19302"
        ])
    ])

    def __init__(self, client: 'WebRTCClient', peer_id: int, configuration: RTCConfiguration = None):
        self.client = client
        self.peer_id = peer_id

        self.connection = RTCPeerConnection(configuration=configuration or P2PConnection.CONFIGURATION)
        self.connection.addTransceiver("video", "recvonly")
        self.connection.on("track", P2PConnection.__on_track)

    @staticmethod
    async def __on_track(track):
        while True:
            await track.recv()

    async def send_remote_description(self, message):
        await self.connection.setRemoteDescription(
            RTCSessionDescription(sdp=message["sdp"]["sdp"], type=message["sdp"]["type"])
        )

    async def offer(self):
        offer = await self.connection.createOffer()
        await self.connection.setLocalDescription(offer)
        await self.client.send("data", {
            "sender_id": self.client.id,
            "target_id": self.peer_id,
            "type": "offer",
            "sdp": {
                "type": offer.type,
                "sdp": offer.sdp
            }
        })

    async def answer(self, offer):
        await self.send_remote_description(offer)  # TODO: if this is not needed, this function is the same as `offer`

        answer = await self.connection.createAnswer()
        await self.connection.setLocalDescription(answer)
        await self.client.send("data", {
            "sender_id": self.client.id,
            "target_id": self.peer_id,
            "type": "answer",
            "sdp": {
                "type": answer.type,
                "sdp": answer.sdp
            }
        })

    async def candidate(self, candidate):
        foundation, component, _, priority, _, ip, port, protocol = candidate["candidate"].split(' ')
        await self.connection.addIceCandidate(RTCIceCandidate(
            ip=ip,
            port=port,
            protocol=protocol,
            priority=priority,
            foundation=foundation,
            component=component,
            type=priority,
            sdpMid=candidate["sdpMid"],
            sdpMLineIndex=candidate["sdpMLineIndex"]
        ))


class WebRTCClient:
    """
    AI agent that is based on WebRTC client bot.
    """

    def __init__(self, name: str, interview_room: int):
        self.id = None  # TODO: initialization of `id` is deferred until `peer_list` is called which seems stupid
        self.client = AsyncClient()
        self.client.on("connect", self.__on_connect)
        self.client.on("peer_list", self.__on_peer_list)
        self.client.on("data", self.__on_data)

        self.name = name
        self.interview_room = interview_room

        self.peers: dict[int, P2PConnection] = dict()

    async def __on_connect(self):
        await self.send("join_room", {"interview_room": self.interview_room})

    async def __on_peer_list(self, data):
        self.id = data["id"]
        for peer_id in data["peers"].keys():
            self.peers[peer_id] = P2PConnection(self, peer_id)

    async def __on_data(self, data):
        peer = self.peers[data["sender_id"]]
        handlers = {
            "offer": peer.answer,
            "answer": peer.send_remote_description,
            "new-ice-candidate": peer.candidate
        }
        handlers[data["type"]](data)

    @classmethod
    async def connect_to_socket(cls, name: str, interview_room: int) -> 'WebRTCClient':
        client = cls(name, interview_room)
        async with aiohttp.ClientSession() as session:
            uri = f"ws://{HOST}:{PORT}/interview/{client.interview_room}/checkpoint/"
            async with session.post(
                    uri,
                    data={"display_name": client.name, "mute_audio": 1, "mute_video": 1},
                    allow_redirects=False
            ) as r:
                headers = {"Cookie": f"session={r.cookies['session'].value}"}
                await client.client.connect(uri, headers=headers)
        return client

    async def send(self, event_name: str, message):
        await self.client.emit(event_name, message)
