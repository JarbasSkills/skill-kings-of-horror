from mycroft.skills.core import intent_file_handler
from pyvod import Collection, Media
from os.path import join, dirname, basename
from ovos_workshop.frameworks.playback import CPSMatchType, CPSPlayback, \
    CPSMatchConfidence
from ovos_workshop.skills.video_collection import VideoCollectionSkill


class KingsofHorrorSkill(VideoCollectionSkill):
    def __init__(self):
        super().__init__("KingsofHorror")
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.MOVIE,
                                CPSMatchType.VIDEO]
        self.message_namespace = basename(dirname(__file__)) + ".jarbasskills"
        # load video catalog
        path = join(dirname(__file__), "res", "KingsofHorror.jsondb")
        self.skill_logo = join(dirname(__file__), "ui", "logo.png")
        self.media_collection = Collection("KingsofHorror",
                                           logo=self.skill_logo,
                                           db_path=path)
        self.default_image = join(dirname(__file__), "ui", "logo.png")
        self.skill_icon = join(dirname(__file__), "ui", "logo.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.jpg")
        self.playback_type = CPSPlayback.GUI
        self.media_type = CPSMatchType.MOVIE

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
                  if v.get("duration") or 0 > 50 * 60 and
                  "full" in v["title"].lower()]

        # filter Directors Commentary
        videos = [v for v in videos
                  if "commentary" not in v["title"].lower()]

        return videos

    # matching
    def match_media_type(self, phrase, media_type):
        score = 0

        if self.voc_match(phrase, "video") or media_type == CPSMatchType.VIDEO:
            score += 5

        if self.voc_match(phrase, "horror"):
            score += 20
            if self.voc_match(phrase, "indie"):
                score += 20

        if self.voc_match(phrase, "indie"):
            score += 10

        if self.voc_match(phrase, "movie") or media_type == CPSMatchType.MOVIE:
            score += 30

        if self.voc_match(phrase, "kings-of-horror"):
            score += 60

        return score

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



def create_skill():
    return KingsofHorrorSkill()
