"""Sections 3 & 4: session review dialog autocomplete and project selection."""

from app import stats
from app.session_review import SessionReviewDialog


def _complete(notes=None, tag=None, focus=None, project_id=None):
    stats.begin_session(planned_duration_seconds=1500, pomodoro_number=1)
    sid = stats.record_session()
    if any(v is not None for v in (notes, tag, focus, project_id)):
        stats.update_session(sid, notes, tag, focus, project_id=project_id)
    return sid


def test_first_session_has_no_prefill(tmp_config):
    sid = _complete()
    assert stats.last_review_today(sid) == (None, None, None, None)


def test_second_session_prefills_from_first(tmp_config):
    pid = stats.ensure_project("Thesis")
    first = _complete(notes="Testing autocomplete", tag="Coding", focus=4, project_id=pid)
    second = _complete()
    assert stats.last_review_today(second) == ("Testing autocomplete", "Coding", 4, pid)


def test_prefill_uses_most_recent_session(tmp_config):
    _complete(notes="First", tag="Reading", focus=3)
    second = _complete(notes="Second", tag="Coding", focus=5)
    third = _complete()
    assert stats.last_review_today(third)[:2] == ("Second", "Coding")


def test_dialog_applies_prefill(qtbot, tmp_config):
    dlg = SessionReviewDialog(
        prefill_notes="Testing autocomplete",
        prefill_tag="Coding",
        prefill_focus=4,
        projects=["Thesis", "App"],
        prefill_project="Thesis",
    )
    qtbot.addWidget(dlg)
    assert dlg._notes.text() == "Testing autocomplete"
    assert dlg._tag.currentText() == "Coding"
    assert dlg._focus_group.checkedId() == 4
    assert dlg._project.currentText() == "Thesis"


def test_skip_clears_next_prefill(tmp_config):
    _complete(notes="Saved", tag="Writing", focus=2)
    skipped = _complete()          # no review data
    next_sid = _complete()
    assert stats.last_review_today(next_sid) == (None, None, None, None)


def test_dialog_project_defaults_to_none(qtbot, tmp_config):
    dlg = SessionReviewDialog(projects=["Thesis"])
    qtbot.addWidget(dlg)
    assert dlg.project is None


def test_dialog_accepts_new_project_name(qtbot, tmp_config):
    dlg = SessionReviewDialog(projects=["Thesis"])
    qtbot.addWidget(dlg)
    dlg._project.setCurrentText("Brand new")
    assert dlg.project == "Brand new"


def test_update_session_links_project_from_review(tmp_config):
    sid = _complete()
    pid = stats.ensure_project("Thesis")
    stats.update_session(sid, notes=None, tag=None, focus_score=None, project_id=pid)
    assert stats.project_breakdown(None) == [("Thesis", 1)]


def test_update_session_can_clear_project(tmp_config):
    pid = stats.ensure_project("Thesis")
    stats.begin_session(planned_duration_seconds=1500, pomodoro_number=1, project_id=pid)
    sid = stats.record_session()

    # saving the review with no project unlinks the stamped one
    stats.update_session(sid, notes=None, tag=None, focus_score=None, project_id=None)
    assert stats.project_breakdown(None) == []
