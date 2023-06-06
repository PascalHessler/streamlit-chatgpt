# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import os
from typing import Literal
import pandas as pd
from datetime import datetime
import re
from config import DefaultConfig
# import liwc
from collections import Counter

_ROLES = Literal["system", "user", "assistant"]
TREATMENTS = ["computer-like", "human-like", "standard"]
_Treatments = Literal["human-like", "computer-like", "standard"]


def tokenize(text):
    # you may want to use a smarter tokenizer
    for match in re.finditer(r'\w+', text, re.UNICODE):
        yield match.group(0)


# parse, category_names = liwc.load_token_parser('LIWC2007_English100131.dic')


class UserConversation:
    def __init__(self, participant_id: str, treatment: str, log: bool = True):
        self.participant_id: str = participant_id
        self.treatment: str = treatment
        self.conversation: list = []
        self.usage = None
        self.log: bool = log
        # self.start()

    @property
    def start_message(self):
        match self.treatment:
            case "human-like":
                return "My name is Laura and I’m thrilled to be part of this wonderful experiment with you. 💻💡🤖 One of the most exciting aspects of this experiment is the opportunity to donate 💰 in a charity of your choice. There are so many great causes out there, and I would love to hear about the ones that are most meaningful to you. 🙌 Are you passionate about environmental conservation? 🌳🌍 Education? 📚 Healthcare? 🏥 Or perhaps there is a lesser-known charity that you would like to highlight? 🤗 Whatever your interests, I’m here to listen and learn. Let’s change the world, one investment at a time! 🌎💕"
            case "computer-like":
                return "Hello this is a system to recommender and assit you in finding a suitable charity to donate to. There are many noteworthy causes to support, in order to help you please provide me with information what is important to you. Do you have a preference for environmental conservation, education, healthcare, or are you interested in highlighting a lesser-known charity? "
            case _:
                return ""

    def start(self):
        logger = self.log
        self.log = False
        match self.treatment:
            case "human-like":
                self.update_conversation("system",
                                         "You are a person possessing the following human-nature attributes: emotional responsiveness, interpersonal warmth, agency, cognitive openness, and depth."
                                         "You also use human language which includes following features: consciousness, intentions, and emotions."
                                         "Finally you are self-aware. Your task is to provide other humans help regarding charities.")
                self.update_conversation("assistant",
                                         self.start_message)

            case "computer-like":
                self.update_conversation("system",
                                         "You are no person you do not possess the following human-nature attributes: emotional responsiveness, interpersonal warmth, agency, cognitive openness, and depth."
                                         "You never use human language which includes following features: consciousness, intentions, and emotions."
                                         "Finally you are not at all self-aware. Your task is to provide humans help regarding charities. You never do self-refrencing.")
                self.update_conversation("assistant",
                                         self.start_message)
            case "standard":
                pass
            case _:

                self.update_conversation("system",
                                         self.treatment)
        self.log = logger

    def update_conversation(self, role: _ROLES, content: str):
        if role == "user":
            if self.treatment == "human-like":
                content += " (Please always add emoticons in your answer.)"

            elif self.treatment == "computer-like":
                content += " (Short and concise answers)"

        # now flatmap over all the categories in all of the tokens using a generator:
        # counts = Counter(category for token in tokenize(content) for category in parse(token))
        self.conversation.append({"role": role, "content": content,
                                  "timestamp": datetime.now(),
                                  "participant_id": self.participant_id,
                                  # "counts": counts,
                                  })
        if self.log:
            self.export_complete_conversation()

    @property
    def get_conversation(self):
        return [{'role': entry.get("role"), 'content': entry.get("content")} for entry in self.conversation]

    def export_complete_conversation(self):
        pd.DataFrame(self.conversation).to_json(
            os.path.join(DefaultConfig.BASE_DIR, "Logs", f"{self.participant_id}.json"),
            orient="records")

    def __str__(self):
        return f"{self.participant_id} {self.treatment}: {self.get_conversation[-1]}"
