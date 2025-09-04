from globals import *

import aiohttp
from socketio import AsyncClient
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration
import cv2
import time
from PIL import Image

# from ai.proctoring import Proctor
# proctor = Proctor()

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
        print(f"Received track: {track}")
        if track.kind == "video":
            # last_sent_time = 0
            # send_interval = 5

            while True:
                frame = await track.recv()
                # current_time = time.time()

                # if current_time - last_sent_time >= send_interval:
                #     img = frame.to_ndarray()
                #     img = cv2.cvtColor(img, cv2.COLOR_YUV2RGB_I420)
                #     proctor.analyze(Image.fromarray(img), 1)
                #     last_sent_time = current_time

                # Open video stream window
                img = frame.to_ndarray()
                img = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_I420)
                cv2.imshow(f"Video stream", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break


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

    async def candidate(self, data):
        data = data["candidate"]
        foundation, component, protocol, priority, ip, port  = data["candidate"][10:].split(' ')[:6] # Just forget about this abomination 
        await self.connection.addIceCandidate(RTCIceCandidate(
            ip=ip,
            port=port,
            protocol=protocol,
            priority=priority,
            foundation=foundation,
            component=component,
            type=priority,
            sdpMid=data["sdpMid"],
            sdpMLineIndex=data["sdpMLineIndex"]
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
        print(f"Received peer list: {data}")
        self.id = data["target_id"]
        if "peers" not in data.keys():
            raise NotImplementedError # Room is empty
        for peer_id in data["peers"].keys():
            self.peers[peer_id] = P2PConnection(self, peer_id)
            await self.peers[peer_id].offer()

    async def __on_data(self, data):
        peer = self.peers[data["sender_id"]]
        handlers = {
            "offer": peer.answer,
            "answer": peer.send_remote_description,
            "new-ice-candidate": peer.candidate
        }
        await handlers[data["type"]](data)

    @classmethod
    async def connect_to_socket(cls, name: str, interview_room: str) -> 'WebRTCClient':
        client = cls(name, interview_room)
        async with aiohttp.ClientSession() as session:
            uri = f"http://{HOST}:{PORT}/interview/{client.interview_room}/checkpoint/"
            async with session.post(
                    uri,
                    data={"display_name": client.name, "mute_audio": 1, "mute_video": 1},
                    allow_redirects=False
            ) as r:
                headers = {"Cookie": f"session={r.cookies['session'].value}"}
                socket_uri = f"http://{HOST}:{PORT}"
                await client.client.connect(socket_uri, headers=headers)
        return client

    async def send(self, event_name: str, message):
        await self.client.emit(event_name, message)
