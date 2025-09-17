## Ping (Chat Application)

#### A simple Python chat application with **server** and **client** using `socketio` and `Tkinter`.
#### The client is a Desktop Application
---

## ⚙️ Features

#### Chat with any friend in Real Time
#### Friend and Group management
#### Real Time messages management (Online status, New messages number)
#### Register and Login service

## 📜 Notes

#### First create .env file and replace <your_db_url> with your mongodb url.
#### (It should have 3 collections: users, groups, messages)
#### Make sure the server is running before starting the client.
#### Dependencies are listed in requirements.txt.


## 🚀 Setup

### 1. Clone the repository
```bash
git clone https://github.com/prasham15/Ping.git
cd Ping
```

```cmd/bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

```
pip install -r requirements.txt
```

## ⚙️ Running the App

### 1. Start the server
```
python server.py
```
### 2. Start the client (in another terminal) (from same folder)
```
python client.py
```
