from youtube_archivist import YoutubeMonitor
import shutil
import json
from os.path import dirname, isfile

url = "https://www.youtube.com/user/TheKingsofHorror"
blacklisted_kwords = ["trailer", "teaser", "movie scene",
                      "movie clip", "behind the scenes", "Announcing the Winners!",
                      "Cult Clips", "Movie Preview", "Low Budget Binge", "Live", "interview", "filmmaker",
                      "Review", "Fight Scene", "KILLER CREATURES |", "Danny Draven's MASTERS OF TERROR",
                      "Kings of Horror Live", " | MUSIC VIDEO", "Weekly Update LIVE"]
archive = YoutubeMonitor("TheKingsofHorror",
                              min_duration=30 * 60,
                              blacklisted_kwords=blacklisted_kwords)
# load previous cache
cache_file = f"{dirname(dirname(__file__))}/bootstrap.json"
if isfile(cache_file):
    try:
        with open(cache_file) as f:
            data = json.load(f)
            archive.db.update(data)
            archive.db.store()
    except:
        pass  # corrupted for some reason

    shutil.rmtree(cache_file, ignore_errors=True)


# parse new vids
archive.parse_videos(url)

# save bootstrap cache
shutil.copy(archive.db.path, cache_file)
