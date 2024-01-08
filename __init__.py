import random
from os.path import join, dirname

import requests
from json_database import JsonStorageXDG

from ovos_utils.ocp import MediaType, PlaybackType
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class KingsofHorrorSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, **kwargs):
        self.supported_media = [MediaType.MOVIE]
        self.skill_icon = join(dirname(__file__), "ui", "logo.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.jpg")
        self.archive = JsonStorageXDG("TheKingsofHorror", subfolder="OCP")
        super().__init__(*args, **kwargs)

    def initialize(self):
        self._sync_db()
        self.load_ocp_keywords()

    def load_ocp_keywords(self):
        title = []
        genre = ["horror film", "horror movie", "indie",
                 "b movie",
                 "low budget movie",
                 "zombie movie", "monster movie", "classic horror",
                 "cheap scary movie",
                 "halloween movie",
                 "indie horror",
                 "scary film"]

        for url, data in self.archive.items():
            t = data["title"].split("📽️")[0].split("|")[0].split("(")[0].split(" KOH ")[0].split(" Full")[0].split(
                " FULL ")[0].split("FREE")[0].strip(" -.!🎁")
            if "exclusive" in t.lower() or "game" in t.lower() \
                    or "music" in t.lower() or "EP0" in data["title"]:
                continue

            else:
                title.append(t)

        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_name", title)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "film_genre", genre)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_streaming_provider",
                                  ["KingsofHorror", "Kings of Horror", "KOH"])

    def _sync_db(self):
        bootstrap = "https://github.com/JarbasSkills/skill-kings-of-horror/raw/dev/bootstrap.json"
        data = requests.get(bootstrap).json()
        self.archive.merge(data)
        self.schedule_event(self._sync_db, random.randint(3600, 24 * 3600))

    def get_playlist(self, num_entries=50):
        pl = self.featured_media()[:num_entries]
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
        base_score = 15 if media_type == MediaType.MOVIE else 0
        entities = self.ocp_voc_match(phrase)

        title = entities.get("movie_name")
        koh = "movie_streaming_provider" in entities  # skill matched

        base_score += 30 * len(entities)

        if title:
            candidates = [video for video in self.archive.values()
                          if title.lower() in video["title"].lower()]
            for video in candidates:
                yield {
                    "title": video["title"],
                    "author": video["author"],
                    "match_confidence": min(100, base_score),
                    "media_type": MediaType.MOVIE,
                    "uri": "youtube//" + video["url"],
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": self.default_bg
                }

            if koh:
                yield self.get_playlist()

        elif koh or len(entities) and media_type == MediaType.MOVIE or \
                len(entities) >= 2:
            yield self.get_playlist()

    @ocp_featured_media()
    def featured_media(self):
        return [{
            "title": video["title"],
            "image": video["thumbnail"],
            "match_confidence": 70,
            "media_type": MediaType.MOVIE,
            "uri": "youtube//" + video["url"],
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "bg_image": video["thumbnail"],
            "skill_id": self.skill_id
        } for video in self.archive.values()]


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = KingsofHorrorSkill(bus=FakeBus(), skill_id="t.fake")
    for r in s.search_db("Mrs. Claus", MediaType.MOVIE):
        print(r)
