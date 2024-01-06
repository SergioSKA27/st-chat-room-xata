import streamlit as st
from st_xatadb_connection import XataConnection
import bcrypt
xata = st.connection('xata', type=XataConnection)
if 'login_status' not in st.session_state:
    st.session_state.login_status = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'view' not in st.session_state:
    st.session_state.view = None
if 'chat' not in st.session_state:
    try:
        st.session_state.chat = xata.query("comments")['records']
    except Exception as e:
        st.error(e)
        st.session_state.chat = []
if 'chatmessage' not in st.session_state:
    st.session_state.chatmessage = None
def update_chat():
    try:
        st.session_state.chat = xata.query("comments")['records']
    except Exception as e:
        st.session_state.chat = []
def add_comment():
    if st.session_state.chatmessage is not None and st.session_state.chatmessage != "":
        try:
            result = xata.insert("comments",{"user":st.session_state.username,"comment":st.session_state.chatmessage})
            st.toast("Comment added",icon="😄")
            st.write(result)
        except Exception as e:
            st.error("Something went wrong try again")
            st.write(e)
def login():
    st.title("Login")
    with st.form(key='login_form'):
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        submit_button = st.form_submit_button(label='Login')
        if username != "" and password != "":
            user_info = None
            try:
                user_info = xata.get("Users",username)
            except Exception as e:
                if e.status_code == 404:
                    st.error("No users found")
        if submit_button:
            if user_info is not None:
                if bcrypt.checkpw(password.strip().encode(), user_info['password'].encode()):
                    st.toast("Logged in as {}".format(username),icon="😄")
                    st.session_state.login_status = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Incorrect password")
            else:
                st.error("No users found")
def user_register():
    st.title("Register")
    with st.form(key='register_form'):
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        submit_button = st.form_submit_button(label='Register')
        if submit_button and username != "" and password != "":
            try:
                xata.get("Users",username)
                st.error("User already exists")
            except Exception as e:
                if e.status_code == 404:
                    pass
            try:
                result = xata.insert("Users",{"username":username,
                "password":bcrypt.hashpw(password.strip().encode(), bcrypt.gensalt()).decode()},
                record_id=username,if_version=0)
                st.toast("User created",icon="😄")
                st.write(result)
            except Exception as e:
                    st.error("Something went wrong")
                    st.write(e)
def chat_room(loged: bool = False):
    def read_chat():
        for i in st.session_state.chat:
            with st.chat_message("user",avatar=""):
                st.write(":blue[user] : " + i['user']['id'])
                st.write(i['comment'])
                st.write(i['xata']['createdAt'])
    st.title("Chat Room")
    read_chat()

    chat_input = st.chat_input("Type here",key="chat_input",max_chars=100,disabled=not loged)
    if chat_input:
        st.session_state.chatmessage = chat_input
        add_comment()
        update_chat()
        st.rerun()
def app():
    if st.session_state.login_status:
        st.title("Welcome")
    else:
        if st.session_state.view is None:
            st.session_state.view = "login"
        if st.session_state.view == "login":
            login()
            if st.button("Register"):
                st.session_state.view = "register"
                st.rerun()
        elif st.session_state.view == "register":
            user_register()
            if st.button("Login"):
                st.session_state.view = "login"
                st.rerun()
    chat_room(st.session_state.login_status)
if __name__ == "__main__":
    app()
