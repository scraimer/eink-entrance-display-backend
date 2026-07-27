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


UNASSIGNED_ORDINAL = 10**9


def _plan_date_from_utc(now_utc: datetime.datetime) -> str:
    """Return the local plan date for a UTC timestamp."""
    local_date = now_utc.astimezone(config.LOCAL_TZ).date()
    return local_date.isoformat()


@dataclass
class Chore:
    due: date
    name: str
    assignee: str
    assignee_avatar: str
    assignee_ordinal: int
    frequency_in_weeks: int


@dataclass
class ChoreData:
    chores: List[Chore]
    error: Optional[str] = None


def _chores_from_summary(summary: dict[str, list[dict[str, Any]]]) -> List["Chore"]:
    # Build a person id→metadata lookup from the people table
    from .chores_db import Person as _Person

    from . import main as _main  # deferred to avoid circular import at module load
    db = _main.chores_db
    if db is None:
        _logger.error("Chores database not initialized")
        return []

    people_by_id: Dict[int, Dict[str, Any]] = {}
    session = db.get_session()
    try:
        for person in session.query(_Person).all():
            people_by_id[person.id] = {
                "name": person.name,
                "avatar": person.avatar,
                "ordinal": person.ordinal,
            }
    finally:
        session.close()

    chores_list = []
    for chore_data in summary.get("chores", []):
        if chore_data.get("is_done"):
            continue
        state = chore_data.get("state") or {}
        next_execution_date = state.get("next_execution_date")

        due = date.today()
        if next_execution_date:
            try:
                due = date.fromisoformat(next_execution_date)
            except (ValueError, TypeError):
                due = date.today()

        next_executor_id = chore_data.get("next_executor_id")
        if chore_data.get("same_person_next_time"):
            next_executor_id = state.get("fixed_executor_id") or next_executor_id
        assignee = ""
        assignee_avatar = ""
        assignee_ordinal = UNASSIGNED_ORDINAL
        if next_executor_id:
            person = people_by_id.get(next_executor_id)
            if person:
                assignee = person["name"]
                assignee_avatar = person["avatar"]
                assignee_ordinal = person["ordinal"]

        chores_list.append(Chore(
            due=due,
            name=chore_data.get("name", ""),
            assignee=assignee,
            assignee_avatar=assignee_avatar,
            assignee_ordinal=assignee_ordinal,
            frequency_in_weeks=chore_data.get("frequency_in_weeks", 1),
        ))
        _logger.debug(f"Added record #{len(chores_list)}")

    return chores_list


def get_chores_from_database(plan_date: Optional[str] = None) -> List["Chore"]:
    """Fetch chores directly from the database via build_chores_summary.

    Args:
        plan_date: Optional plan date string to use for the persisted plan snapshot.

    Returns:
        List of Chore objects
    """
    from . import main as _main  # deferred to avoid circular import at module load
    from .chores_api import build_chores_summary

    db = _main.chores_db
    if db is None:
        _logger.error("Chores database not initialized")
        return []

    if plan_date is None:
        plan_date = _plan_date_from_utc(datetime.datetime.now(datetime.timezone.utc))

    summary = build_chores_summary(db, plan_date=plan_date)
    return _chores_from_summary(summary)


EMPTY_CHORES = "-no chores data-"
API_ERROR = "-error getting chores from database API-"


def collect_data(now_utc: datetime, force_refresh: bool = False) -> ChoreData:
    """Collect chores data from the database.
    
    Args:
        now_utc: Current UTC datetime
        force_refresh: Ignored for chores, included for API compatibility
        
    Returns:
        ChoreData with chores list or error message
    """
    plan_date = _plan_date_from_utc(now_utc)
    from .chores_api import build_chores_summary
    from . import main as _main  # deferred to avoid circular import at module load

    db = _main.chores_db
    if db is None:
        _logger.error("Chores database not initialized")
        return ChoreData(chores=[], error=API_ERROR)

    try:
        summary = build_chores_summary(db, plan_date=plan_date)
        chores = _chores_from_summary(summary)
    except Exception as ex:
        _logger.error(f"Exception {ex} in build_chores_summary")
        _logger.error(traceback.format_exc())
        return ChoreData(chores=[], error=API_ERROR)
    if not chores:
        _logger.error("No chores found")
        return ChoreData(chores=[], error=EMPTY_CHORES)
    return ChoreData(chores=chores)


def render_chores(chores: List[Chore], now_utc: datetime, color: str) -> str:
    # Sort the chores:
    # - unassigned items are last
    # - by the assignee's database ordinal
    # - sort by how often (more often, i.e. lower frequency_in_weeks is sooner)
    chores.sort(key=lambda c: (not c.assignee, c.assignee_ordinal, c.frequency_in_weeks))

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
            extra_classes += f" assigned"
            if chore.assignee_avatar:
                avatar_url = f"file:///app/assets/avatars/joined/{chore.assignee_avatar}"
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
