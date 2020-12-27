from ovos_utils.skills.templates.media_collection import MediaCollectionSkill
from ovos_utils.waiting_for_mycroft.common_play import CommonPlaySkill, \
    CPSMatchLevel, CPSTrackStatus, CPSMatchType
from mycroft.skills.core import intent_file_handler
from mycroft.util.parse import fuzzy_match, match_one
from pyvod import Collection, Media
from os.path import join, dirname, basename
import random
import re
from json_database import JsonStorageXDG
import datetime


class KingsofHorrorSkill(MediaCollectionSkill):
    def __init__(self):
        super().__init__("KingsofHorror")
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.MOVIE,
                                CPSMatchType.VIDEO]
        self.message_namespace = basename(dirname(__file__)) + ".jarbasskills"
        # load video catalog
        path = join(dirname(__file__), "res", "KingsofHorror.jsondb")
        logo = join(dirname(__file__), "res", "kings_of_horror_logo.png"),
        self.media_collection = Collection("KingsofHorror", logo=logo,
                                           db_path=path)

    # voice interaction
    def get_intro_message(self):
        self.speak_dialog("intro")

    @intent_file_handler('home.intent')
    def handle_homescreen_utterance(self, message):
        self.handle_homescreen(message)

    # homescreen / menu
    def sort_videos(self, videos):
        videos = super(KingsofHorrorSkill, self).sort_videos(videos)

        # filter only full movies
        videos = [v for v in videos
                  if v.get("duration", 0) > 50 * 60 and
                  "full" in v["title"].lower()]

        # filter Directors Commentary
        videos = [v for v in videos
                  if "commentary" not in v["title"].lower()]

        return videos

    # matching
    def match_media_type(self, phrase, media_type):
        match = None
        score = 0

        if self.voc_match(phrase,
                          "video") or media_type == CPSMatchType.VIDEO:
            score += 0.05
            match = CPSMatchLevel.GENERIC

        if self.voc_match(phrase, "horror"):
            score += 0.1
            match = CPSMatchLevel.CATEGORY

        if self.voc_match(phrase,
                          "movie") or media_type == CPSMatchType.MOVIE:
            score += 0.1
            match = CPSMatchLevel.CATEGORY

        if self.voc_match(phrase, "kings-of-horror"):
            score += 0.3
            match = CPSMatchLevel.TITLE

        return match, score

    def normalize_title(self, title):
        title = title.lower().strip()
        title = self.remove_voc(title, "kings-of-horror")
        title = self.remove_voc(title, "movie")
        title = self.remove_voc(title, "video")
        title = self.remove_voc(title, "horror")
        title = title.replace("|", "").replace('"', "") \
            .replace(':', "").replace('”', "").replace('“', "") \
            .strip()
        return " ".join([w for w in title.split(" ") if w])

        # common play

    def calc_final_score(self, phrase, base_score, match_level):
        score = base_score

        if self.voc_match(phrase, "kings-of-horror"):
            score += 0.15
        if self.voc_match(phrase, "movie"):
            score += 0.05  # bonus for films
        if self.voc_match(phrase, "horror"):
            score += 0.05  # bonus for horror films

        return score


def create_skill():
    return KingsofHorrorSkill()
