## Ping (Chat Application)

 #### 1. A simple Python chat application with **server** and **client** using `socketio` and `Tkinter`.
 #### 2. The client is a Desktop Application
---

## ⚙️ Current Features

#### 1. Chat with any friend in Real Time
#### 2. Friend and Group management
#### 3. Real Time messages management (Online status, Unread messages)
#### 4. Register and Login service

## Future Features

#### 1. Images and Video
#### 2. AI Support



## 📜 Notes

#### 1. First create .env file and replace <your_db_url> with your mongodb url.
#### 2. (It should have 3 collections: users, groups, messages)
#### 3. Make sure the server is running before starting the client.
#### 4. Dependencies are listed in requirements.txt.


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
