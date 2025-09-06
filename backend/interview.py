from backend.application import socketio, application
from flask import render_template, url_for, redirect, request, session
from flask_socketio import emit, join_room
import logging
import threading
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_users_in_room = {} # stores room wise user list
_room_of_sid = {} # stores room joined by an used
_name_of_sid = {} # stores display name of users


@application.route("/interview/<string:interview_room>/", methods=["GET"])
async def interview_route(interview_room: str):
    if interview_room not in session:
        return redirect(url_for("checkpoint_route", interview_room=interview_room))
    return render_template("interview.html", interview_room=interview_room, display_name=session[interview_room]["name"], mute_audio=session[interview_room]["mute_audio"], mute_video=session[interview_room]["mute_video"])


@socketio.on("connect")
def on_connect():
    sid = request.sid
    logger.info(f"New socket connected with sid: {sid}")


@socketio.on("coding_field_update")
def coding_field_update(data):
    """Socket IO handler for live coding session."""
    
    logger.critical("Coding field update should be tied to certain room!")
    emit(
        "coding_field_update",
        {"code": data["code"]},
        broadcast=True,
        include_self=False
    )
    

def run_agent_async(interview_room):
    def agent_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from agent.application import run
            logger.info(f"Starting agent in room: {interview_room}")
            loop.run_until_complete(run())
        except Exception as e:
            logger.error(f"Error running agent: {e}")
        finally:
            loop.close()
    
    thread = threading.Thread(target=agent_thread, daemon=True)
    thread.start()
    logger.info(f"Agent thread started for room: {interview_room}")


@socketio.on("join_room")
def on_join_room(data):
    sid = request.sid
    interview_room = data["interview_room"]
    display_name = session[interview_room]["name"]
    
    # register sid to the room
    join_room(interview_room)
    _room_of_sid[sid] = interview_room
    _name_of_sid[sid] = display_name
    
    # broadcast to others in the room
    logger.info("[{}] New member joined: {}<{}>".format(interview_room, display_name, sid))
    emit("peer_connect", {"sid": sid, "name": display_name}, broadcast=True, include_self=False, room=interview_room)
    
    # add to user list maintained on server
    if interview_room not in _users_in_room:
        _users_in_room[interview_room] = [sid]
        emit("peer_list", {"target_id": sid}) # send own id only  TODO: `peer_list` event will try to reach for `peers`
        
        logger.info("Someone entered empty room. Running agent")
        run_agent_async(interview_room)

    else:
        usrlist = {u_id:_name_of_sid[u_id] for u_id in _users_in_room[interview_room]}
        emit("peer_list", {"peers": usrlist, "target_id": sid}) # send list of existing users to the new member
        _users_in_room[interview_room].append(sid) # add new member to user list maintained on server

    logger.info(f"\nusers: {_users_in_room}\n")


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    interview_room = _room_of_sid[sid]
    display_name = _name_of_sid[sid]

    logger.info("[{}] Member left: {}<{}>".format(interview_room, display_name, sid))
    emit("peer_disconnect", {"sid": sid}, broadcast=True, include_self=False, room=interview_room)

    _users_in_room[interview_room].remove(sid)
    if len(_users_in_room[interview_room]) == 0:
        _users_in_room.pop(interview_room)

    _room_of_sid.pop(sid)
    _name_of_sid.pop(sid)

    logger.info(f"\nusers: {_users_in_room}\n")


@socketio.on("data")
def on_data(data):
    sender_sid = data["sender_id"]
    target_sid = data["target_id"]
    if sender_sid != request.sid:
        logger.critical("[Not supposed to happen!] request.sid and sender_id don't match!")

    if data["type"] != "new-ice-candidate":
        logger.info("{} message from {} to {}".format(data["type"], sender_sid, target_sid))
    emit("data", data, room=target_sid)  # TODO: `interview_room` as `target_sid`???????
