from flask import request, Flask
from flask_socketio import SocketIO, emit, disconnect
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # allow cross-origin for testing


#-----------------------------------------------------------
# Keep track of online users
#-----------------------------------------------------------

online_users = {}

@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}") # logging

@socketio.on("login")
def handle_login(data):
    username = data["username"]
    password = data["password"]
    
    response = users_col.find_one({"username": username})
    if not response:
        emit("login", {"status": "error", "message": "User not found"})
        print(f"{request.sid}",username,"User not found") # logging
        return
    
    if response["password"] != password:
        emit("login", {"status": "error", "message": "Incorrect password"})
        print(f"{request.sid}",username,"incorrect password") # logging
        return
    
    online_users[username] = request.sid
    response["_id"] = str(response["_id"])
    del response["password"]  # Do not send password back
    response["online_friends"] = []
    
    # Notify online friends that this user is online
    for friend in response.get("friends", []):
        if friend in online_users:
            emit("user_online", {"username": username}, room=online_users.get(friend))
            response["online_friends"].append(friend)
    
    emit("login", {"status": "ok", "user": response})
    print(f"{username} logged in.") # logging

@socketio.on("disconnect")
def handle_disconnect():
    for username, sid in list(online_users.items()):
        if sid == request.sid:
            online_users.pop(username)
            # Notify online friends that this user is offline
            for friend in users_col.find_one({"username": username}).get("friends", []):
                if friend in online_users:
                    emit("user_offline", {"username": username}, room=online_users.get(friend))
            
            print(f"{username} disconnected.")
            break
    
    print(f"Client disconnected: {request.sid}") # logging


#-----------------------------------------------------------
# Messages
#-----------------------------------------------------------

@socketio.on("user_register")
def handle_user_register(data):
    username = data["username"]
    password = data["password"]
    online_users[username] = request.sid
    
    if users_col.find_one({"username": username}):
        emit("user_register", {"status": "error", "message": "Username already exists"})
        return  # Username already exists
    
    user = {
        "username": username,
        "password": password,  # In real app, hash passwords!
        "friends": [],
        "groups": [],
        "time": time.time()
    }
    
    users_col.insert_one(user)
    user["_id"] = str(user["_id"])
    del user["password"]  # Do not send password back
    user["online_friends"] = []
    emit("user_register", {"status": "ok", "user": user} )
    
    print(f"{username} registered.") # logging
    
@socketio.on("user_message")
def handle_user_message(data):
    sender = data["from"]
    receiver = data["to"]
    msg = {
        "from": sender,
        "to": receiver,
        "text": data["text"],
        "time": time.time()
    }
    result = messages_col.insert_one(msg)
    msg["_id"] = str(result.inserted_id)

    # Deliver instantly if receiver online
    if receiver in online_users:
        emit("user_message", msg, room=online_users[receiver])

    emit("user_message", msg)  # echo back to sender
    print(f"Message from {sender} → {receiver}: {data['text']}") # logging

@socketio.on("get_user_messages")
def handle_get_user_messages(data):
    username = data["username"]
    friend = data["friend"]

    all = list(messages_col.find(
        {"$or": [
            {"from": username, "to": friend},
            {"from": friend, "to": username}
        ]}
    ))


    # Convert ObjectId for JSON
    for msg in all: msg["_id"] = str(msg["_id"])

    # Sending message history
    emit("get_user_messages", {"friend": friend, "messages": all})
    
    print("messsages sent to", username) # logging

#-----------------------------------------------------------
# Friendship Management
#-----------------------------------------------------------

@socketio.on("add_friend")
def handle_add_friend(data):
    username = data["username"]
    friend = data["friend"]
    
    if not users_col.find_one({"username": friend}):
        emit("add_friend", {"status": "error", "message": "Friend username not found"})
        return  # Friend username not found
    
    users_col.update_one({"username": username}, {"$addToSet": {"friends": friend}})
    users_col.update_one({"username": friend}, {"$addToSet": {"friends": username}})
    
    emit("add_friend", {"status": "ok", "friend": friend})
    if friend in online_users:
        emit("add_friend", {"friend": username}, room=online_users.get(friend))
    print(f"{username} added {friend} as a friend.") # logging

@socketio.on("remove_friend")
def handle_remove_friend(data):
    username = data["username"]
    friend = data["friend"]
    
    if not users_col.find_one({"username": friend}):
        emit("remove_friend", {"status": "error", "message": "Friend username not found"})
        return  # Friend username not found
    
    users_col.update_one({"username": username}, {"$pull": {"friends": friend}})
    users_col.update_one({"username": friend}, {"$pull": {"friends": username}})
    
    emit("remove_friend", {"status": "ok", "friend": friend})
    if friend in online_users:
        emit("remove_friend", {"friend": username}, room=online_users.get(friend))
    print(f"{username} removed {friend} from friends.") # logging

#-----------------------------------------------------------
# Group Messages
#-----------------------------------------------------------

@socketio.on("group_register")
def handle_group_register(data):
    print(data)
    
    r = request.sid
    for x in online_users: 
        if online_users[x] == r: 
            creator = x
            break
    
    creator = users_col.find_one({"username": creator})  # to verify user exists
    friends = creator.get("friends", [])
    members = [x for x in data["members"] if x in friends]
    members.append(creator["username"])  # ensure creator is in the group
    
    group_name = data["group_name"]
    
    if groups_col.find_one({"group_name": group_name}):
        emit("group_register", {"status": "error", "message": "Group name already exists"})
        return  # Group name already exists
    
    
    group = {
        "group_name": group_name,
        "admin": creator["username"],
        "members": members,
        "time": time.time()
    }
    groups_col.insert_one(group) # also adds the _id attribute 
    group["_id"] = str(group["_id"])
    
    print(group)
    
    users_col.update_many({"username": {"$in": members}}, {"$addToSet": {"groups": group_name}})
    
    print(members)
    print(group)
    # Notify all members about the new group
    for member in members:
        if member in online_users:
            emit("group_register", {"group": group}, room=online_users[member])

    print(f"Group '{group_name}' created with members {members}") # logging

@socketio.on("group_message")
def handle_group_message(data):
    
    sender = data["from"]
    group_name = data["group_name"]
    msg = {
        "from": sender,
        "to": group_name,
        "text": data["text"],
        "time": time.time()
    }
    result = messages_col.insert_one(msg)
    msg["_id"] = str(result.inserted_id)
    
    group = groups_col.find_one({"group_name": group_name})
    if not group:
        print(f"Group Name {group_name} not found.")
        return  # Group not found
    
    for member in group["members"]:
        if member != sender and member in online_users:
            emit("group_message", msg, room=online_users[member])
    
    emit("group_message", msg)  # echo back to sender
    print(f"Group Message from {sender} to Group {group_name}: {data['text']}") # logging
    
@socketio.on("get_group_messages")
def handle_get_group_messages(data):
    
    group_name = data["group_name"]
    username = data["username"]

    group = groups_col.find_one({"group_name": group_name})
    if not group or username not in group["members"]:
        print(f"Group ID {group_name} not found or user {username} not a member.")
        return  # Group not found or user not a member
    
    all = list(messages_col.find({"to": group_name}))
    for msg in all: msg["_id"] = str(msg["_id"])

    emit("get_group_messages", {"group_name": group_name, "messages": all})
    
    print(f"Group messages sent to {username} for Group {group_name}") # logging


#-----------------------------------------------------------
# Database Connection
#-----------------------------------------------------------

from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.

client = MongoClient(os.getenv("DB_URL"))
db = client['chat_app']

users_col = db['users']
groups_col = db['groups']
messages_col = db['messages']

#-----------------------------------------------------------
# Application Running
#-----------------------------------------------------------

@app.route("/")
def index():
    return "Flask-SocketIO server running!"

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
