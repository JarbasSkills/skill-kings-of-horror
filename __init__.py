import random
from os.path import join, dirname

from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.parse import fuzzy_match
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media
from youtube_archivist import YoutubeArchivist


class KingsofHorrorSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super().__init__("KingsofHorror")
        self.supported_media = [MediaType.GENERIC, MediaType.MOVIE]
        self.skill_icon = join(dirname(__file__), "ui", "logo.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.jpg")

        blacklisted_kwords = ["trailer", "teaser", "movie scene",
                              "movie clip", "behind the scenes", "Announcing the Winners!",
                              "Cult Clips", "Movie Preview", "Low Budget Binge", "Live", "interview", "filmmaker",
                              "Review", "Fight Scene", "KILLER CREATURES |", "Danny Draven's MASTERS OF TERROR",
                              "Kings of Horror Live", " | MUSIC VIDEO", "Weekly Update LIVE"]
        self.archive = YoutubeArchivist("TheKingsofHorror", blacklisted_kwords=blacklisted_kwords)

    def initialize(self):
        if len(self.archive.db):
            # update db sometime in the next 12 hours, randomized to avoid a huge network load every boot
            # (every skill updating at same time)
            self.schedule_event(self._scheduled_update, random.randint(3600, 12 * 3600))
        else:
            # no database, sync right away
            self.schedule_event(self._scheduled_update, 5)

    def _scheduled_update(self):
        self.update_db()
        self.schedule_event(self._scheduled_update, random.randint(3600, 12 * 3600))  # every 6 hours

    def update_db(self):
        url = "https://www.youtube.com/user/TheKingsofHorror"
        self.archive.archive_channel(url)
        self.archive.archive_channel_playlists(url)
        self.archive.remove_below_duration(30)  # 30 minutes minimum duration
        self.archive.remove_unavailable()  # check if video is still available

    # matching
    def match_skill(self, phrase, media_type):
        score = 0
        if self.voc_match(phrase, "horror"):
            score += 20
            if self.voc_match(phrase, "indie"):
                score += 10
        if self.voc_match(phrase, "movie") or media_type == MediaType.MOVIE:
            score += 10
        if self.voc_match(phrase, "kings-of-horror"):
            score += 40
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

    def calc_score(self, phrase, match, base_score=0):
        score = base_score
        score += 100 * fuzzy_match(phrase.lower(), match["title"].lower())
        return min(100, score)

    def get_playlist(self, num_entries=250):
        pl = [{
            "title": video["title"],
            "image": video["thumbnail"],
            "match_confidence": 70,
            "media_type": MediaType.MOVIE,
            "uri": "youtube//" + video["url"],
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "bg_image": video["thumbnail"],
            "skill_id": self.skill_id
        } for video in self.archive.sorted_entries()][:num_entries]
        return {
            "match_confidence": 90,
            "media_type": MediaType.MOVIE,
            "playlist": pl,
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "image": self.skill_icon,
            "bg_image": self.default_bg,
            "title": "Kings Of Horror (Movie Playlist)",
            "author": "KingsOfHorror"
        }

    @ocp_search()
    def search_db(self, phrase, media_type):
        if self.voc_match(phrase, "kings-of-horror"):
            yield self.get_playlist()
        if media_type == MediaType.MOVIE:
            # only search db if user explicitly requested movies
            base_score = self.match_skill(phrase, media_type)
            phrase = self.normalize_title(phrase)

            for url, video in self.archive.db.items():
                yield {
                    "title": video["title"],
                    "match_confidence": self.calc_score(phrase, video, base_score),
                    "media_type": MediaType.MOVIE,
                    "uri": "youtube//" + url,
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": self.default_bg,
                    "author": "Kings Of Horror"
                }

    @ocp_featured_media()
    def featured_media(self):
        return self.get_playlist()['playlist']


def create_skill():
    return KingsofHorrorSkill()
