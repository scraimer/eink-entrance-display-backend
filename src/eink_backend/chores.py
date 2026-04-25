"""
Chores data collection and rendering for e-ink display.

This module fetches chore data from the SQLite database via the API
and renders it as HTML for the e-ink display.
"""

from __future__ import print_function
import datetime
from dataclasses import dataclass
from datetime import date
import logging
from string import Template
import textwrap
import traceback
from typing import Any, Dict, List, Optional

from . import config, render


_logger: logging.Logger = logging.getLogger()


@dataclass
class Chore:
    due: date
    name: str
    assignee: str
    frequency_in_weeks: int


@dataclass
class ChoreData:
    chores: List[Chore]
    error: Optional[str] = None


@dataclass
class Assignee:
    name: str
    avatar: str


def get_chores_from_database() -> List["Chore"]:
    """Fetch chores directly from the database via build_chores_summary.

    Returns:
        List of Chore objects
    """
    from . import main as _main  # deferred to avoid circular import at module load
    from .chores_api import build_chores_summary

    db = _main.chores_db
    if db is None:
        _logger.error("Chores database not initialized")
        return []

    summary = build_chores_summary(db)

    # Build a person id→name lookup from the people table
    people_by_id: Dict[int, str] = {}
    session = db.get_session()
    try:
        from .chores_db import Person as _Person
        for person in session.query(_Person).all():
            people_by_id[person.id] = person.name
    finally:
        session.close()

    chores_list = []
    for chore_data in summary.get("chores", []):
        state = chore_data.get("state") or {}
        next_execution_date = state.get("next_execution_date")

        due = date.today()
        if next_execution_date:
            try:
                due = date.fromisoformat(next_execution_date)
            except (ValueError, TypeError):
                due = date.today()

        next_executor_id = state.get("next_executor_id")
        assignee = people_by_id.get(next_executor_id, "") if next_executor_id else ""

        chores_list.append(Chore(
            due=due,
            name=chore_data.get("name", ""),
            assignee=assignee,
            frequency_in_weeks=chore_data.get("frequency_in_weeks", 1),
        ))
        _logger.debug(f"Added record #{len(chores_list)}")

    return chores_list


EMPTY_CHORES = "-no chores data-"
API_ERROR = "-error getting chores from database API-"


def collect_data(now_utc: datetime) -> ChoreData:
    """Collect chores data from the database.
    
    Args:
        now_utc: Current UTC datetime
        
    Returns:
        ChoreData with chores list or error message
    """
    try:
        chores = get_chores_from_database()
    except Exception as ex:
        _logger.error(f"Exception {ex} in get_chores_from_database")
        _logger.error(traceback.format_exc())
        return ChoreData(chores=[], error=API_ERROR)
    if not chores:
        _logger.error("No chores found")
        return ChoreData(chores=[], error=EMPTY_CHORES)
    return ChoreData(chores=chores)


def normalize_assigneed(raw_assignee: str) -> Optional[Assignee]:
    first_name = raw_assignee.split(" ")[0].lower()
    DEFAULT = "DEFAULT"
    TABLE = {
        "ariel": Assignee(name="Ariel", avatar="ariel.png"),
        "asaf": Assignee(name="Asaf", avatar="asaf.png"),
        "amalya": Assignee(name="Amalya", avatar="amalya.png"),
        "alon": Assignee(name="Alon", avatar="alon.png"),
        "aviv": Assignee(name="Aviv", avatar="aviv.png"),
        DEFAULT: Assignee(name="Other", avatar="other.png"),
    }
    if first_name in TABLE:
        return TABLE[first_name]
    else:
        return TABLE[DEFAULT]


def render_chores(chores: List[Chore], now_utc: datetime, color: str) -> str:
    # Sort the chores:
    # - unassigned items are last
    # - by assignee name
    # - sort by how often (more often, i.e. lower between weeks is sooner)
    chores.sort(key=lambda c: (not c.assignee, c.assignee, c.frequency_in_weeks))

    chore_template = Template(
        textwrap.dedent(
            """\
        <li class="chore$extra_classes">
            <ul>
                <li class="avatar">$avatar_img</li>
                <li class="black name">$name</li>
                <li class="black assignee">$assignee</li>
            </ul>
        </li>"""
        )
    )

    today = now_utc.date()
    chores_str = ""
    for chore in chores:
        if chore.due > today:
            # print("SKIPPING item in the future: " + str(chore))
            continue

        extra_classes = ""
        avatar_img = ""
        if chore.assignee:
            assignee = normalize_assigneed(chore.assignee)
            extra_classes += f" assigned"
            if assignee and assignee.avatar:
                avatar_url = f"file:///app/assets/avatars/joined/{assignee.avatar}"
                avatar_url = render.image_extract_color_channel(
                    img_url=avatar_url, color=color
                )
                avatar_img = f'<img src="{avatar_url}" />'
        chore_out = {
            "assignee": chore.assignee,
            "name": chore.name,
            "extra_classes": extra_classes,
            "avatar_img": avatar_img,
        }
        chores_str += "\n" + textwrap.indent(
            chore_template.substitute(chore_out),
            prefix=render.INDENT,
        )

    outer_template = Template(
        textwrap.dedent(
            f"""\
            <ul class="chores">
            $x
            </ul>
            """
        )
    )

    out_str = outer_template.substitute(x=chores_str)
    return out_str


# python3 -m eink_backend.chores
if __name__ == "__main__":
    # out = collect_data(now_utc=datetime.datetime(year=2023, month=12, day=15, hour=10, minute=00))
    out = collect_data(now_utc=datetime.datetime.now())
    print(out)
