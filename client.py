"""
Simple chatroom client.

This script connects to a small chat server to sign up, log in, poll for messages,
and send messages. It's written in a straightforward way so a student can read
and understand it easily.
"""

import requests
import threading
import time

SERVER = "http://127.0.0.1:5500"

def choose_signup_or_login():
    """Ask the user to choose signup or login and return the choice.
    Keeps asking until the user enters 1 (signup) or 2 (login).
    """
    while True:
        print("Choose: 1 SIGNUP")
        print("Choose: 2 LOG IN")
        try:
            option = int(input("Enter your choice >"))
        except ValueError:
            print("Please enter 1 or 2.")
            continue
        if option == 1:
            return "signup"
        if option == 2:
            return "login"

def signup():
    """Collect username, email and password and call the server to create user.
    Returns (username, email, password) on success, or (None, None, None) on fail.
    """
    print("---- Sign-Up ----")
    username = input("Choose username: ").strip()
    email = input("Enter Email: ").strip()
    passw = input("Create Password: ").strip()

    if not username or not passw or not email:
        print("All fields are required!")
        return None, None, None
    
    try:
        r = requests.post(f"{SERVER}/sinup", json={"username": username, "email": email, "password": passw}, timeout=5)
    except Exception as e:
        print("Request error:", e)
        return None, None, None
    
    # -- printing the created user if status = OK
    if r.status_code in (200, 201):
        data = r.json()
        # server returns {"status":"registered","username":..., "email":...}
        print("Registered:", data)
        # Use returned username/email and the password we just created
        return data.get("username"), data.get("email"), passw
    
    else:
        try:
            print("Signup failed:", r.status_code, r.json())
        except Exception:
            print("Signup failed:", r.status_code, r.text)
        return None, None, None


def login():
    """Ask for email and password, call server to login.
    Returns (username, email, password) on success, or (None, None, None) on fail.
    """
    print("---- Log In ----")
    email = input("Enter Email: ").strip()
    passw = input("Enter Password: ").strip()

    if  not passw or not email:
        print("All fields are required!")
        return None, None, None
    
    try:
        r = requests.post(f"{SERVER}/login", json={"email": email, "password": passw}, timeout=5)
    except Exception as e:
        print("Request error:", e)
        return None, None, None
    
    # -- printing the loged user if status = OK
    if r.status_code == 200:
        data = r.json()
        username = data.get("username")
        print(f"Logged in as {username} ({email})")
        return username, email, passw
    else:
        try:
            print("Login failed:", r.status_code, r.json())
        except Exception:
            print("Login failed:", r.status_code, r.text)
        return None, None, None

def poll_loop(user_name):
    """Background loop that asks server for new messages for this username.
    It keeps polling and prints any new messages to the console.
    """
    last_id = None
    while True:
        params = {"username": user_name}
        if last_id:
            params["since"] = last_id
        try:
            r = requests.get(f"{SERVER}/poll", params=params, timeout=10)
            if r.status_code == 200:
                msgs = r.json().get("messages", [])
                for m in msgs:
                    print(f"\n[{m['id']}] {m['created_at']} {m['username']}: {m['message']}")
                    last_id = m["id"]
            else:
                # print server-side error but keep polling
                try:
                    print("Poll error:", r.status_code, r.json())
                except Exception:
                    print("Poll error:", r.status_code, r.text)
        except Exception as e:
            print("Poll exception:", e)
        time.sleep(1)

def send_message_flow(email, password, text):
    """Send one message to server using email/password auth.
    Prints an error if sending fails.
    """
    try:
        r = requests.post(f"{SERVER}/send", json={"email": email, "password": password, "message": text}, timeout=5)
    except Exception as e:
        print("Send request error:", e)
        return

    if r.status_code == 201:
        # message sent
        return
    else:
        try:
            print("Send failed:", r.status_code, r.json())
        except Exception:
            print("Send failed:", r.status_code, r.text)

def main():
    """Main program flow: choose, signup/login, then start poll and read user input.

    After successful login/signup this starts a background thread for polling and
    then allows the user to type messages to send.
    """
    action = choose_signup_or_login()
    username = None
    email = None
    passw = None

    if action == "signup":
        username, email, passw = signup()
        if not username:
            # signup failed — fall back to login attempt
            action = "login"

    if action == "login":
        while not username:
            username, email, passw = login()


    # safety check: ensure username is set before starting poll
    if not username:
        print("ERROR: username missing after signup/login")
        return
    # start polling thread (uses username)
    poll_thread = threading.Thread(target=poll_loop, args=(username,), daemon=True)
    poll_thread.start() 

    print("You can now type messages. Press Ctrl+C to exit.")
    try:
        while True:
            line = input()
            if not line.strip():
                continue
            send_message_flow(email, passw, line.strip())
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()