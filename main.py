import os
import requests
from plyer import filechooser

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage

# =========================================================
# SERVER CONFIGURATION
# =========================================================
SERVER_URL = "https://aarsjahad.pythonanywhere.com"

def get_dp_url(filename):
    if filename:
        return f"{SERVER_URL}/uploads/{filename}"
    return "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"

# =========================================================
# LOGIN SCREEN 
# =========================================================
class LoginScreen(Screen):
    def login(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text
        
        if not username or not password:
            self.ids.info.text = "Enter Username and Password."
            return
            
        self.ids.info.text = "Logging in..."
        try:
            res = requests.post(f"{SERVER_URL}/api/login", json={"username": username, "password": password}, timeout=10)
            data = res.json()
            if data.get("success"):
                App.get_running_app().current_user = data["user"]
                self.ids.password.text = ""
                self.ids.info.text = ""
                self.manager.current = "home"
            else:
                self.ids.info.text = data.get("message", "Login failed.")
        except Exception:
            self.ids.info.text = "Cannot connect to server."

# =========================================================
# REGISTER SCREEN
# =========================================================
class RegisterScreen(Screen):
    def request_otp(self):
        email = self.ids.email.text.strip()
        if not email:
            self.ids.info.text = "Enter Gmail address first."
            return
        self.ids.info.text = "Sending OTP..."
        try:
            res = requests.post(f"{SERVER_URL}/api/auth/send_otp", json={"email": email}, timeout=10)
            self.ids.info.text = res.json().get("message", "Check email/terminal")
        except Exception:
            self.ids.info.text = "Server connection error."

    def register(self):
        display_name = self.ids.display_name.text.strip()
        username = self.ids.username.text.strip()
        email = self.ids.email.text.strip()
        otp = self.ids.otp.text.strip()
        password = self.ids.password.text
        confirm = self.ids.confirm.text

        if not all([display_name, username, email, otp, password]):
            self.ids.info.text = "All fields are required."
            return
        if password != confirm:
            self.ids.info.text = "Passwords do not match."
            return
            
        self.ids.info.text = "Creating account..."
        try:
            res = requests.post(
                f"{SERVER_URL}/api/register", 
                json={"email": email, "otp": otp, "username": username, "password": password, "display_name": display_name}, 
                timeout=10
            )
            data = res.json()
            if data.get("success"):
                self.ids.info.text = "Account created!"
                App.get_running_app().current_user = data["user"]
                self.manager.current = "home"
            else:
                self.ids.info.text = data.get("message", "Registration failed.")
        except Exception:
            self.ids.info.text = "Cannot connect to server."

# =========================================================
# FORGOT PASSWORD SCREEN 
# =========================================================
class ForgotPasswordScreen(Screen):
    def request_otp(self):
        email = self.ids.email.text.strip()
        if not email:
            self.ids.info.text = "Enter registered Gmail first."
            return
        self.ids.info.text = "Sending OTP..."
        try:
            res = requests.post(f"{SERVER_URL}/api/auth/send_otp", json={"email": email}, timeout=10)
            self.ids.info.text = res.json().get("message", "Check email/terminal")
        except Exception:
            self.ids.info.text = "Server connection error."
            
    def reset_password(self):
        email = self.ids.email.text.strip()
        otp = self.ids.otp.text.strip()
        new_password = self.ids.new_password.text
        
        if not all([email, otp, new_password]):
            self.ids.info.text = "All fields are required."
            return
            
        self.ids.info.text = "Resetting password..."
        try:
            res = requests.post(
                f"{SERVER_URL}/api/auth/reset_password",
                json={"email": email, "otp": otp, "new_password": new_password},
                timeout=10
            )
            if res.json().get("success"):
                self.ids.info.text = "Password reset successful! Go to Login."
                self.ids.otp.text = ""
                self.ids.new_password.text = ""
            else:
                self.ids.info.text = res.json().get("message", "Failed to reset.")
        except Exception:
            self.ids.info.text = "Cannot connect to server."

# =========================================================
# CREATE GROUP SCREEN
# =========================================================
class CreateGroupScreen(Screen):
    def create_group(self):
        name = self.ids.group_name.text.strip()
        usernames = self.ids.members.text.strip()
        if not name: 
            return
            
        app = App.get_running_app()
        try:
            res = requests.post(
                f"{SERVER_URL}/api/groups/create", 
                json={"creator_id": app.current_user["id"], "name": name, "usernames": usernames}, 
                timeout=10
            )
            if res.json().get("success"):
                self.ids.group_name.text = ""
                self.ids.members.text = ""
                self.manager.current = "home"
        except Exception: 
            pass

# =========================================================
# HOME SCREEN
# =========================================================
class HomeScreen(Screen):
    def on_pre_enter(self):
        self.load_recent_chats()

    def load_recent_chats(self):
        app = App.get_running_app()
        if not app.current_user: 
            return
        self.ids.results.clear_widgets()
        try:
            res = requests.get(f"{SERVER_URL}/api/home_data/{app.current_user['id']}", timeout=10)
            data = res.json()
            if data.get("success"):
                for grp in data.get("groups", []): 
                    self.add_group_card(grp)
                for user in data.get("chats", []): 
                    self.add_user_card(user)
        except Exception: 
            pass

    def search_users(self):
        query = self.ids.search.text.strip()
        self.ids.results.clear_widgets()
        if not query:
            self.load_recent_chats()
            return
        try:
            res = requests.get(f"{SERVER_URL}/api/users/search", params={"q": query}, timeout=10)
            users = res.json().get("users", [])
            for user in users:
                if user["id"] != App.get_running_app().current_user["id"]:
                    self.add_user_card(user)
        except Exception: 
            pass

    def add_user_card(self, user):
        box = BoxLayout(orientation='horizontal', size_hint_y=None, height="60dp", padding="5dp", spacing="10dp")
        img = AsyncImage(source=get_dp_url(user.get("profile_picture")), size_hint_x=None, width="50dp", allow_stretch=True)
        btn = Button(text=f"👤 {user['display_name']}  (@{user['username']})", background_normal="", background_color=(0.08, 0.08, 0.08, 1), color=(0, 1, 0.35, 1), halign="left")
        btn.target_id = user["id"]
        btn.target_name = user["display_name"]
        btn.is_group = False
        btn.bind(on_release=self.open_chat)
        
        box.add_widget(img)
        box.add_widget(btn)
        self.ids.results.add_widget(box)

    def add_group_card(self, group):
        box = BoxLayout(orientation='horizontal', size_hint_y=None, height="60dp", padding="5dp", spacing="10dp")
        btn = Button(text=f"👥 {group['name']}", background_normal="", background_color=(0.12, 0.12, 0.12, 1), color=(1, 0.8, 0.2, 1), halign="left")
        btn.target_id = group["id"]
        btn.target_name = group["name"]
        btn.is_group = True
        btn.bind(on_release=self.open_chat)
        
        box.add_widget(btn)
        self.ids.results.add_widget(box)

    def open_chat(self, button):
        chat = self.manager.get_screen("chat")
        chat.setup_chat(button.target_id, button.target_name, button.is_group)
        self.manager.current = "chat"

# =========================================================
# CHAT SCREEN
# =========================================================
class ChatScreen(Screen):
    target_id = None
    target_name = ""
    is_group = False
    poll_event = None
    last_message_count = 0

    def on_enter(self):
        self.poll_event = Clock.schedule_interval(lambda dt: self.load_messages(silent=True), 2)
        
    def on_leave(self):
        if self.poll_event: 
            self.poll_event.cancel()

    def setup_chat(self, t_id, t_name, is_grp):
        self.target_id = t_id
        self.target_name = t_name
        self.is_group = is_grp
        
        self.ids.friend_name.text = ("👥 " if is_grp else "👤 ") + self.target_name
        self.last_message_count = 0
        self.ids.messages.clear_widgets()
        self.load_messages()

    def load_messages(self, silent=False):
        app = App.get_running_app()
        if not app.current_user or self.target_id is None: 
            return
            
        try:
            if self.is_group:
                url = f"{SERVER_URL}/api/groups/messages/{self.target_id}"
            else:
                url = f"{SERVER_URL}/api/messages/{app.current_user['id']}/{self.target_id}"
                
            response = requests.get(url, timeout=5)
            messages = response.json().get("messages", [])
            
            if len(messages) == self.last_message_count: 
                return
                
            self.last_message_count = len(messages)
            self.ids.messages.clear_widgets()

            for msg in messages:
                mine = int(msg.get("sender_id")) == int(app.current_user["id"])
                msg_type = msg.get("message_type", "text")
                sender_name = msg.get("sender_name", "") if (self.is_group and not mine) else ""
                
                if msg_type == "image": 
                    self.add_image_bubble(msg.get("file_path"), mine, sender_name)
                elif msg_type == "document": 
                    self.add_document_bubble(msg.get("file_name"), msg.get("file_path"), mine, sender_name)
                else: 
                    self.add_text_bubble(msg.get("content", ""), mine, sender_name)
                    
            self.ids.scroll_view.scroll_y = 0
        except Exception: 
            pass

    def add_text_bubble(self, text, mine, sender_name):
        row = BoxLayout(
            orientation="vertical" if sender_name else "horizontal", 
            size_hint_y=None, 
            height="60dp" if sender_name else "50dp", 
            padding="4dp"
        )
        
        if sender_name:
            name_lbl = Label(text=sender_name, color=(1,0.8,0.2,1), size_hint_y=None, height="15dp", font_size="10sp", halign="left")
            name_lbl.bind(size=name_lbl.setter('text_size'))
            row.add_widget(name_lbl)
            
        lbl = Label(text=f"  {text}  ", size_hint=(None, None), height="42dp", halign="left", valign="middle")
        lbl.bind(texture_size=lambda i, v: setattr(i, 'width', max(v[0] + 20, 80)))
        
        h_box = BoxLayout(orientation="horizontal")
        
        lbl.color = (0, 0, 0, 1) if mine else (1, 1, 1, 1)
        lbl.canvas.before.clear()
        with lbl.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            if mine:
                Color(0, 1, 0.35, 1)
                RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=[10, 10, 2, 10])
            else:
                Color(0.15, 0.15, 0.15, 1)
                RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=[10, 10, 10, 2])
                
        lbl.bind(pos=self._update_rect, size=self._update_rect)
        
        if mine: 
            h_box.add_widget(BoxLayout())
            h_box.add_widget(lbl)
        else: 
            h_box.add_widget(lbl)
            h_box.add_widget(BoxLayout())
        
        if sender_name: 
            row.add_widget(h_box)
            self.ids.messages.add_widget(row)
        else: 
            self.ids.messages.add_widget(h_box)

    def add_image_bubble(self, file_path, mine, sender_name):
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height="160dp", padding="5dp")
        img = AsyncImage(source=f"{SERVER_URL}/uploads/{file_path}", size_hint=(None, None), size=("150dp", "150dp"), allow_stretch=True)
        if mine: 
            row.add_widget(BoxLayout())
            row.add_widget(img)
        else: 
            row.add_widget(img)
            row.add_widget(BoxLayout())
        self.ids.messages.add_widget(row)

    def add_document_bubble(self, file_name, file_path, mine, sender_name):
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height="50dp", padding="4dp")
        btn = Button(text=f"📄 {file_name[:20]}", size_hint=(None, None), size=("200dp", "40dp"), background_normal="", background_color=(0, 0.6, 0.3, 1) if mine else (0.2, 0.2, 0.2, 1), color=(1, 1, 1, 1))
        if mine: 
            row.add_widget(BoxLayout())
            row.add_widget(btn)
        else: 
            row.add_widget(btn)
            row.add_widget(BoxLayout())
        self.ids.messages.add_widget(row)

    def _update_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            if instance.color == [0, 0, 0, 1]:
                Color(0, 1, 0.35, 1)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10, 10, 2, 10])
            else:
                Color(0.15, 0.15, 0.15, 1)
                RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10, 10, 10, 2])

    def send_message(self):
        text = self.ids.message.text.strip()
        if not text: 
            return
            
        app = App.get_running_app()
        payload = {"sender_id": app.current_user["id"], "message": text}
        
        if self.is_group:
            payload["group_id"] = self.target_id
        else:
            payload["receiver_id"] = self.target_id
            
        try:
            res = requests.post(f"{SERVER_URL}/api/messages/send", json=payload, timeout=10)
            if res.json().get("success"):
                self.ids.message.text = ""
                self.load_messages()
        except Exception: 
            pass

    def open_file_picker(self):
        try: 
            filechooser.open_file(on_selection=self.upload_file)
        except Exception: 
            pass

    def upload_file(self, selection):
        if not selection: 
            return
            
        app = App.get_running_app()
        try:
            payload = {"sender_id": str(app.current_user["id"])}
            if self.is_group:
                payload["group_id"] = str(self.target_id)
            else:
                payload["receiver_id"] = str(self.target_id)
                
            with open(selection[0], "rb") as f:
                requests.post(
                    f"{SERVER_URL}/api/messages/send", 
                    data=payload, 
                    files={"file": (os.path.basename(selection[0]), f)}, 
                    timeout=20
                )
                self.load_messages()
        except Exception: 
            pass

    def back_home(self): 
        self.manager.current = "home"

# =========================================================
# PROFILE SCREEN
# =========================================================
class ProfileScreen(Screen):
    def on_pre_enter(self):
        user = App.get_running_app().current_user
        if user:
            self.ids.display_name.text = user["display_name"]
            self.ids.username.text = f"@{user['username']}"
            self.ids.dp_image.source = get_dp_url(user.get("profile_picture"))
            
    def choose_dp(self):
        try: 
            filechooser.open_file(on_selection=self.upload_dp, filters=[("Images", "*.png", "*.jpg", "*.jpeg")])
        except Exception: 
            pass
            
    def upload_dp(self, selection):
        if not selection: 
            return
        app = App.get_running_app()
        try:
            with open(selection[0], "rb") as f:
                res = requests.post(
                    f"{SERVER_URL}/api/user/dp/{app.current_user['id']}", 
                    files={"file": (os.path.basename(selection[0]), f)}, 
                    timeout=20
                )
                if res.json().get("success"):
                    app.current_user = res.json()["user"]
                    self.ids.dp_image.source = get_dp_url(app.current_user.get("profile_picture"))
        except Exception: 
            pass
            
    def logout(self):
        App.get_running_app().current_user = None
        self.manager.current = "login"


# =========================================================
# KV INTERFACE DESIGN (Properly Indented)
# =========================================================
KV = """
ScreenManager:
    LoginScreen:
        name: "login"
    RegisterScreen:
        name: "register"
    ForgotPasswordScreen:
        name: "forgot_password"
    HomeScreen:
        name: "home"
    CreateGroupScreen:
        name: "create_group"
    ChatScreen:
        name: "chat"
    ProfileScreen:
        name: "profile"

<LoginScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: "25dp"
        spacing: "12dp"
        canvas.before:
            Color:
                rgb: 0.03, 0.03, 0.03
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "ALMA X"
            font_size: "34sp"
            bold: True
            color: 0, 1, 0.35, 1
            size_hint_y: None
            height: "70dp"
        TextInput:
            id: username
            hint_text: "Username"
            multiline: False
            size_hint_y: None
            height: "48dp"
        TextInput:
            id: password
            hint_text: "Password"
            password: True
            multiline: False
            size_hint_y: None
            height: "48dp"
        Label:
            id: info
            text: ""
            size_hint_y: None
            height: "30dp"
            color: 1, 0.35, 0.35, 1
        Button:
            text: "LOGIN"
            size_hint_y: None
            height: "48dp"
            background_normal: ""
            background_color: 0, 1, 0.35, 1
            color: 0, 0, 0, 1
            on_release: root.login()
        Button:
            text: "FORGOT PASSWORD?"
            size_hint_y: None
            height: "40dp"
            background_normal: ""
            background_color: 0, 0, 0, 0
            color: 1, 0.8, 0.2, 1
            on_release: root.manager.current = "forgot_password"
        Button:
            text: "CREATE NEW ACCOUNT"
            size_hint_y: None
            height: "45dp"
            background_normal: ""
            background_color: 0, 0, 0, 0
            color: 0, 1, 0.35, 1
            on_release: root.manager.current = "register"

<RegisterScreen>:
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgb: 0.03, 0.03, 0.03
            Rectangle:
                pos: self.pos
                size: self.size
        ScrollView:
            BoxLayout:
                orientation: "vertical"
                padding: "25dp"
                spacing: "10dp"
                size_hint_y: None
                height: self.minimum_height
                Label:
                    text: "CREATE ACCOUNT"
                    font_size: "24sp"
                    bold: True
                    color: 0, 1, 0.35, 1
                    size_hint_y: None
                    height: "55dp"
                TextInput:
                    id: display_name
                    hint_text: "Display Name"
                    multiline: False
                    size_hint_y: None
                    height: "45dp"
                TextInput:
                    id: username
                    hint_text: "Username (no spaces)"
                    multiline: False
                    size_hint_y: None
                    height: "45dp"
                BoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "45dp"
                    spacing: "5dp"
                    TextInput:
                        id: email
                        hint_text: "Gmail Address"
                        multiline: False
                    Button:
                        text: "SEND OTP"
                        size_hint_x: None
                        width: "80dp"
                        background_normal: ""
                        background_color: 0.1, 0.1, 0.1, 1
                        color: 0, 1, 0.35, 1
                        on_release: root.request_otp()
                TextInput:
                    id: otp
                    hint_text: "Enter OTP"
                    password: True
                    multiline: False
                    size_hint_y: None
                    height: "45dp"
                TextInput:
                    id: password
                    hint_text: "Set Password"
                    password: True
                    multiline: False
                    size_hint_y: None
                    height: "45dp"
                TextInput:
                    id: confirm
                    hint_text: "Confirm Password"
                    password: True
                    multiline: False
                    size_hint_y: None
                    height: "45dp"
                Label:
                    id: info
                    text: ""
                    size_hint_y: None
                    height: "30dp"
                    color: 1, 0.35, 0.35, 1
                Button:
                    text: "SIGN UP"
                    size_hint_y: None
                    height: "48dp"
                    background_normal: ""
                    background_color: 0, 1, 0.35, 1
                    color: 0, 0, 0, 1
                    on_release: root.register()
                Button:
                    text: "BACK TO LOGIN"
                    size_hint_y: None
                    height: "40dp"
                    background_normal: ""
                    background_color: 0, 0, 0, 0
                    color: 0, 1, 0.35, 1
                    on_release: root.manager.current = "login"

<ForgotPasswordScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: "25dp"
        spacing: "12dp"
        canvas.before:
            Color:
                rgb: 0.03, 0.03, 0.03
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "RESET PASSWORD"
            font_size: "24sp"
            bold: True
            color: 1, 0.8, 0.2, 1
            size_hint_y: None
            height: "60dp"
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "48dp"
            spacing: "5dp"
            TextInput:
                id: email
                hint_text: "Registered Gmail"
                multiline: False
            Button:
                text: "SEND OTP"
                size_hint_x: None
                width: "80dp"
                background_normal: ""
                background_color: 0.1, 0.1, 0.1, 1
                color: 1, 0.8, 0.2, 1
                on_release: root.request_otp()
        TextInput:
            id: otp
            hint_text: "Enter OTP"
            password: True
            multiline: False
            size_hint_y: None
            height: "48dp"
        TextInput:
            id: new_password
            hint_text: "New Password"
            password: True
            multiline: False
            size_hint_y: None
            height: "48dp"
        Label:
            id: info
            text: ""
            size_hint_y: None
            height: "30dp"
            color: 1, 0.35, 0.35, 1
        Button:
            text: "UPDATE PASSWORD"
            size_hint_y: None
            height: "48dp"
            background_normal: ""
            background_color: 1, 0.8, 0.2, 1
            color: 0, 0, 0, 1
            on_release: root.reset_password()
        Button:
            text: "BACK TO LOGIN"
            size_hint_y: None
            height: "40dp"
            background_normal: ""
            background_color: 0, 0, 0, 0
            color: 1, 1, 1, 1
            on_release: root.manager.current = "login"

<CreateGroupScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: "25dp"
        spacing: "15dp"
        canvas.before:
            Color:
                rgb: 0.03, 0.03, 0.03
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "CREATE NEW GROUP"
            font_size: "24sp"
            bold: True
            color: 1, 0.8, 0.2, 1
            size_hint_y: None
            height: "60dp"
        TextInput:
            id: group_name
            hint_text: "Group Name"
            multiline: False
            size_hint_y: None
            height: "50dp"
        TextInput:
            id: members
            hint_text: "Add friends (comma separated usernames)"
            multiline: False
            size_hint_y: None
            height: "50dp"
        Label:
            id: info
            text: ""
            size_hint_y: None
            height: "40dp"
            color: 1, 0.35, 0.35, 1
        Button:
            text: "CREATE GROUP"
            size_hint_y: None
            height: "50dp"
            background_normal: ""
            background_color: 1, 0.8, 0.2, 1
            color: 0, 0, 0, 1
            on_release: root.create_group()
        Button:
            text: "CANCEL"
            size_hint_y: None
            height: "50dp"
            background_normal: ""
            background_color: 0.1, 0.1, 0.1, 1
            color: 1, 1, 1, 1
            on_release: root.manager.current = "home"

<HomeScreen>:
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgb: 0.03, 0.03, 0.03
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: "60dp"
            padding: "10dp"
            Label:
                text: "ALMA X"
                font_size: "22sp"
                bold: True
                color: 0, 1, 0.35, 1
            Button:
                text: "PROFILE"
                size_hint_x: None
                width: "80dp"
                background_normal: ""
                background_color: 0.1, 0.1, 0.1, 1
                color: 0, 1, 0.35, 1
                on_release: app.root.current = "profile"
        BoxLayout:
            size_hint_y: None
            height: "50dp"
            padding: "6dp"
            spacing: "6dp"
            TextInput:
                id: search
                hint_text: "Search by username..."
                multiline: False
            Button:
                text: "SEARCH"
                size_hint_x: None
                width: "80dp"
                background_normal: ""
                background_color: 0, 1, 0.35, 1
                color: 0, 0, 0, 1
                on_release: root.search_users()
        BoxLayout:
            size_hint_y: None
            height: "50dp"
            padding: "6dp"
            Button:
                text: "+ CREATE NEW GROUP"
                background_normal: ""
                background_color: 0.1, 0.1, 0.1, 1
                color: 1, 0.8, 0.2, 1
                on_release: root.manager.current = "create_group"
        ScrollView:
            do_scroll_x: False
            GridLayout:
                id: results
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: "8dp"
                spacing: "6dp"

<ChatScreen>:
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgb: 0.03, 0.03, 0.03
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: "65dp"
            padding: "6dp"
            spacing: "10dp"
            canvas.before:
                Color:
                    rgb: 0.08, 0.08, 0.08
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "<"
                size_hint_x: None
                width: "45dp"
                background_normal: ""
                background_color: 0, 0, 0, 0
                color: 0, 1, 0.35, 1
                font_size: "24sp"
                on_release: root.back_home()
            Label:
                id: friend_name
                text: "Chat"
                font_size: "18sp"
                color: 1, 1, 1, 1
                bold: True
                text_size: self.size
                halign: "left"
                valign: "middle"
        ScrollView:
            id: scroll_view
            do_scroll_x: False
            BoxLayout:
                id: messages
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: "8dp"
                padding: "10dp"
        BoxLayout:
            size_hint_y: None
            height: "55dp"
            padding: "6dp"
            spacing: "6dp"
            canvas.before:
                Color:
                    rgb: 0.06, 0.06, 0.06
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "📎"
                font_name: "DejaVuSans"
                size_hint_x: None
                width: "45dp"
                background_normal: ""
                background_color: 0.15, 0.15, 0.15, 1
                color: 0, 1, 0.35, 1
                font_size: "18sp"
                on_release: root.open_file_picker()
            TextInput:
                id: message
                hint_text: "Type a message..."
                multiline: False
            Button:
                text: "SEND"
                size_hint_x: None
                width: "70dp"
                background_normal: ""
                background_color: 0, 1, 0.35, 1
                color: 0, 0, 0, 1
                bold: True
                on_release: root.send_message()

<ProfileScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: "25dp"
        spacing: "15dp"
        canvas.before:
            Color:
                rgb: 0.03, 0.03, 0.03
            Rectangle:
                pos: self.pos
                size: self.size
        Button:
            size_hint_y: None
            height: "120dp"
            background_normal: ""
            background_color: 0,0,0,0
            on_release: root.choose_dp()
            AsyncImage:
                id: dp_image
                source: ""
                pos: self.parent.pos
                size: self.parent.size
                allow_stretch: True
        Label:
            id: display_name
            text: ""
            font_size: "22sp"
            bold: True
            color: 1, 1, 1, 1
            size_hint_y: None
            height: "40dp"
        Label:
            id: username
            text: ""
            color: 0.6, 0.6, 0.6, 1
            size_hint_y: None
            height: "30dp"
        Widget:
        Button:
            text: "BACK"
            size_hint_y: None
            height: "48dp"
            background_normal: ""
            background_color: 0, 1, 0.35, 1
            color: 0, 0, 0, 1
            on_release: root.manager.current = "home"
        Button:
            text: "LOGOUT"
            size_hint_y: None
            height: "48dp"
            background_normal: ""
            background_color: 0.15, 0.15, 0.15, 1
            color: 1, 0.3, 0.3, 1
            on_release: root.logout()
"""

# =========================================================
# APPLICATION ENTRY
# =========================================================
class AlmaXApp(App):
    current_user = None
    title = "Alma X"

    def build(self):
        return Builder.load_string(KV)

if __name__ == "__main__":
    AlmaXApp().run()
