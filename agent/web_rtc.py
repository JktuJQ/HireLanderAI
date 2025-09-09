from globals import *

import aiohttp
from socketio import AsyncClient
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer
from aiortc.mediastreams import MediaStreamError
import cv2
import av
from ai.interviewer import STTProcessor, Interviewer
from ai.proctoring import Proctor
from PIL import Image
import asyncio
import logging
import os
import threading
import time

logging.getLogger('aioice.ice').setLevel(logging.ERROR)

proctor = Proctor()
interviewer = Interviewer()
q = ["""критерий: высшее техническое или экономическое образование\n тип: education\n сложность: easy\n follow_ups: ["какие курсы или сертификаты вы получали во время учебы?", "как ваше образование связано с работой бизнес аналитика?"]"""]

STOP_WORD = "закончить ответ"

class AudioEchoTrack(MediaStreamTrack):
    """
    A media stream track that echoes back audio.
    """
    kind = "audio"

    def __init__(self, track):
        super().__init__()
        self.track = track
        self.resampler = av.AudioResampler(format="s16", layout="mono", rate=16_000)
        self.recorder = STTProcessor()
        self.response_frames = asyncio.Queue()

        self.user_answer = ""
        
        self.player = None
        self.output_ready = False
        self.current_pts = 0
        self.add_pts = 0
        self.setup()


    def setup(self):
        silent_frame = av.AudioFrame(format="s16", layout="stereo", samples=160)
        for p in silent_frame.planes: # Remove random date, so there are no glitches
            p.update(bytes(p.buffer_size))
        silent_frame.pts = 0
        silent_frame.sample_rate = 48_000
        self.silent_frame = silent_frame

        self.answer_event = threading.Event()
        self.interview_thread = threading.Thread(target=self.__run_interview, kwargs={"q": q, "answer_event": self.answer_event}, daemon=True)

        self.question_generated_event = threading.Event()
        self.reponse_generated = False
        
        self.interview_thread.start()

    def __run_interview(self, q, answer_event):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(interviewer.hold_interview(q, answer_event))
        finally:
            loop.close()

    async def recv(self):
        if not interviewer.curr_question:
            return self.silent_frame

        if not self.reponse_generated:
            interviewer.text_to_speech_online(interviewer.curr_question)           
            self.player = MediaPlayer("agent/audio/output.mp3", format="mp3", loop=False).audio
            self.output_ready = True
            self.reponse_generated = True

        try:
            frame = await self.track.recv()
        except MediaStreamError:
            return self.silent_frame

        resampled = self.resampler.resample(frame)[0]
        audio_data = resampled.to_ndarray().tobytes()
        self.recorder.feed_audio(audio_data)

        if self.recorder.transcribed:
            self.user_answer += self.recorder.text.lower() + " "
            print(self.user_answer)
            self.recorder.transcribed = False

        if STOP_WORD in self.user_answer:
            interviewer.curr_answer = self.user_answer
            self.answer_event.set()
            
            self.user_answer = ""
            self.reponse_generated = False
            print("STOP WORD")

        if self.output_ready:
            try:
                res = await asyncio.wait_for(self.player.recv(), timeout=0.5)
                res.pts += self.add_pts
                self.current_pts = res.pts
                return res
            except (MediaStreamError, asyncio.TimeoutError):
                os.remove("agent/audio/output.mp3")
                self.output_ready = False
                self.add_pts = self.current_pts # TODO: Decide if there should be accumulation or assignment

        return self.silent_frame


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
        import os
        dir_path = os.path.dirname(os.path.realpath(__file__))
        print("pwd:", dir_path)
        self.client = client
        self.peer_id = peer_id
        self.pending_ice_candidates = []

        self.connection = RTCPeerConnection(configuration=configuration or P2PConnection.CONFIGURATION)
        self.connection.addTransceiver("video", "recvonly")
        self.connection.addTransceiver("audio", "sendrecv")
        self.connection.on("track", self.__on_track)

    async def __on_track(self, track):
        print(f"Received track: {track}")
        if track.kind == "video":
            last_sent_time = 0
            send_interval = 5

            while True:
                frame = await track.recv()
                await asyncio.sleep(time.time() - last_sent_time + 1)
                current_time = time.time()
                if current_time - last_sent_time >= send_interval:
                    img = frame.to_ndarray()
                    img = cv2.cvtColor(img, cv2.COLOR_YUV2RGB_I420)
                    proctor.analyze(Image.fromarray(img), None)
                    last_sent_time = current_time

                # Open video stream window
                # img = frame.to_ndarray()
                # img = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_I420)
                # cv2.imshow(f"Video stream", img)
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
        if track.kind == "audio":
            echo_track = AudioEchoTrack(track)
            self.connection.addTrack(echo_track)
            echo_track.recorder.start_processing()

    async def set_remote_description(self, message):
        await self.connection.setRemoteDescription(
            RTCSessionDescription(sdp=message["sdp"]["sdp"], type=message["sdp"]["type"])
        )

        for candidate in self.pending_ice_candidates:
            await self.connection.addIceCandidate(candidate)
        self.pending_ice_candidates = []

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
        await self.set_remote_description(offer)  

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
        foundation, component, protocol, priority, ip, port, _, type  = data["candidate"][10:].split(' ')[:8] # Just forget about this abomination 
        candidate = RTCIceCandidate(
            ip=ip,
            port=int(port),
            protocol=protocol,
            priority=int(priority),
            foundation=int(foundation),
            component=int(component),
            type=type,
            sdpMid=data["sdpMid"],
            sdpMLineIndex=data["sdpMLineIndex"]
        )

        if self.connection.remoteDescription:
            await self.connection.addIceCandidate(candidate)
        else:
            self.pending_ice_candidates.append(candidate)


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
        if "peers" not in data.keys(): # Room is empty
            return
        for peer_id in data["peers"].keys():
            self.peers[peer_id] = P2PConnection(self, peer_id)
            await self.peers[peer_id].offer()

    async def __on_data(self, data):
        sender_id = data["sender_id"]
        if sender_id not in self.peers.keys(): # New peer might send offer before it's in self.peers
            self.peers[sender_id] = P2PConnection(self, sender_id)
        peer = self.peers[sender_id]
            
        handlers = {
            "offer": peer.answer,
            "answer": peer.set_remote_description,
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
