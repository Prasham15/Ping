# client_curses.py

import curses
import socketio
import requests
import threading
import queue
import sys


SERVER_URL = 'http://localhost:5000'
sio = socketio.Client()
current_user = None
message_queue = queue.Queue()


# --------------------------------------------
# Socket.IO Events
# --------------------------------------------
@sio.on("connect")
def on_connect():
    sio.emit('register_socket', {'username': current_user})
    message_queue.put("[Socket] Connected to server.")

@sio.on('receive_message')
def on_message(data):
    message_queue.put(f"[{data['from']}] {data['message']}")

# --------------------------------------------
# UI Rendering with Curses
# --------------------------------------------
def draw_ui(stdscr):
    curses.curs_set(1)
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    chat_win_height = height - 3
    chat_win = curses.newwin(chat_win_height, width, 0, 0)
    chat_win.scrollok(True)

    input_win = curses.newwin(3, width, chat_win_height, 0)

    def refresh_chat():
        chat_win.clear()
        lines = list(message_queue.queue)[-chat_win_height:]
        for idx, msg in enumerate(lines):
            chat_win.addstr(idx, 0, msg)
        chat_win.refresh()
        

    while True:
        refresh_chat()
        input_win.clear()
        input_win.addstr(0, 0, "To: ")
        curses.echo()
        to = input_win.getstr(0, 4, 20).decode('utf-8').strip()
        input_win.addstr(1, 0, "Message: ")
        message = input_win.getstr(1, 9).decode('utf-8').strip()
        curses.noecho()

        if message.lower() == "/quit":
            break

        if to and message:
            threading.Thread(target=send_message,args=[current_user, to, message]).start()

def send_message(sender, recipient, message):
    r = requests.post(f'{SERVER_URL}/send', json={
        'from': sender,
        'to': recipient,
        'message': message
    })
    status = r.json().get('status', 'error')
    message_queue.put(f"[{sender} -> {recipient}] {message} (status: {status})")

# --------------------------------------------
# Registration & Login Flow
# --------------------------------------------
def register_user():
    username = input("Choose username: ").strip()
    password = input("Choose password: ").strip()
    res = requests.post(f'{SERVER_URL}/register', json={
        'username': username,
        'password': password
    })
    print(res.json()['message'])
    return res.status_code == 200

def login_user():
    global current_user
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    res = requests.post(f'{SERVER_URL}/login', json={
        'username': username,
        'password': password
    })
    if res.status_code == 200:
        print("[+] Login successful.")
        current_user = username
        return True
    else:
        print("[-] Login failed:", res.json().get('message'))
        return False

def auth_menu():
    print("==== Terminal Chat ====")
    print("1. Register")
    print("2. Login")
    print("3. Exit")
    choice = input("Choose option: ").strip()
    if choice == '1':
        if register_user():
            return login_user()
        return False
    elif choice == '2':
        return login_user()
    elif choice == '3':
        sys.exit()
    else:
        print("Invalid choice.")
        return False

# --------------------------------------------
# Main Entry
# --------------------------------------------
def main():
    while not auth_menu():
        print("Try again.\n")

    # Connect to real-time server
    sio.connect(SERVER_URL)

    # Launch terminal chat UI
    curses.wrapper(draw_ui)

    # Clean exit
    sio.disconnect()
    print("Disconnected. Bye!")

if __name__ == '__main__':
    main()
