"""Projects table: CRUD, session linking, archiving, config migration, tab behaviour."""

import json
from unittest.mock import MagicMock

from PyQt6.QtGui import QIcon

from app import config, stats
from app.notifier import Notifier
from app.timer import PomodoroTimer
from app.window import MainWindow


def _record(project_id=None):
    stats.begin_session(planned_duration_seconds=1500, pomodoro_number=1, project_id=project_id)
    return stats.record_session()


def _window(qtbot, cfg):
    window = MainWindow(
        timer=PomodoroTimer(),
        icon=QIcon(),
        cfg=cfg,
        notifier=MagicMock(spec=Notifier),
    )
    qtbot.addWidget(window)
    window.show()
    return window


def test_ensure_project_creates_once(tmp_config):
    pid = stats.ensure_project("Thesis")
    assert stats.ensure_project("Thesis") == pid
    assert stats.list_projects() == [(pid, "Thesis", 0)]


def test_begin_session_links_project(tmp_config):
    pid = stats.ensure_project("Thesis")
    _record(project_id=pid)
    with stats._db() as conn:
        row = conn.execute("SELECT project_id FROM sessions").fetchone()
    assert row[0] == pid


def test_project_breakdown_joins_names(tmp_config):
    thesis = stats.ensure_project("Thesis")
    app_ = stats.ensure_project("App")
    _record(project_id=thesis)
    _record(project_id=thesis)
    _record(project_id=app_)
    _record()  # no project, excluded

    assert stats.project_breakdown(7) == [("Thesis", 2), ("App", 1)]


def test_archive_hides_project_but_keeps_history(tmp_config):
    pid = stats.ensure_project("Thesis")
    _record(project_id=pid)

    stats.archive_project(pid)
    assert stats.list_projects() == []
    # sessions keep their link and still show in analysis
    assert stats.project_breakdown(None) == [("Thesis", 1)]
    # re-adding the same name restores the same project
    assert stats.ensure_project("Thesis") == pid
    assert stats.list_projects() == [(pid, "Thesis", 1)]


def test_legacy_text_column_backfilled_into_projects(tmp_config):
    # simulate a DB from the short-lived era where sessions had a free-text project column
    with stats._db() as conn:
        conn.execute("ALTER TABLE sessions ADD COLUMN project TEXT")
        conn.execute(
            "INSERT INTO sessions (date, started_at, completed_at, project)"
            " VALUES ('2026-07-01', '2026-07-01T10:00:00', '2026-07-01T10:25:00', 'Thesis')"
        )

    stats.init_db()

    assert stats.project_breakdown(None) == [("Thesis", 1)]
    with stats._db() as conn:
        row = conn.execute("SELECT project_id FROM sessions WHERE project = 'Thesis'").fetchone()
    assert row[0] is not None


def test_config_migration_moves_projects_to_db(tmp_config, tmp_path):
    data = json.loads(config._CONFIG_FILE.read_text())
    data["projects"] = ["Thesis", "App"]
    data["active_project"] = "App"
    config._CONFIG_FILE.write_text(json.dumps(data))

    config.seed(tmp_path)  # empty assets dir is fine

    migrated = json.loads(config._CONFIG_FILE.read_text())
    assert "projects" not in migrated and "active_project" not in migrated
    names = [name for _, name, _ in stats.list_projects()]
    assert names == ["Thesis", "App"]
    assert migrated["active_project_id"] == stats.ensure_project("App")


def test_add_project_sets_active_and_persists(qtbot, tmp_config):
    window = _window(qtbot, tmp_config)
    page = window._projects_page

    page._input.setText("Thesis")
    page._add()

    pid = stats.ensure_project("Thesis")
    assert tmp_config["active_project_id"] == pid
    saved = json.loads(config._CONFIG_FILE.read_text())
    assert saved["active_project_id"] == pid
    assert window._lbl_project.text() == "▸ Thesis"


def test_add_existing_name_reactivates_instead_of_duplicating(qtbot, tmp_config):
    window = _window(qtbot, tmp_config)
    page = window._projects_page

    page._input.setText("  ")
    page._add()
    assert stats.list_projects() == []

    page._input.setText("Thesis")
    page._add()
    page._input.setText("Thesis")
    page._add()
    assert len(stats.list_projects()) == 1


def test_click_active_project_deactivates(qtbot, tmp_config):
    window = _window(qtbot, tmp_config)
    page = window._projects_page
    page._input.setText("Thesis")
    page._add()

    page._on_item_clicked(page._list.item(0))

    assert tmp_config["active_project_id"] is None
    assert window._lbl_project.text() == ""


def test_archive_button_clears_active(qtbot, tmp_config):
    window = _window(qtbot, tmp_config)
    page = window._projects_page
    page._input.setText("Thesis")
    page._add()

    page._list.setCurrentRow(0)
    page._archive()

    assert tmp_config["active_project_id"] is None
    assert page._list.count() == 0


def test_projects_list_shows_session_counts(qtbot, tmp_config):
    pid = stats.ensure_project("Thesis")
    _record(project_id=pid)
    _record(project_id=pid)

    window = _window(qtbot, tmp_config)
    page = window._projects_page

    assert "Thesis" in page._list.item(0).text()
    assert "2" in page._list.item(0).text()


def test_dashboard_shows_project_breakdown(qtbot, tmp_config):
    pid = stats.ensure_project("Thesis")
    _record(project_id=pid)

    window = _window(qtbot, tmp_config)
    window.centralWidget().setCurrentIndex(2)
    qtbot.waitUntil(
        lambda: window._dashboard_page._projects._data == [("Thesis", 1)], timeout=1000
    )
