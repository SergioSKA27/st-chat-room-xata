import streamlit as st
from st_xatadb_connection import XataConnection
import bcrypt

st.set_page_config(page_title="Xata Demo",page_icon="🦋",layout="wide")
# Set the connection to the database
xata = st.connection('xata', type=XataConnection)

# Set the title of the app
st.title("Xata Demo")
st.subheader("Chat Room with Xata and Streamlit")
st.divider()
# Set the variables for the app
if 'login_status' not in st.session_state:
    #we can use this to check if the user is logged in or not
    st.session_state.login_status = False

if 'username' not in st.session_state:
    #we can use this to check the username of the user
    st.session_state.username = None

if 'view' not in st.session_state:
    st.session_state.view = None

if 'chat' not in st.session_state or st.session_state.chat is None:
    #this stores the chat
    try:
        st.session_state.chat = xata.query("comments",{"page": {"size": 10},
        "sort": {"xata.createdAt": "desc"}
        })
    except Exception as e:
        st.error(e)
        st.session_state.chat = []

if 'chatmessage' not in st.session_state:
    st.session_state.chatmessage = None

def update_chat():
    #this updates the chat to get the latest messages
    try:
        st.session_state.chat = xata.query("comments",{"page": {"size": 10},
        "sort": {"xata.createdAt": "desc"}
        })
    except Exception as e:
        st.session_state.chat = []

def add_comment():
    #this adds the comment to the database
    if st.session_state.chatmessage is not None and st.session_state.chatmessage != "":
        try:
            xata.insert("comments",{"user":st.session_state.username,"comment":st.session_state.chatmessage})

        except Exception as e:
            st.error("Something went wrong try again")
            st.write(e)

def login():
    st.title("Login")
    #this is the login form
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
                    #this means that the user does not exist
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
        password2 = st.text_input("Confirm Password", type='password')

        submit_button = st.form_submit_button(label='Register')

        if submit_button and username != "" and password != "":
            username = username.strip()
            password = password.strip()
            password2 = password2.strip()
            if password == password2:
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
            else:
                st.error("Passwords do not match")


def chat_room(loged: bool = False):

    def read_chat():
        for i in st.session_state.chat['records'][::-1]:
            with st.chat_message("user",avatar="🦋"):
                st.write(":blue[user] : " + i['user']['id'])
                st.write(i['comment'])
                st.write(i['xata']['createdAt'][:19])

    st.title("Chat Room")
    read_chat()
    cols = st.columns([0.2,0.3,0.3,0.2])
    if cols[1].button("Previous"):
        st.session_state.chat = xata.prev_page("comments",st.session_state.chat,pagesize=10)
        st.rerun()
    if cols[2].button("Next"):
        st.session_state.chat = xata.next_page("comments",st.session_state.chat,pagesize=10)
        st.rerun()
    if cols[3].button("Refresh"):
        update_chat()
        st.rerun()


    chat_input = st.chat_input("Type here",key="chat_input",max_chars=250,disabled=not loged)
    if chat_input:
        st.session_state.chatmessage = chat_input
        add_comment()
        update_chat()
        st.rerun()

def app():
    if st.session_state.login_status:
        st.title("Welcome")
        if st.button("Logout"):
            st.session_state.login_status = False
            st.session_state.username = None
            st.rerun()
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
