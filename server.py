
import eventlet
eventlet.monkey_patch()
# server.py

from dotenv import load_dotenv
import os

load_dotenv()
database_uri = os.getenv("DATABASE_URI")


from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from bson.objectid import ObjectId
from datetime import datetime
import bcrypt


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Connect to MongoDB (replace URI with your own MongoDB Atlas URI)
uri = database_uri
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

db = client['chat_app']
users_col = db['users']
messages_col = db['messages']



# Store connected users and their session IDs
connected_users = {}


# -------- REST API Routes -------- #

# Register new user
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']

    if users_col.find_one({'username': username}):
        return jsonify({'status': 'error', 'message': 'User already exists'}), 400

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    users_col.insert_one({'username': username, 'password': hashed_pw})
    return jsonify({'status': 'success', 'message': 'User registered'})

# Login user
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    user = users_col.find_one({'username': username})
    if user and bcrypt.checkpw(password.encode(), user['password']):
        return jsonify({'status': 'success', 'message': 'Login successful'})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

# HTTP API for sending a message (can also use this as backup)
@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    sender = data['from']
    recipient = data['to']
    message = data['message']
    timestamp = datetime.utcnow()

    # Save message in database
    messages_col.insert_one({
        'sender': sender,
        'recipient': recipient,
        'message': message,
        'timestamp': timestamp
    })

    # Deliver in real-time if recipient is online
    recipient_sid = connected_users.get(recipient)
    if recipient_sid:
        socketio.emit('receive_message', {
            'from': sender,
            'message': message,
            'timestamp': timestamp.isoformat()
        }, to=recipient_sid)
        return jsonify({'status': 'delivered'})
    else:
        return jsonify({'status': 'stored - recipient offline'})

# -------- Socket.IO Events -------- #

@socketio.on('connect')
def on_connect():
    print('Client connected:', request.sid)

@socketio.on('register_socket')
def handle_register_socket(data):
    username = data['username']
    connected_users[username] = request.sid
    print(f"{username} connected with sid {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    user_to_remove = None
    for user, user_sid in connected_users.items():
        if user_sid == sid:
            user_to_remove = user
            break
    if user_to_remove:
        del connected_users[user_to_remove]
        print(f"{user_to_remove} disconnected")

# -------- Start Server -------- #
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
