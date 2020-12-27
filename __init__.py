from ovos_utils.waiting_for_mycroft.common_play import CommonPlaySkill, \
    CPSMatchLevel, CPSTrackStatus, CPSMatchType
from mycroft.skills.core import intent_file_handler
from mycroft.util.parse import fuzzy_match, match_one
from pyvod import Collection, Media
from os.path import join, dirname
import random
import re
from json_database import JsonStorageXDG
import datetime


def datestr2ts(datestr):
    y = int(datestr[:4])
    m = int(datestr[4:6])
    d = int(datestr[-2:])
    dt = datetime.datetime(y, m, d)
    return dt.timestamp()


class KingsofHorrorSkill(CommonPlaySkill):

    def __init__(self):
        super().__init__("KingsofHorror")
        if "max_videos" not in self.settings:
            self.settings["max_videos"] = 500
        if "min_duration" not in self.settings:
            self.settings["min_duration"] = 130
        if "max_duration" not in self.settings:
            self.settings["max_duration"] = -1
        if "shuffle_menu" not in self.settings:
            self.settings["shuffle_menu"] = False
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.MOVIE,
                                CPSMatchType.VIDEO]

        path = join(dirname(__file__), "res", "KingsofHorror.jsondb")
        # load video catalog
        videos = Collection("KingsofHorror",
                            logo=join(dirname(__file__), "res",
                                      "kings_of_horror_logo.png"),
                            db_path=path)
        self.videos = [ch.as_json() for ch in videos.entries]
        self.sort_videos()

    def initialize(self):
        self.add_event('skill-kings-of-horror.jarbasskills.home',
                       self.handle_homescreen)
        self.gui.register_handler(
            "skill-kings-of-horror.jarbasskills.play_event",
                                  self.play_video_event)
        self.gui.register_handler(
            "skill-kings-of-horror.jarbasskills.clear_history",
            self.handle_clear_history)

    # voice interaction
    def get_intro_message(self):
        self.speak_dialog("intro")

    @intent_file_handler('kings-of-horrorhome.intent')
    def handle_homescreen_utterance(self, message):
        self.handle_homescreen(message)

    # homescreen / menu
    def sort_videos(self):
        # this will filter private and live videos
        videos = [v for v in self.videos
                  if v.get("upload_date") and not v.get("is_live")]

        # filter only full movies
        videos = [v for v in videos
                  if v.get("duration", 0) > 50 * 60 and
                  "full" in v["title"].lower()]

        # filter Directors Commentary
        videos = [v for v in videos
                  if "commentary" not in v["title"].lower()]

        # sort by upload date
        videos = sorted(videos,
                             key=lambda kv: datestr2ts(kv["upload_date"]),
                             reverse=True)
        # live streams before videos
        self.videos =  [v for v in self.videos if v.get("is_live")] + videos

    def filter_videos(self):
        videos = self.videos
        # filter by duration
        videos = [v for v in videos if int(v.get("duration", 0)) >=
                  self.settings["min_duration"]]
        if self.settings["max_duration"] > 0:
            videos = [v for v in videos if int(v.get("duration", 0)) <=
                      self.settings["max_duration"]]

        # TODO filter behind the scenes, clips etc based on
        #  title/tags/description/keywords required or forbidden

        if self.settings["shuffle_menu"]:
            random.shuffle(videos)

        if self.settings["max_videos"]:
            # rendering takes forever if there are too many entries
            videos = videos[:self.settings["max_videos"]]

        return videos

    def handle_homescreen(self, message):
        self.gui.clear()
        self.gui["videosHomeModel"] = self.filter_videos()
        self.gui["historyModel"] = JsonStorageXDG("kings-of-horror-history")\
            .get("model", [])
        self.gui.show_page("Homescreen.qml", override_idle=True)

    def play_video_event(self, message):
        video_data = message.data["modelData"]
        self.play_video(video_data)

    # watch history database
    def add_to_history(self, video_data):
        # History
        historyDB = JsonStorageXDG("kings-of-horror-history")
        if "model" not in historyDB:
            historyDB["model"] = []
        historyDB["model"].append(video_data)
        historyDB.store()
        self.gui["historyModel"] = historyDB["model"]

    def handle_clear_history(self, message):
        historyDB = JsonStorageXDG("kings-of-horror-history")
        historyDB["model"] = []
        historyDB.store()

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

    def match_tags(self, video, phrase, match):
        score = 0
        # score tags
        leftover_text = phrase
        tags = list(set(video.get("tags") or []))
        if tags:
            # tag match bonus
            for tag in tags:
                tag = tag.lower().strip()
                if tag in phrase:
                    match = CPSMatchLevel.CATEGORY
                    score += 0.05
                    leftover_text = leftover_text.replace(tag, "")
        return match, score, leftover_text

    def match_description(self, video, phrase, match):
        # score description
        score = 0
        leftover_text = phrase
        words = video.get("description", "").split(" ")
        for word in words:
            if len(word) > 4 and word in self._clean_title(leftover_text):
                score += 0.05
                leftover_text = leftover_text.replace(word, "")
        return match, score, leftover_text

    def match_title(self, videos, phrase, match):
        # match video name
        clean_phrase = self._clean_title(phrase)
        leftover_text = phrase
        best_score = 0
        best_video = random.choice(videos)
        for video in videos:
            title = video["title"]
            clean_title = self._clean_title(title)
            score = fuzzy_match(clean_phrase, self._clean_title(title))
            if phrase.lower() in title.lower() or\
                    clean_phrase in clean_title:
                score += 0.3

            # word intersection bonus
            intersection = [x for x in phrase.lower().split(" ")
                            if x in clean_title.lower().split(" ")]
            if intersection:
                score += len(intersection) / len(clean_title.split(" "))

            if score >= best_score:
                match = CPSMatchLevel.TITLE
                best_video = video
                best_score = score
                leftover_text = phrase.replace(title, "")
        return match, best_score, best_video, leftover_text

    def remove_voc(self, utt, voc_filename, lang=None):
        lang = lang or self.lang
        cache_key = lang + voc_filename

        if cache_key not in self.voc_match_cache:
            # trigger caching
            self.voc_match(utt, voc_filename, lang)

        if utt:
            # Check for matches against complete words
            for i in self.voc_match_cache[cache_key]:
                # Substitute only whole words matching the token
                utt = re.sub(r'\b' + i + r"\b", "", utt)

        return utt

    def _clean_title(self, title):
        title = title.lower().strip()
        title = self.remove_voc(title, "kings-of-horror")
        title = self.remove_voc(title, "movie")
        title = self.remove_voc(title, "video")
        title = self.remove_voc(title, "horror")
        title = title.replace("|", "").replace('"', "") \
            .replace(':', "").replace('”', "").replace('“', "") \
            .strip()
        return " ".join([w for w in title.split(" ") if w]) # remove extra
        # spaces

    # common play
    def CPS_match_query_phrase(self, phrase, media_type):
        best_score = 0
        best_video = {"title": "No match"}
        # see if media type is in query, base_score will depend if "scifi"
        # or "video" is in query
        match, base_score = self.match_media_type(phrase, media_type)
        videos = list(self.videos)
        # match video data
        scores = []
        for video in videos:
            match, score, _ = self.match_tags(video, phrase, match)
            # match, score, leftover_text = self.match_description(video, leftover_text, match)
            scores.append((video, score))
            if score > best_score:
                best_video = video
                best_score = score

        self.log.debug("Best KingsofHorror Tags Match: {s}, {t}".format(
            s=best_score, t=best_video["title"]))

        # match video name
        match, title_score, best_title, leftover_text = self.match_title(
            videos, phrase, match)
        self.log.debug("Best KingsofHorror Title Match: {s}, {t}".format(
            s=title_score, t=best_title["title"]))

        # title more important than tags
        if title_score + 0.15 > best_score:
            best_video = best_title
            best_score = title_score

        # sort matches
        scores = sorted(scores, key=lambda k: k[1], reverse=True)
        scores.insert(0, (best_title, title_score))
        scores.remove((best_video, best_score))
        scores.insert(0, (best_video, best_score))

        # choose from top N
        if best_score < 0.6:
            n = 50
        elif best_score < 0.7:
            n = 10
        elif best_score < 0.8:
            n = 3
        else:
            n = 1

        candidates = scores[:n]
        self.log.info("Choosing randomly from top {n} KingsofHorror matches".format(
            n=len(candidates)))
        best_video = random.choice(candidates)[0]

        # calc final confidence
        score = base_score + best_score

        if self.voc_match(phrase, "kings-of-horror"):
            score += 0.15
        if self.voc_match(phrase, "movie"):
            score += 0.05  # bonus for films
        if self.voc_match(phrase, "horror"):
            score += 0.05  # bonus for horror films

        if score >= 0.85:
            match = CPSMatchLevel.EXACT
        elif score >= 0.7:
            match = CPSMatchLevel.MULTI_KEY
        elif score >= 0.5:
            match = CPSMatchLevel.TITLE

        self.log.debug("Best KingsofHorror video: " + best_video["title"])

        if match is not None:
            return (leftover_text, match, best_video)
        return None

    def CPS_start(self, phrase, data):
        self.play_video(data)

    def play_video(self, video_data):
        # TODO audio only
        # if self.gui.connected:
        #    ...
        # else:
        #    self.audioservice.play(video_data["url"])
        # add to playback history

        self.add_to_history(video_data)
        # play video
        video = Media.from_json(video_data)
        url = str(video.streams[0])
        self.gui.play_video(url, video.name)


def create_skill():
    return KingsofHorrorSkill()
