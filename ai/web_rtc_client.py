import asyncio
import sys
import json
import cv2
import aiohttp
import socketio
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration


class WebRTCClient:
    def __init__(self, name, room_id, uri):
        self.name = name
        self.room_id = room_id
        self.uri = uri
        ice_servers = [
            RTCIceServer(urls=[
            'stun:stun.l.google.com:19302',
            'stun:stun1.l.google.com:19302',
            'stun:stun2.l.google.com:19302',
            'stun:stun3.l.google.com:19302',
            'stun:stun4.l.google.com:19302'
        ])  # Google's public STUN server
        ]
        self.PC_CONFIG = RTCConfiguration(iceServers=ice_servers)
        self.ice_candidates = []
        self.peers = dict()

        self.frame_queue = asyncio.Queue()  # Add a queue for frames

    async def create_peer_connection(self, peer_id):
        # print("creating peer connection for:", peer_id)
        pc = RTCPeerConnection(configuration=self.PC_CONFIG)
        pc.addTransceiver("video", "recvonly")

        @pc.on("track")
        async def on_track(track):
            print('TRACK RECEIVED', track)
            print('TRACK KIND', track.kind)
            frame = await track.recv()

            while True:
                try:
                    frame = await track.recv()
                    # Convert the frame to OpenCV format
                    img = frame.to_ndarray(format="bgr24")
                    
                    # Put the frame in the queue for processing
                    await self.frame_queue.put((peer_id, img))
                    
                    # Optional: Display the frame (for debugging)
                    cv2.imshow(f"Video from {peer_id}", img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
                except Exception as e:
                    print(f"Error receiving frame: {e}")
                    break


        @pc.on("signalingstatechange")
        async def on_signalingstatechange():
            print('Signaling state change:', pc.signalingState)
            if pc.signalingState == 'stable':
                print('ICE gathering complete')
                # Log all gathered candidates
                for candidate in self.ice_candidates:
                    print('Gathered candidate:', candidate)

        @pc.on('negotiationneeded')
        async def on_negotiation_needed(peer_id):
            print('Need negotiation with', peer_id)
            await self.create_offer(peer_id)

        @pc.on('iceconnectionstatechange')
        async def on_iceconnectionstatechange():
            print("ICE connection state is", pc.iceConnectionState)
            if pc.iceConnectionState == "failed":
                print("ICE Connection has failed, attempting to restart ICE")
                await pc.restartIce()

        @pc.on('connectionstatechange')
        async def on_connectionstatechange():
            print('Connection state change:', pc.connectionState)
            if pc.connectionState == 'connected':
                print('Peers successfully connected')


        @pc.on('icegatheringstatechange')
        async def on_icegatheringstatechange():
            print('ICE gathering state changed to', pc.iceGatheringState)
            if pc.iceGatheringState == 'complete':
                print('All ICE candidates have been gathered.')
                # Log all gathered candidates
                for candidate in self.ice_candidates:
                    print('Gathered candidate:', candidate)

        self.peers[peer_id] = pc

        print("events for current peer are added")

    async def invite(self, peer_id):
        print("Inviting:", peer_id)
        if(self.peers[peer_id]):
            return
        print(peer_id, "is not connected to")
        await self.create_peer_connection(peer_id)
        await self.create_offer(self.peers[peer_id], peer_id)

    async def start_webrtc(self):
        print("current peers:", self.peers)
        for peer_id in self.peers.keys():
            await self.invite(peer_id)

    async def connect_to_socketio(self):
        self.sio = socketio.AsyncClient()

        async with aiohttp.ClientSession() as session:
            data = {"display_name": self.name, "mute_audio": 1, "mute_video": 1}
            uri = f"{self.uri}/room/{self.room_id}/checkpoint/"
            async with session.post(uri, data=data, allow_redirects=False) as r:
                sid = r.cookies["session"].value
                print("Session id:", sid)

        @self.sio.on("connect")
        async def on_connect():
            print("Connected, sending join-room request")
            await self.sio.emit("join-room", {
                "room_id": self.room_id,
            })


        @self.sio.on("user-connect")
        async def on_user_connect(data):
            print("A user has connected! Data provided:", data)
            # self.peers[data["sid"]] = None
            # await self.create_peer_connection(data["sid"])

        @self.sio.on("user-list")
        async def on_user_list(data):
            print("Received user list:", data)
            self.my_id = data["my_id"]
            for peer_id in data["list"].keys():
                self.peers[peer_id] = None
            await self.start_webrtc()

        @self.sio.on("data")
        async def on_data(data):
            # print("on_data:", data)
            match data["type"]:
                case "offer":
                    await self.handle_offer(data)
                case "answer":
                    await self.handle_answer(data)
                case "new-ice-candidate":
                    await self.handle_candidate(data["sender_id"], data["candidate"])
        
        headers = {"Cookie": f"session={sid}"}
        print(f"Connecting to the signaling server at {self.uri} with headers {headers}...")
        await self.sio.connect(self.uri, headers=headers)
        print("Done!")

    async def create_offer(self, pc, target_id):
        print("creating offer for:", target_id)
        pc.addTransceiver("video", "recvonly")
        offer = await pc.createOffer()
        print("Offer created")
        await pc.setLocalDescription(offer)
        await self.send_message({
            "sender_id": self.my_id,
            "target_id": target_id,
            "type": "offer",
            "sdp": {
                "type": offer.type,
                "sdp": offer.sdp
            }
        })

    async def handle_offer(self, offer):
        sender_id = offer["sender_id"]
        try:
            pc = self.peers[sender_id]
        except:
            await self.create_peer_connection(sender_id)
            pc = self.peers[sender_id]

        print("Handling offer for", pc, sender_id)
        # await pc.setRemoteDescription(RTCSessionDescription(sdp=str(offer["sdp"]), type=offer["type"]))
        print("Offer type", type(offer))
        print("Offer contents:", offer)
        await pc.setRemoteDescription(RTCSessionDescription(sdp=offer["sdp"]["sdp"], type=offer["sdp"]["type"]))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        # await self.send_message({'event': 'answer', 'data': {'type': answer.type, 'sdp': answer.sdp}})
        await self.send_message({
            "sender_id": self.my_id,
            "target_id": sender_id,
            "type": "answer",
            "sdp": {
                "type": answer.type,
                "sdp": answer.sdp
            }
        })

    async def handle_candidate(self, sender_id, candidate):
        # print('Received ICE candidate:', candidate)
        pc = self.peers[sender_id]
        # print("Current pc is:", pc)
        ip = candidate['candidate'].split(' ')[4]
        port = candidate['candidate'].split(' ')[5]
        protocol = candidate['candidate'].split(' ')[7]
        priority = candidate['candidate'].split(' ')[3]
        foundation = candidate['candidate'].split(' ')[0]
        component = candidate['candidate'].split(' ')[1]
        type = candidate['candidate'].split(' ')[7]
        rtc_candidate = RTCIceCandidate(
            ip=ip,
            port=port,
            protocol=protocol,
            priority=priority,
            foundation=foundation,
            component=component,
            type=type,
            sdpMid=candidate['sdpMid'],
            sdpMLineIndex=candidate['sdpMLineIndex']
        )
        # print("Composed candidate:", rtc_candidate)
        await pc.addIceCandidate(rtc_candidate)
        self.ice_candidates.append(rtc_candidate)

    async def handle_answer(self, answer):
        sender_id = answer["sender_id"]
        pc = self.peers[sender_id]
        # await pc.setRemoteDescription(RTCSessionDescription(sdp=answer['sdp'], type=answer['type']))
        await pc.setRemoteDescription(RTCSessionDescription(sdp=answer["sdp"]["sdp"], type=answer["sdp"]["type"]))

    async def send_message(self, message):
        await self.sio.emit("data", message)

    async def close(self):
        await self.sio.close()

async def main():
    client = WebRTCClient(name="python-client", room_id="test-room", uri="ws://127.0.0.1:5000")
    await client.connect_to_socketio()
    # await client.create_offer()  # Create an offer after connecting to the websocket
    while True:
        await asyncio.sleep(1)  # Keep the session alive for debugging
    # await client.close()

if __name__ == '__main__':
    asyncio.run(main())
