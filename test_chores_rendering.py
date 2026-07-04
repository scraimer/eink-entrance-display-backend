from datetime import datetime, date, timezone

from eink_backend.chores import Chore, render_chores


def test_render_chores_sorts_by_assignee_ordinal_and_frequency():
    chores = [
        Chore(
            due=date.today(),
            name="Chore A",
            assignee="Ariel",
            assignee_avatar="ariel.png",
            assignee_ordinal=3,
            frequency_in_weeks=1,
        ),
        Chore(
            due=date.today(),
            name="Chore B",
            assignee="Asaf",
            assignee_avatar="asaf.png",
            assignee_ordinal=1,
            frequency_in_weeks=4,
        ),
        Chore(
            due=date.today(),
            name="Chore C",
            assignee="",
            assignee_avatar="",
            assignee_ordinal=10**9,
            frequency_in_weeks=1,
        ),
        Chore(
            due=date.today(),
            name="Chore D",
            assignee="Aviv",
            assignee_avatar="aviv.png",
            assignee_ordinal=1,
            frequency_in_weeks=2,
        ),
    ]

    output = render_chores(chores, datetime.now(timezone.utc), color="black")

    assert output.index("Chore D") < output.index("Chore B")
    assert output.index("Chore B") < output.index("Chore A")
    assert output.index("Chore A") < output.index("Chore C")


def test_render_chores_uses_assignee_avatar_from_db():
    chores = [
        Chore(
            due=date.today(),
            name="Chore X",
            assignee="Ariel",
            assignee_avatar="ariel.png",
            assignee_ordinal=1,
            frequency_in_weeks=1,
        )
    ]

    output = render_chores(chores, datetime.now(timezone.utc), color="black")
    assert '<img src="' in output
    assert "Chore X" in output
