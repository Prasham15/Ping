import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import socketio


config = {}

# ---------------------------------------------------------
# Socket.IO client
# ---------------------------------------------------------

sio = socketio.Client()

@sio.on("connect")
def on_connect():
    print("Connected to server")

@sio.on("login")
def on_login(data):
    if data["status"] == "ok":
        config["username"] = data["user"]["username"]
        config["groups"] = data["user"].get("groups", [])
        config["friends"] = data["user"].get("friends", [])
        d = {}
        for x in data["user"].get("online_friends", []): d[x] = 0
        config["online_pendings"] = d
        
        app.set_status(f"Logged in as {data['user']['username']}")
        login_app.dialog.destroy()
        app.root.deiconify()
        app.populate_chats()
    else:
        messagebox.showerror("Login Failed", data.get("message","Unknown Error"))

#-----------------------------------------------------------
# Socket Events listners and handlers
#-----------------------------------------------------------

@sio.on("user_online")
def on_user_online(data):
    username = data["username"]
    if username not in config["online_pendings"]:
        config["online_pendings"][username] = 0
    app.populate_chats()

@sio.on("user_offline")
def on_user_offline(data):  
    username = data["username"]
    del config["online_pendings"][username]
    app.populate_chats()

@sio.on("user_message")
def on_user_message(msg):
    if app.current_chat == msg["from"] or app.current_chat == msg["to"]:
        app.display_message(msg)
    else: 
        username = config["username"]
        if msg["to"] == username:    
            config["online_pendings"][msg["from"]] = config["online_pendings"].get(msg["from"], 0)+1
        else:
            config["online_pendings"][msg["to"]] = config["online_pendings"].get(msg["to"], 0)+1
        app.populate_chats()
        
@sio.on("group_message")
def on_group_message(msg):
    if app.current_chat == msg["to"]:
        app.display_message(msg)
    else:
        group_name = msg["to"]
        config["online_pendings"][group_name] = config["online_pendings"].get(group_name, 0)+1
        app.populate_chats()

@sio.on("get_user_messages")
def on_user_messages(data):
    if app.current_chat == data["friend"]:
        app.show_messages(data["messages"])
        if data["friend"] in config["online_pendings"]:
            config["online_pendings"][data["friend"]] = 0
        app.populate_chats()

@sio.on("get_group_messages")
def on_group_messages(data):
    if app.current_chat == data["group_name"]:
        app.show_messages(data["messages"])
        if data["group_name"] in config["online_pendings"]:
            config["online_pendings"][data["group_name"]] = 0
        app.populate_chats()

@sio.on("group_register")
def on_group_register(data):
    config["groups"].append(data["group"]["group_name"])
    app.populate_chats()

@sio.on("user_register")
def on_user_register(data):
    print("user_register",data)
    
    if data["status"] == "ok":
        config["username"] = data["user"]["username"]
        config["groups"] = data["user"].get("groups", [])
        config["friends"] = data["user"].get("friends", [])
        d = {}
        for x in data["user"].get("online_friends", []): d[x] = 0
        config["online_pendings"] = d
        
        app.set_status(f"Logged in as {data['user']['username']}")
        login_app.dialog.destroy()
        app.root.deiconify()
        app.populate_chats()
        
    else:
        messagebox.showerror("Registration Failed", data["message"])

@sio.on("add_friend")
def on_add_friend(data):
    if "status" in data:
        if data["status"] == "ok":
            config["friends"].append(data["friend"])
            app.populate_chats()
        else:
            messagebox.showerror("Add Friend Failed", data["message"])
    else:
        config["friends"].append(data["friend"])
        app.populate_chats()
        
@sio.on("remove_friend")
def on_remove_friend(data): 
    if "status" in data:
        if data["status"] == "ok":
            if data["friend"] in config["friends"]:
                config["friends"].remove(data["friend"])
            app.populate_chats()
        else:
            messagebox.showerror("Remove Friend Failed", data["message"])
    else:
        if data["friend"] in config["friends"]:
            config["friends"].remove(data["friend"])
        app.populate_chats()
        
# --------------------------------------------------------
# Tkinter Chat App
# ---------------------------------------------------------

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Chat Client")
        self.root.geometry("800x600")
        self.root.configure(bg="#CBDCF7")

        self.current_chat = None


        # Left frame (chat list)
        self.left_frame = tk.Frame(root, width=220, bg="#CBDCF7")
        self.left_frame.pack(side="left", fill="y")

        self.chat_list_frame = tk.Frame(self.left_frame, bg="#CBDCF7")
        self.chat_list_frame.pack(fill="both", expand=True)

        self.add_user_btn = tk.Button(
            self.left_frame, text="+ Add User", 
            bg="#84ADEA", fg="white", relief="flat",
            command=self.add_user
        )
        self.add_user_btn.pack(fill="x", pady=2)

        self.add_group_btn = tk.Button(
            self.left_frame, text="+ Create Group", 
            bg="#84ADEA", fg="white", relief="flat",
            command=self.create_group
        )
        self.add_group_btn.pack(fill="x", pady=2)

        # Right frame (messages)
        self.right_frame = tk.Frame(root, bg="#ffffff")
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.status_label = tk.Label(self.right_frame, text="Not logged in",
                                     anchor="w", bg="#ffffff", fg="black", font=("Arial", 10))
        self.status_label.pack(fill="x", pady=5)

        self.chat_display = scrolledtext.ScrolledText(
            self.right_frame, state="disabled", bg="#ffffff", fg="black", insertbackground="black",
            font=("Consolas", 11), wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)

        self.msg_entry = tk.Entry(self.right_frame, bg="#ffffff", fg="black", insertbackground="black", font=("Arial", 11))
        self.msg_entry.pack(fill="x", padx=10, pady=5)
        self.msg_entry.bind("<Return>", self.send_message)

        self.populate_chats()

    def set_status(self, text):
        self.status_label.config(text=text)

    def populate_chats(self):
        for widget in self.chat_list_frame.winfo_children():
            widget.destroy()
        
        background = "#84ADEA"
            
        for gname in config.get("groups",[]):
            background = "#84ADEA"
            if gname == self.current_chat: background = "#4A90E2"
            pendings = config["online_pendings"].get(gname, 0)
            display_name = f"[Group] {gname}" + (f" ({pendings})" if pendings>0 else "")
            
            tk.Button(self.chat_list_frame, text=display_name, bg=background, fg="lightblue",
                      relief="flat", anchor="w",
                      command=lambda g=gname: self.open_chat(g)).pack(fill="x", pady=1)
        
        for friend in config.get("friends", []):
            background = "#84ADEA"
            if friend == self.current_chat: background = "#4A90E2"
            pendings = config["online_pendings"].get(friend, 0)
            status = " (Online)" if friend in config.get("online_pendings", []) else " (Offline)"
            display_name = friend + status + (f" ({pendings})" if pendings>0 else "")
            
            tk.Button(self.chat_list_frame, text=display_name, bg=background, fg="white",
                      relief="flat", anchor="w",
                      command=lambda f=friend: self.open_chat(f)).pack(fill="x", pady=1)

    def add_user(self):
        username = simpledialog.askstring("Add User", "Enter username:")
        sio.emit("add_friend", {"username": config["username"], "friend": username})

    def create_group(self):
        group_name = simpledialog.askstring("New Group", "Enter group name:")
        if not group_name:
            return
        members = simpledialog.askstring("New Group", "Enter members (comma separated):")
        members = list(set([m.strip() for m in members.split(",") if m.strip()]))
        if not members:
            return
        
        if config["username"] in members:
            members.remove(config["username"])
            
        member_list = [config["username"]]+members
        sio.emit("group_register", {"group_name": group_name, "members": member_list})

    def open_chat(self, current_chat):
        self.current_chat = current_chat
        self.chat_display.config(state="normal")
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state="disabled")

        if current_chat in config["groups"]:
            sio.emit("get_group_messages", {"username": config["username"], "group_name": current_chat})
        else:
            sio.emit("get_user_messages", {"username": config["username"], "friend": current_chat})
            
    def show_messages(self, messages):
        self.chat_display.config(state="normal")
        self.chat_display.delete(1.0, tk.END)
        for msg in messages:
            self.display_message(msg, insert_only=True)
        self.chat_display.config(state="disabled")

    def display_message(self, msg, insert_only=False):
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"{msg['from']}: {msg['text']}\n")
        self.chat_display.config(state="disabled")
        self.chat_display.yview(tk.END)

    def send_message(self, event=None):
        if not self.current_chat:
            return
        text = self.msg_entry.get().strip()
        if not text:
            return
        if self.current_chat in config["groups"]:
            sio.emit("group_message", {"from": config["username"], "group_name": self.current_chat, "text": text})
        else:
            sio.emit("user_message", {"from": config["username"], "to": self.current_chat, "text": text})
        self.msg_entry.delete(0, tk.END)


#-----------------------------------------------------------
# Login Dilogbox
#---------------------------------------------------------- 
class LoginDialog:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # hide main window

        self.dialog = tk.Toplevel(root)
        self.dialog.title("Login")
        self.dialog.geometry("300x200")
        self.dialog.configure(bg="#CBDCF7")
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)

        tk.Label(self.dialog, text="Username:", bg="#CBDCF7").pack(pady=5)
        self.username_entry = tk.Entry(self.dialog, bg="#ffffff", fg="black", insertbackground="black")
        self.username_entry.pack(pady=5)

        tk.Label(self.dialog, text="Password:", bg="#CBDCF7").pack(pady=5)
        self.password_entry = tk.Entry(self.dialog, show="*", bg="#ffffff", fg="black", insertbackground="black")
        self.password_entry.pack(pady=5)

        self.login_btn = tk.Button(
            self.dialog, text="Login",
            bg="#84ADEA", fg="white", relief="flat",
            command=self.attempt_login
        )
        self.login_btn.pack(pady=10)
        
        self.register_btn = tk.Button(
            self.dialog, text="Register",
            bg="#84ADEA", fg="white", relief="flat",
            command=self.attempt_register
        )
        self.register_btn.pack(pady=10)
        

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if username and password:
            sio.emit("login", {"username": username, "password": password})
        else:
            messagebox.showerror("Error", "Please enter both username and password.")

    def attempt_register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if username and password:
            sio.emit("user_register", {"username": username, "password": password})
        else:
            messagebox.showerror("Error", "Please enter both username and password.")
        
        
        
    def on_close(self):
        self.dialog.destroy()
        self.root.destroy()  # exit whole app if login window closed
    
# -----------------------------------------------------------
# Run client
# ----------------------------------------------------------


def start_client():
    global app
    global login_app
    root = tk.Tk()
    app = ChatApp(root)
    
    try:
        sio.connect("http://localhost:5000")
    except Exception as e:
        messagebox.showerror("Connection Error", str(e))
        return
    
    login_app = LoginDialog(root)
    
    root.mainloop()

if __name__ == "__main__":
    start_client()
