from backend.application import socketio, application
from flask import render_template, url_for, redirect, request, session
from flask_socketio import emit, join_room
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_users_in_room = {} # stores room wise user list
_room_of_sid = {} # stores room joined by an used
_name_of_sid = {} # stores display name of users


@application.route("/interview/room/<string:room_id>/")
def enter_room(room_id):
    if room_id not in session:
        return redirect(url_for("entry_checkpoint", room_id=room_id))
    return render_template("interview_page.html", room_id=room_id, display_name=session[room_id]["name"], mute_audio=session[room_id]["mute_audio"], mute_video=session[room_id]["mute_video"])


@socketio.on("connect")
def on_connect():
    sid = request.sid
    logger.info("New socket connected ", sid)


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
    

@socketio.on("join-room")
def on_join_room(data):
    sid = request.sid
    room_id = data["room_id"]
    display_name = session[room_id]["name"]
    
    # register sid to the room
    join_room(room_id)
    _room_of_sid[sid] = room_id
    _name_of_sid[sid] = display_name
    
    # broadcast to others in the room
    logger.info("[{}] New member joined: {}<{}>".format(room_id, display_name, sid))
    emit("user-connect", {"sid": sid, "name": display_name}, broadcast=True, include_self=False, room=room_id)
    
    # add to user list maintained on server
    if room_id not in _users_in_room:
        _users_in_room[room_id] = [sid]
        emit("user-list", {"my_id": sid}) # send own id only
    else:
        usrlist = {u_id:_name_of_sid[u_id] for u_id in _users_in_room[room_id]}
        emit("user-list", {"list": usrlist, "my_id": sid}) # send list of existing users to the new member
        _users_in_room[room_id].append(sid) # add new member to user list maintained on server

    logger.info("\nusers: ", _users_in_room, "\n")


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    room_id = _room_of_sid[sid]
    display_name = _name_of_sid[sid]

    logger.info("[{}] Member left: {}<{}>".format(room_id, display_name, sid))
    emit("user-disconnect", {"sid": sid}, broadcast=True, include_self=False, room=room_id)

    _users_in_room[room_id].remove(sid)
    if len(_users_in_room[room_id]) == 0:
        _users_in_room.pop(room_id)

    _room_of_sid.pop(sid)
    _name_of_sid.pop(sid)

    logger.info("\nusers: ", _users_in_room, "\n")


@socketio.on("data")
def on_data(data):
    sender_sid = data["sender_id"]
    target_sid = data["target_id"]
    if sender_sid != request.sid:
        logger.critical("[Not supposed to happen!] request.sid and sender_id don't match!")

    if data["type"] != "new-ice-candidate":
        logger.info("{} message from {} to {}".format(data["type"], sender_sid, target_sid))
    emit("data", data, room=target_sid)
