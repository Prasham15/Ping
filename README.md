# 🗨️ Terminal Chat App

A simple Python-based terminal chat application using sockets. This project includes both server and client code, allowing real-time messaging between multiple users on the same network.

## 🚀 Features

- Real-time messaging in terminal
- Easy-to-use client and server architecture
- Environment configuration support via `.env` file
- Lightweight and minimal dependencies

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Prasham15/chat.git
cd chat
2. Configure Environment
Copy .env.example to .env and edit it as needed:

bash
Copy
Edit
cp .env.example .env
3. Install Requirements (if any)
If you use additional libraries, install them:

bash
Copy
Edit
pip install -r requirements.txt
4. Run the Server
bash
Copy
Edit
python server.py
5. Run the Client
Open a new terminal window:

bash
Copy
Edit
python client.py
🧪 Example
arduino
Copy
Edit
[Client 1] > Hello!
[Client 2] > Hi there! How are you?
📁 File Structure
bash
Copy
Edit
chat/
├── client.py        # Chat client code
├── server.py        # Chat server code
├── .env             # Environment variables
├── .env.example     # Sample environment config
└── .gitignore       # Git ignored files
🔐 Security Notes
This is for local or LAN use only. Do not expose to the public internet without encryption and authentication mechanisms.

Add user authentication and encrypted communication (e.g., TLS) for production use.

📌 Future Enhancements
 GUI using Tkinter or PyQt

 TLS encryption

 Chat history logging

 User authentication

👨‍💻 Author
Prasham Sandeep Shah
GitHub: Prasham15
