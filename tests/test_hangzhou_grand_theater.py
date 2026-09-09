import unittest
from unittest.mock import patch

from scripts import scrape


INDEX_HTML = """
<article>
  <a href="https://www.douban.com/event/38026360/">1+1≥2 钢琴的传奇之旅—迈克·彼亚克独奏音乐会</a>
  <p>演出时间: 2026.11.27 周五 19:30</p>
  <p>地点: 杭州大剧院-音乐厅</p>
</article>
<article>
  <a href="https://www.douban.com/event/38000000/">某音乐剧</a>
  <p>演出时间: 2026.11.28 周六 19:30</p>
  <p>地点: 杭州大剧院-歌剧院</p>
</article>
"""


class HangzhouGrandTheaterSupplementTests(unittest.TestCase):
    def test_douban_page_keeps_concert_and_metadata(self):
        events = scrape.parse_douban_music_page(
            "杭州大剧院",
            "https://www.douban.com/location/hangzhou/events/future-music",
            INDEX_HTML,
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["date"], "2026-11-27")
        self.assertEqual(events[0]["startTime"], "19:30")
        self.assertEqual(events[0]["theater"], "杭州大剧院")
        self.assertEqual(
            events[0]["source"],
            "https://www.douban.com/event/38026360/",
        )

    @patch.object(scrape, "scrape_douban_music", return_value=[])
    @patch.object(scrape, "scrape_localhub_venue", return_value=[])
    def test_verified_missing_events_are_always_present(self, _localhub, _index):
        events = scrape.scrape_hangzhou_grand_theater()
        by_date = {event["date"]: event for event in events}

        self.assertIn("2026-11-20", by_date)
        self.assertIn("2026-11-27", by_date)
        self.assertEqual(by_date["2026-11-27"]["durationMinutes"], 120)


if __name__ == "__main__":
    unittest.main()
