import openai
import streamlit as st
import streamlit.errors as errors
from streamlit_chat import message
from conversation import UserConversation, TREATMENTS
from typing import Optional
import uuid
import pandas as pd
import os
from config import DefaultConfig

# url?prompt=1&participant=Pascal
# http://localhost:8501/?prompt=0&participant=Pascal
# http://localhost:8501/?prompt=1&participant=Pascal
# admin = True muss in die URL wenn admin view
#  pip install --upgrade --no-deps --force-reinstall git+https://github.com/PascalHessler/st-chat
# --- GENERAL SETTINGS ---
PAGE_TITLE: str = "Experiment"
PAGE_ICON: str = "🤖"


AI_MODEL_OPTIONS: list[str] = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4-32k",
]

openai.api_key = st.secrets["API_KEY"]
# st.experimental_get_query_params()

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)
with open("style.css", "r") as f:
    st.markdown(f"<style>{f.read()}</style)", unsafe_allow_html=True)


################################################
#            Functions
################################################
def get_open_ai():
    with container:
        # writing current prompt
        write_single_message({"role": "user", "content": st.session_state["user_input"]})
    # calling open ai
    generate_response(st.session_state["user_input"])
    # clearing input field
    st.session_state["user_input"] = ""
    # after this script will run again and trigger show history


def generate_response(prompt):
    st.session_state['conversation'].update_conversation("user", prompt)
    messages = st.session_state['conversation'].get_conversation
    try:
        if st.session_state["stream"]:
            st.session_state['conversation'].update_conversation("assistant", "")
            for chunk in openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=2048,
                    n=1,
                    stream=True,
                    temperature=0,
            ):
                # conversation.conversation[-1]["content"] += resp.choices[0].delta.content.strip().replace("\n", "")
                content = chunk["choices"][0]["delta"].get("content")
                if content is not None:
                    st.session_state['conversation'].conversation[-1]["content"] += content

        else:
            completions = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=2048,
                n=1,
                stream=False,
                temperature=0,  # todo ausprobieren 0 ist weniger random
            )
            st.session_state['conversation'].update_conversation("assistant",
                                                                 completions.choices[0].message.content.strip())

    except openai.error.RateLimitError as e:
        print("error")
        # todo should not happen!
        raise e


def show_chat():
    if st.session_state.get('conversation'):
        # [{'role': entry.get("role"), 'content': entry.get("content")} for entry in self.conversation]
        conv = st.session_state['conversation'].get_conversation
        for i, con in enumerate(reversed(conv)):
            write_single_message(con, i)


def write_single_message(content: dict, i: Optional = None):
    try:
        match content["role"]:
            case "system":
                return None
            case "assistant":
                message(content["content"],
                        logo="https://experiment.jlubwl12.de/media/Chatbot_Potrait/female_low.jpg",
                        key=f"{uuid.uuid1()}")
            case "user":
                message(content["content"].replace(" (Please always add emoticons in your answer.)", "").replace(
                    " (Short and concise answers)", ""), is_user=True, key=f"{uuid.uuid1()}"
                )
    except errors.DuplicateWidgetID:
        # hab ich mittlerweile gelöst, da jede Nachricht seine unique id bekommt
        print(f"error with {i}: {content['content']}")
        # write_single_message(i+1, content)
        pass


def export():
    def get_df(files):
        df = pd.concat((pd.read_json(os.path.join(path, file)) for file in files))
        return df.to_csv(index=False, sep=";").encode('utf-8')

    path = os.path.join(DefaultConfig.BASE_DIR, "Logs")
    all_files = [i for i in os.listdir(path) if i.endswith(".json")]
    if len(all_files) > 0:

        st.title("Download the logs:")
        st.download_button(
            "Logs",
            get_df(all_files),
            "logs.csv",
            "text/csv",
            key='download-csv'
        )
    else:
        st.write("No logs available yet!")


def get_participant_id() -> str:
    if st.session_state['admin'] is True:
        if "participant" in st.session_state:
            return st.session_state['participant']

    from_url = st.experimental_get_query_params().get("participant", [None])[0]
    if from_url:
        return from_url
    else:
        return uuid.uuid1().hex


def get_treatment() -> str:
    if st.session_state['admin'] is True:
        if "treatment" in st.session_state:
            return st.session_state['treatment']
    treatment = st.experimental_get_query_params().get("prompt", [None])[0]
    if treatment is not None:
        try:
            treatment = TREATMENTS[int(treatment)]
        except (ValueError, TypeError):
            pass
    else:
        # Default, wenn keine Info bekannt
        st.info("No treatment was given")
        treatment = "standard"
    return treatment


def get_logging() -> bool:
    if st.session_state['treatment'] == "standard":
        return False  # deactivate logging im standard case
    else:
        # Ansonsten wird die URl info verwendet, default ist True!
        return st.experimental_get_query_params().get("log", ["True"])[0].title() == "True"


def init_conversation() -> UserConversation:
    # todo eventuell alten Dialog einlesen?
    conv: UserConversation = UserConversation(
        participant_id=st.session_state['participant'],
        treatment=st.session_state['treatment'],
        log=st.session_state['logging'])
    conv.start()
    return conv


def reset_admin():
    print("reset")
    st.session_state['treatment'] = selected  # updated des Treatments
    st.session_state['participant'] = get_participant_id()
    st.session_state['logging'] = get_logging()
    st.session_state['conversation']: UserConversation = init_conversation()  # Setzt den Dialog zurück und setzt neuen


# Initialize
st.session_state['admin']: bool = st.experimental_get_query_params().get('admin', ['False'])[0].title() == "True"
st.session_state['participant']: str = get_participant_id()
st.session_state['treatment']: str = get_treatment()
st.session_state['logging']: bool = get_logging()

# möglichkeit url up zu daten
# st.experimental_set_query_params(
#     participant=st.session_state['participant'],
# )

if 'stream' not in st.session_state:
    st.session_state['stream']: bool = False

if "conversation" not in st.session_state:
    st.session_state['conversation']: UserConversation = init_conversation()

####################################################
# ------------    Actual website     -------------
####################################################

if st.session_state['admin'] is True:
    with st.sidebar:
        st.title("Admin area!")
        st.divider()

        selected = st.selectbox(label="Change the treatment:",
                                options=TREATMENTS[::-1],
                                )
        if selected != st.session_state['treatment']:
            # change only if treatment changed
            reset_admin()
        st.divider()
        st.metric(label="Participant", value=st.session_state['participant'])
        st.metric(label="Treatment", value=st.session_state['treatment'])
        st.metric(label="Logging", value=st.session_state['logging'])
        st.divider()
        export()

# st.header("Welcome to ")
if st.session_state['logging'] is False:
    st.info("Logging is disabled")
st.write("Your conversation:")

container = st.container()

with container:
    container = st.empty()  # not quite sure why but this is important in order that messages are show in the correct order when new message arrives
    show_chat()

user_input = st.text_input(label="You:", help="Type your message here.", key="user_input", on_change=get_open_ai)

