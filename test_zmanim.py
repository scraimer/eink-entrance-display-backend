from datetime import datetime
import textwrap
from pytest import TempdirFactory
import shul_zmanim


def test_find_shabbat_from_weekday():
    json = textwrap.dedent(
        """\
        [
            {
                "gregorian_date": "2023-04-01",
                "name": "\u05e6\u05d5-\u05e9\u05d1\u05ea \u05d4\u05d2\u05d3\u05d5\u05dc",
                "hebrew_date": "\u05d9' \u05e0\u05d9\u05e1\u05df",
                "candle_lighting": "18:40",
                "tzet_shabat": "19:34",
                "all_fields": {
                    "f_00": "1 \u05d0\u05e4\u05e8\u05f3 23",
                    "f_01": "\u05e6\u05d5-\u05e9\u05d1\u05ea \u05d4\u05d2\u05d3\u05d5\u05dc",
                    "f_02": "\u05d9' \u05e0\u05d9\u05e1\u05df",
                    "f_03": "18:40",
                    "f_04": "04:54",
                    "f_05": "06:26",
                    "f_06": "13:13",
                    "f_07": "08:59",
                    "f_08": "09:36",
                    "f_09": "19:00",
                    "f_10": "19:34",
                    "f_11": "",
                    "f_12": ""
                }
            },
            {
                "gregorian_date": "2023-04-06",
                "name": "\u05e4\u05e1\u05d7",
                "hebrew_date": "\u05d8\\"\u05d5 \u05e0\u05d9\u05e1\u05df",
                "candle_lighting": "18:43",
                "tzet_shabat": "19:39",
                "all_fields": {
                    "f_00": "6 \u05d0\u05e4\u05e8\u05f3 23",
                    "f_01": "\u05e4\u05e1\u05d7",
                    "f_02": "\u05d8\\"\u05d5 \u05e0\u05d9\u05e1\u05df",
                    "f_03": "18:43",
                    "f_04": "04:47",
                    "f_05": "06:19",
                    "f_06": "13:12",
                    "f_07": "08:55",
                    "f_08": "09:32",
                    "f_09": "19:03",
                    "f_10": "19:39",
                    "f_11": "",
                    "f_12": ""
                }
            },
            {
                "gregorian_date": "2023-04-08",
                "name": "\u05e9\u05d1\u05ea \u05d7\u05d5\u05dc \u05d4\u05de\u05d5\u05e2\u05d3",
                "hebrew_date": "\u05d9\\"\u05d6 \u05e0\u05d9\u05e1\u05df",
                "candle_lighting": "18:44",
                "tzet_shabat": "19:39",
                "all_fields": {
                    "f_00": "8 \u05d0\u05e4\u05e8\u05f3 23",
                    "f_01": "\u05e9\u05d1\u05ea \u05d7\u05d5\u05dc \u05d4\u05de\u05d5\u05e2\u05d3",
                    "f_02": "\u05d9\\"\u05d6 \u05e0\u05d9\u05e1\u05df",
                    "f_03": "18:44",
                    "f_04": "04:44",
                    "f_05": "06:17",
                    "f_06": "13:12",
                    "f_07": "08:54",
                    "f_08": "09:30",
                    "f_09": "19:05",
                    "f_10": "19:39",
                    "f_11": "",
                    "f_12": ""
                }
            },
            {
                "gregorian_date": "2023-04-12",
                "name": "\u05e9\u05d1\u05d9\u05e2\u05d9 \u05e9\u05dc \u05e4\u05e1\u05d7",
                "hebrew_date": "\u05db\\"\u05d0 \u05e0\u05d9\u05e1\u05df",
                "candle_lighting": "18:47",
                "tzet_shabat": "19:43",
                "all_fields": {
                    "f_00": "12 \u05d0\u05e4\u05e8\u05f3 23",
                    "f_01": "\u05e9\u05d1\u05d9\u05e2\u05d9 \u05e9\u05dc \u05e4\u05e1\u05d7",
                    "f_02": "\u05db\\"\u05d0 \u05e0\u05d9\u05e1\u05df",
                    "f_03": "18:47",
                    "f_04": "04:38",
                    "f_05": "06:12",
                    "f_06": "13:11",
                    "f_07": "08:50",
                    "f_08": "09:27",
                    "f_09": "19:07",
                    "f_10": "19:43",
                    "f_11": "",
                    "f_12": ""
                }
            }
        ]"""
    )

    # Check the chol-hamoed shabbat in pesach
    z1 = shul_zmanim.collect_data(now=datetime(year=2023, month=4, day=7), db_json=json)
    assert (
        z1.name
        == "\u05e9\u05d1\u05ea \u05d7\u05d5\u05dc \u05d4\u05de\u05d5\u05e2\u05d3"
    )
    assert z1.times["candle_lighting"] == "18:44"
    assert z1.times["tzet_shabat"] == "19:39"

    # TODO: This doesn't work as of this writing.
    # Check the first Yom Tov of Pesach
    # z2 = shul_zmanim.collect_data(now=datetime(year=2023, month=4, day=5), db_json=json)
    # assert z2.name == "\u05e4\u05e1\u05d7"
    # assert z2.times["candle_lighting"] == "18:43"
    # assert z2.times["tzet_shabat"] == "19:39"


if __name__ == "__main__":
    test_find_shabbat_from_weekday()
