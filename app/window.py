from PyQt6.QtCore import Qt, QEvent, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.timer import Phase, PomodoroTimer

_COLOR_WORK = QColor("#D85A30")
_COLOR_BREAK = QColor("#1D9E75")
_COLOR_LONG_BREAK = QColor("#5B6AE8")
_COLOR_STOP = QColor("#C0392B")
_COLOR_TRACK = QColor("#2E2E2E")
_COLOR_BG = QColor("#1A1A1A")
_COLOR_TEXT = QColor("#F0F0F0")
_COLOR_DIM = QColor("#555555")

_ARC_MARGIN = 24
_ARC_WIDTH = 10


class _ArcWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fraction = 1.0
        self._phase = Phase.IDLE
        self._seconds_left = 0
        self._sessions_completed = 0
        self._pomodoros_until_long_break = 4
        self.setMinimumSize(240, 240)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_state(
        self,
        fraction: float,
        phase: Phase,
        seconds_left: int,
        sessions_completed: int = 0,
        pomodoros_until_long_break: int = 4,
    ) -> None:
        self._fraction = fraction
        self._phase = phase
        self._seconds_left = seconds_left
        self._sessions_completed = sessions_completed
        self._pomodoros_until_long_break = pomodoros_until_long_break
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        rect = QRect(
            _ARC_MARGIN,
            _ARC_MARGIN,
            w - _ARC_MARGIN * 2,
            h - _ARC_MARGIN * 2,
        )

        # Background fill
        p.fillRect(0, 0, w, h, _COLOR_BG)

        # Track ring
        pen = QPen(_COLOR_TRACK, _ARC_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        # Progress arc (depletes clockwise from top)
        if self._fraction > 0:
            if self._phase == Phase.BREAK:
                color = _COLOR_BREAK
            elif self._phase == Phase.LONG_BREAK:
                color = _COLOR_LONG_BREAK
            else:
                color = _COLOR_WORK
            pen = QPen(color, _ARC_WIDTH)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen)
            start_angle = 90 * 16
            span_angle = -int(self._fraction * 360 * 16)
            p.drawArc(rect, start_angle, span_angle)

        # Time label
        minutes, seconds = divmod(self._seconds_left, 60)
        label = f"{minutes:02d}:{seconds:02d}"
        p.setPen(QPen(_COLOR_TEXT))
        font = QFont("Monospace", 28, QFont.Weight.Bold)
        p.setFont(font)
        time_rect = QRect(rect.x(), rect.y() - 12, rect.width(), rect.height())
        p.drawText(time_rect, Qt.AlignmentFlag.AlignCenter, label)

        # Session dots (N filled + remaining empty circles)
        n = self._pomodoros_until_long_break
        done = self._sessions_completed % n
        dots = "●" * done + "○" * (n - done)
        p.setPen(QPen(_COLOR_DIM))
        font_dots = QFont("Monospace", 11)
        p.setFont(font_dots)
        dots_rect = QRect(rect.x(), rect.y() + 22, rect.width(), rect.height())
        p.drawText(dots_rect, Qt.AlignmentFlag.AlignCenter, dots)

        p.end()


class _ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple[str, int]] = []
        self._is_current = True
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data: list[tuple[str, int]], is_current: bool = True) -> None:
        self._data = data
        self._is_current = is_current
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, _COLOR_BG)

        if not self._data:
            p.end()
            return

        n = len(self._data)
        margin_x = 20
        margin_top = 32
        margin_bottom = 36
        bar_area_h = h - margin_top - margin_bottom
        max_count = max(c for _, c in self._data) or 1
        col_w = (w - margin_x * 2) / n
        bar_w = col_w * 0.5

        for i, (day, count) in enumerate(self._data):
            cx = margin_x + (i + 0.5) * col_w
            bar_x = cx - bar_w / 2
            is_today = self._is_current and (i == n - 1)

            bar_h = max((count / max_count) * bar_area_h, 4) if count > 0 else 0
            bar_y = margin_top + bar_area_h - bar_h

            if count > 0:
                color = _COLOR_WORK.lighter(120) if is_today else _COLOR_WORK
                p.setBrush(color)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(int(bar_x), int(bar_y), int(bar_w), int(bar_h), 3, 3)
                p.setPen(QPen(_COLOR_TEXT))
                p.setFont(QFont("Monospace", 9, QFont.Weight.Bold))
                p.drawText(
                    QRect(int(bar_x - 8), int(bar_y) - 20, int(bar_w + 16), 18),
                    Qt.AlignmentFlag.AlignCenter,
                    str(count),
                )

            label_color = _COLOR_TEXT if is_today else _COLOR_DIM
            p.setPen(QPen(label_color))
            p.setFont(QFont("Monospace", 8))
            p.drawText(
                QRect(int(cx - col_w / 2), h - margin_bottom + 6, int(col_w), 22),
                Qt.AlignmentFlag.AlignCenter,
                day,
            )

        p.end()


_NAV_BTN = (
    "QPushButton { background: #2E2E2E; color: #F0F0F0; border: none;"
    " border-radius: 4px; font-size: 14px; padding: 2px 8px; }"
    "QPushButton:hover { background: #3A3A3A; }"
    "QPushButton:disabled { color: #3A3A3A; }"
)
_TOGGLE_ON = (
    "QPushButton { background: #D85A30; color: white; border: none;"
    " padding: 3px 16px; border-radius: 3px; font-size: 11px; }"
)
_TOGGLE_OFF = (
    "QPushButton { background: #2E2E2E; color: #888888; border: none;"
    " padding: 3px 16px; border-radius: 3px; font-size: 11px; }"
    "QPushButton:hover { color: #CCCCCC; }"
)


class _StatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0

        self._btn_chart_toggle = QPushButton("Chart")
        self._btn_list_toggle = QPushButton("List")
        self._btn_chart_toggle.setStyleSheet(_TOGGLE_ON)
        self._btn_list_toggle.setStyleSheet(_TOGGLE_OFF)
        self._btn_chart_toggle.clicked.connect(self._show_chart)
        self._btn_list_toggle.clicked.connect(self._show_list)

        toggle_row = QHBoxLayout()
        toggle_row.addStretch()
        toggle_row.addWidget(self._btn_chart_toggle)
        toggle_row.addWidget(self._btn_list_toggle)
        toggle_row.addStretch()

        # summary strip
        _lbl_style = "color: #888888; font-size: 11px;"
        self._lbl_streak = QLabel()
        self._lbl_streak.setStyleSheet(_lbl_style)
        self._lbl_goal = QLabel()
        self._lbl_goal.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._lbl_goal.setStyleSheet(_lbl_style)

        summary_row = QHBoxLayout()
        summary_row.setContentsMargins(12, 0, 12, 0)
        summary_row.addWidget(self._lbl_streak)
        summary_row.addStretch()
        summary_row.addWidget(self._lbl_goal)

        # chart page
        self._chart = _ChartWidget()

        self._week_label = QLabel("Last 7 days")
        self._week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._week_label.setStyleSheet("color: #888888; font-size: 11px;")

        self._btn_prev = QPushButton("←")
        self._btn_prev.setFixedSize(32, 26)
        self._btn_prev.setStyleSheet(_NAV_BTN)
        self._btn_prev.clicked.connect(self._go_prev)

        self._btn_next = QPushButton("→")
        self._btn_next.setFixedSize(32, 26)
        self._btn_next.setStyleSheet(_NAV_BTN)
        self._btn_next.clicked.connect(self._go_next)
        self._btn_next.setEnabled(False)

        nav_row = QHBoxLayout()
        nav_row.addWidget(self._btn_prev)
        nav_row.addStretch()
        nav_row.addWidget(self._week_label)
        nav_row.addStretch()
        nav_row.addWidget(self._btn_next)

        chart_page = QWidget()
        chart_vbox = QVBoxLayout()
        chart_vbox.setContentsMargins(8, 4, 8, 8)
        chart_vbox.addWidget(self._chart)
        chart_vbox.addLayout(nav_row)
        chart_page.setLayout(chart_vbox)

        # list page
        self._list = QListWidget()
        self._list.setStyleSheet(_LIST_STYLE)
        self._list.setAlternatingRowColors(True)
        self._list.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        self._stack = QStackedWidget()
        self._stack.addWidget(chart_page)
        self._stack.addWidget(self._list)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 6, 0, 0)
        vbox.addLayout(toggle_row)
        vbox.addLayout(summary_row)
        vbox.addWidget(self._stack)
        self.setLayout(vbox)

        self.refresh()

    def refresh(self) -> None:
        from datetime import date, timedelta
        from app import config, stats

        # summary strip
        s = stats.streak()
        self._lbl_streak.setText(f"{s}-day streak" if s > 0 else "")

        cfg = config.load()
        goal = cfg.get("daily_goal", 0)
        n = stats.today_count()
        if goal:
            self._lbl_goal.setText(f"{n} / {goal} today")
            self._lbl_goal.setStyleSheet(
                f"color: {'#1D9E75' if n >= goal else '#888888'}; font-size: 11px;"
            )
        else:
            self._lbl_goal.setText(f"{n} today")
            self._lbl_goal.setStyleSheet("color: #888888; font-size: 11px;")

        data = stats.last_7_days(self._offset)
        self._chart.set_data(data, is_current=(self._offset == 0))

        end = date.today() - timedelta(weeks=self._offset)
        start = end - timedelta(days=6)
        self._week_label.setText(
            "Last 7 days" if self._offset == 0
            else f"{start.strftime('%b %d')} – {end.strftime('%b %d')}"
        )

        self._list.clear()
        today_iso = date.today().isoformat()
        for iso_date, count in stats.all_days():
            try:
                d = date.fromisoformat(iso_date)
                suffix = "  (today)" if iso_date == today_iso else ""
                label = f"{d.strftime('%b %d')}  {d.strftime('%a')}{suffix}  —  {count}"
            except ValueError:
                label = f"{iso_date}  —  {count}"
            self._list.addItem(label)

    def _go_prev(self) -> None:
        self._offset += 1
        self._btn_next.setEnabled(True)
        self.refresh()

    def _go_next(self) -> None:
        self._offset = max(0, self._offset - 1)
        self._btn_next.setEnabled(self._offset > 0)
        self.refresh()

    def _show_chart(self) -> None:
        self._stack.setCurrentIndex(0)
        self._btn_chart_toggle.setStyleSheet(_TOGGLE_ON)
        self._btn_list_toggle.setStyleSheet(_TOGGLE_OFF)

    def _show_list(self) -> None:
        self._stack.setCurrentIndex(1)
        self._btn_list_toggle.setStyleSheet(_TOGGLE_ON)
        self._btn_chart_toggle.setStyleSheet(_TOGGLE_OFF)


class _TagBarsWidget(QWidget):
    def __init__(self, parent=None, min_height: int = 90):
        super().__init__(parent)
        self._data: list[tuple[str, int]] = []
        self.setMinimumHeight(min_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data: list[tuple[str, int]]) -> None:
        self._data = data
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, _COLOR_BG)

        if not self._data:
            p.setPen(QPen(_COLOR_DIM))
            p.setFont(QFont("Monospace", 9))
            p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "No tagged sessions yet")
            p.end()
            return

        margin = 14
        row_h = min(22, h // len(self._data))
        label_w = 80
        count_w = 26
        bar_area = w - margin * 2 - label_w - count_w
        max_count = max(c for _, c in self._data)

        for i, (tag, count) in enumerate(self._data):
            y = i * row_h
            name = tag if len(tag) <= 11 else tag[:10] + "…"
            p.setPen(QPen(_COLOR_TEXT))
            p.setFont(QFont("Monospace", 8))
            p.drawText(
                QRect(margin, y, label_w, row_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                name,
            )
            bar_w = max(int(bar_area * count / max_count), 3)
            p.setBrush(_COLOR_WORK)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(margin + label_w, y + row_h // 2 - 4, bar_w, 8, 3, 3)
            p.setPen(QPen(_COLOR_DIM))
            p.setFont(QFont("Monospace", 8))
            p.drawText(
                QRect(margin + label_w + bar_w + 6, y, count_w, row_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                str(count),
            )
        p.end()


class _HourChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._counts: list[int] = [0] * 24
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, counts: list[int]) -> None:
        self._counts = counts
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, _COLOR_BG)

        if not any(self._counts):
            p.setPen(QPen(_COLOR_DIM))
            p.setFont(QFont("Monospace", 9))
            p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "No sessions yet")
            p.end()
            return

        margin_x = 14
        margin_top = 8
        margin_bottom = 18
        bar_area_h = h - margin_top - margin_bottom
        col_w = (w - margin_x * 2) / 24
        bar_w = col_w * 0.7
        max_count = max(self._counts)

        for hour, count in enumerate(self._counts):
            cx = margin_x + (hour + 0.5) * col_w
            if count > 0:
                bar_h = max((count / max_count) * bar_area_h, 3)
                p.setBrush(_COLOR_BREAK)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(
                    int(cx - bar_w / 2),
                    int(margin_top + bar_area_h - bar_h),
                    max(int(bar_w), 2),
                    int(bar_h),
                    1, 1,
                )
            if hour % 6 == 0:
                p.setPen(QPen(_COLOR_DIM))
                p.setFont(QFont("Monospace", 7))
                p.drawText(
                    QRect(int(cx - col_w * 1.5), h - margin_bottom + 4, int(col_w * 3), 12),
                    Qt.AlignmentFlag.AlignCenter,
                    str(hour),
                )
        p.end()


_LIST_STYLE = """
    QListWidget {
        background: #1A1A1A; color: #F0F0F0; border: none;
        font-family: Monospace; font-size: 12px;
    }
    QListWidget::item { padding: 7px 14px; }
    QListWidget::item:alternate { background: #222222; }
    QListWidget::item:selected { background: #2E2E2E; color: #F0F0F0; }
    QScrollBar:vertical { background: #1A1A1A; width: 6px; border: none; }
    QScrollBar::handle:vertical { background: #444444; border-radius: 3px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


class _ProjectsWidget(QWidget):
    """Manage the projects table; the active project is stamped on every new work session."""

    active_changed = pyqtSignal(str)  # active project name, "" = none

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self._cfg = cfg

        self._input = QLineEdit()
        self._input.setPlaceholderText("New project name")
        self._input.setStyleSheet(
            "QLineEdit { background: #2E2E2E; color: #F0F0F0; border: none;"
            " border-radius: 4px; padding: 6px 10px; font-size: 12px; }"
        )
        self._input.returnPressed.connect(self._add)

        btn_add = QPushButton("Add")
        btn_add.setFixedHeight(30)
        btn_add.setStyleSheet(_TOGGLE_ON)
        btn_add.clicked.connect(self._add)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(12, 4, 12, 4)
        input_row.addWidget(self._input)
        input_row.addWidget(btn_add)

        hint = QLabel(
            "Click a project to make it active — every pomodoro is recorded under it."
            " Archiving keeps its history; re-add the same name to restore it."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888888; font-size: 10px; margin: 0 14px;")

        self._list = QListWidget()
        self._list.setStyleSheet(_LIST_STYLE)
        self._list.setAlternatingRowColors(True)
        self._list.itemClicked.connect(self._on_item_clicked)

        self._btn_archive = QPushButton("Archive selected")
        self._btn_archive.setStyleSheet(_TOGGLE_OFF)
        self._btn_archive.setFixedHeight(26)
        self._btn_archive.clicked.connect(self._archive)

        archive_row = QHBoxLayout()
        archive_row.setContentsMargins(12, 0, 12, 8)
        archive_row.addStretch()
        archive_row.addWidget(self._btn_archive)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 8, 0, 0)
        vbox.setSpacing(6)
        vbox.addLayout(input_row)
        vbox.addWidget(hint)
        vbox.addWidget(self._list)
        vbox.addLayout(archive_row)
        self.setLayout(vbox)

        self.refresh()

    def refresh(self) -> None:
        from app import stats

        active_id = self._cfg.get("active_project_id")
        self._list.clear()
        for pid, name, count in stats.list_projects():
            marker = "●" if pid == active_id else "○"
            item = QListWidgetItem(f"{marker}  {name}  —  {count}")
            item.setData(Qt.ItemDataRole.UserRole, pid)
            if pid == active_id:
                item.setForeground(_COLOR_WORK)
            self._list.addItem(item)

    def active_name(self) -> str:
        from app import stats

        pid = self._cfg.get("active_project_id")
        if pid is None:
            return ""
        return stats.project_name(pid) or ""

    def _save(self) -> None:
        from app import config
        config.save(self._cfg)
        self.refresh()
        self.active_changed.emit(self.active_name())

    def _add(self) -> None:
        from app import stats

        name = self._input.text().strip()
        if not name:
            return
        self._cfg["active_project_id"] = stats.ensure_project(name)
        self._input.clear()
        self._save()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        pid = item.data(Qt.ItemDataRole.UserRole)
        # clicking the active project again deactivates it
        self._cfg["active_project_id"] = None if self._cfg.get("active_project_id") == pid else pid
        self._save()

    def _archive(self) -> None:
        from app import stats

        item = self._list.currentItem()
        if item is None:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        stats.archive_project(pid)
        if self._cfg.get("active_project_id") == pid:
            self._cfg["active_project_id"] = None
        self._save()


class _DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._days: int | None = 7

        self._period_btns: list[tuple[QPushButton, int | None]] = []
        period_row = QHBoxLayout()
        period_row.addStretch()
        for label, days in [("7D", 7), ("30D", 30), ("All", None)]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, d=days: self._set_period(d))
            period_row.addWidget(btn)
            self._period_btns.append((btn, days))
        period_row.addStretch()

        self._val_sessions = self._value_label()
        self._val_time = self._value_label()
        self._val_focus = self._value_label()
        self._val_days = self._value_label()

        cards_row = QHBoxLayout()
        cards_row.setContentsMargins(8, 4, 8, 4)
        for value_lbl, caption in [
            (self._val_sessions, "sessions"),
            (self._val_time, "focus time"),
            (self._val_focus, "avg focus"),
            (self._val_days, "active days"),
        ]:
            cards_row.addLayout(self._card(value_lbl, caption))

        self._projects = _TagBarsWidget(min_height=70)
        self._tags = _TagBarsWidget(min_height=70)
        self._hours = _HourChartWidget()

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 6, 0, 4)
        vbox.setSpacing(2)
        vbox.addLayout(period_row)
        vbox.addLayout(cards_row)
        vbox.addWidget(self._section_label("BY PROJECT"))
        vbox.addWidget(self._projects)
        vbox.addWidget(self._section_label("BY TAG"))
        vbox.addWidget(self._tags)
        vbox.addWidget(self._section_label("START HOUR"))
        vbox.addWidget(self._hours)
        self.setLayout(vbox)

        self._style_period_btns()
        self.refresh()

    @staticmethod
    def _value_label() -> QLabel:
        lbl = QLabel("—")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #F0F0F0; font-size: 15px; font-weight: bold;")
        return lbl

    @staticmethod
    def _card(value_lbl: QLabel, caption: str):
        cap = QLabel(caption)
        cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cap.setStyleSheet("color: #888888; font-size: 9px;")
        box = QVBoxLayout()
        box.setSpacing(0)
        box.addWidget(value_lbl)
        box.addWidget(cap)
        return box

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #555555; font-size: 9px; margin-left: 14px;")
        return lbl

    def _style_period_btns(self) -> None:
        for btn, days in self._period_btns:
            btn.setStyleSheet(_TOGGLE_ON if days == self._days else _TOGGLE_OFF)

    def _set_period(self, days: int | None) -> None:
        self._days = days
        self._style_period_btns()
        self.refresh()

    def refresh(self) -> None:
        from app import stats

        summary = stats.dashboard_summary(self._days)
        self._val_sessions.setText(str(summary["sessions"]))

        secs = summary["focus_seconds"]
        if secs >= 3600:
            self._val_time.setText(f"{secs // 3600}h {(secs % 3600) // 60:02d}m")
        else:
            self._val_time.setText(f"{secs // 60}m")

        avg = summary["avg_focus"]
        self._val_focus.setText(f"{avg:.1f} ★" if avg is not None else "—")
        self._val_days.setText(str(summary["active_days"]))

        self._projects.set_data(stats.project_breakdown(self._days))
        self._tags.set_data(stats.tag_breakdown(self._days))
        self._hours.set_data(stats.hour_histogram(self._days))


class MainWindow(QMainWindow):
    def __init__(self, timer: PomodoroTimer, icon: QIcon, cfg: dict, notifier=None, parent=None):
        super().__init__(parent)
        self._timer = timer
        self._cfg = cfg
        self._notifier = notifier
        self._total_seconds = timer.work_duration

        self.setWindowTitle("Pomodoro")
        self.setWindowIcon(icon)
        self.setMinimumSize(300, 380)
        self.resize(340, 460)
        self.setStyleSheet(f"background-color: {_COLOR_BG.name()};")

        # Widgets
        self._arc = _ArcWidget()
        self._arc.set_state(
            1.0,
            Phase.IDLE,
            timer.work_duration,
            timer.sessions_completed,
            timer.pomodoros_until_long_break,
        )

        self._btn_start = QPushButton("Start")
        self._btn_start.setFixedSize(100, 40)
        self._btn_start.setStyleSheet(self._btn_style(_COLOR_WORK))
        self._btn_start.clicked.connect(self._on_start_stop)

        self._btn_pause = QPushButton("Pause")
        self._btn_pause.setFixedSize(100, 40)
        self._btn_pause.setStyleSheet(self._btn_style(QColor("#888888")))
        self._btn_pause.clicked.connect(self._on_pause_resume)
        self._btn_pause.setVisible(False)

        self._btn_gear = QPushButton("⚙")
        self._btn_gear.setFixedSize(36, 36)
        self._btn_gear.setStyleSheet(
            "color: #888; background: transparent; border: none; font-size: 18px;"
        )
        self._btn_gear.clicked.connect(self._on_settings)

        # Layout
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._btn_start)
        btn_row.addSpacing(8)
        btn_row.addWidget(self._btn_pause)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_gear)

        self._lbl_project = QLabel()
        self._lbl_project.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_project.setStyleSheet("color: #888888; font-size: 11px;")

        vbox = QVBoxLayout()
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.addWidget(self._arc, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox.addWidget(self._lbl_project)
        vbox.addLayout(btn_row)

        timer_page = QWidget()
        timer_page.setLayout(vbox)

        self._stats_page = _StatsWidget()
        self._dashboard_page = _DashboardWidget()
        self._projects_page = _ProjectsWidget(cfg)
        self._projects_page.active_changed.connect(self._set_project_label)
        self._set_project_label(self._projects_page.active_name())

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #2E2E2E; color: #888888;
                padding: 6px 14px; border: none;
            }
            QTabBar::tab:selected { background: #1A1A1A; color: #F0F0F0; }
            QTabBar::tab:hover { background: #3A3A3A; color: #CCCCCC; }
        """)
        tabs.addTab(timer_page, "Timer")
        tabs.addTab(self._stats_page, "Stats")
        tabs.addTab(self._dashboard_page, "Dashboard")
        tabs.addTab(self._projects_page, "Projects")
        tabs.currentChanged.connect(self._on_tab_changed)

        self.setCentralWidget(tabs)

        # Signals
        timer.tick.connect(self._on_tick)
        timer.phase_ended.connect(self._on_phase_ended)
        timer.paused.connect(self._on_paused)
        timer.resumed.connect(self._on_resumed)
        timer.stopped.connect(self._on_stopped)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_tick(self, seconds_left: int) -> None:
        fraction = seconds_left / self._total_seconds if self._total_seconds else 0
        self._arc.set_state(
            fraction,
            self._timer.phase,
            seconds_left,
            self._timer.sessions_completed,
            self._timer.pomodoros_until_long_break,
        )

    def _on_tab_changed(self, index: int) -> None:
        if index == 1:
            self._stats_page.refresh()
        elif index == 2:
            self._dashboard_page.refresh()
        elif index == 3:
            self._projects_page.refresh()

    def _on_phase_ended(self, phase: str) -> None:
        if phase == "work":
            if self._timer.next_is_long_break:
                self._total_seconds = self._timer.long_break_duration
            else:
                self._total_seconds = self._timer.break_duration
            self._stats_page.refresh()
            self._dashboard_page.refresh()
        else:
            self._total_seconds = self._timer.work_duration
        self._btn_start.setText("Stop")
        self._btn_start.setStyleSheet(self._btn_style(_COLOR_STOP))

    def _on_stopped(self) -> None:
        pending = self._timer.pending_break
        if pending is not None:
            duration = (
                self._timer.long_break_duration if pending == Phase.LONG_BREAK
                else self._timer.break_duration
            )
            arc_color = _COLOR_LONG_BREAK if pending == Phase.LONG_BREAK else _COLOR_BREAK
            self._total_seconds = duration
            self._arc.set_state(
                1.0, pending, duration,
                self._timer.sessions_completed,
                self._timer.pomodoros_until_long_break,
            )
            self._btn_start.setText("Start Break")
            self._btn_start.setStyleSheet(self._btn_style(arc_color))
        else:
            self._total_seconds = self._timer.work_duration
            self._arc.set_state(
                1.0, Phase.IDLE, self._timer.work_duration,
                self._timer.sessions_completed,
                self._timer.pomodoros_until_long_break,
            )
            self._btn_start.setText("Start")
            self._btn_start.setStyleSheet(self._btn_style(_COLOR_WORK))
        self._btn_pause.setVisible(False)
        self._btn_pause.setText("Pause")

    def _on_paused(self) -> None:
        self._btn_pause.setText("Resume")
        prev = self._timer._phase_before_pause
        if prev == Phase.LONG_BREAK:
            color = _COLOR_LONG_BREAK
        elif prev == Phase.BREAK:
            color = _COLOR_BREAK
        else:
            color = _COLOR_WORK
        self._btn_pause.setStyleSheet(self._btn_style(color))

    def _on_resumed(self) -> None:
        self._btn_pause.setText("Pause")
        self._btn_pause.setStyleSheet(self._btn_style(QColor("#888888")))

    def _on_start_stop(self) -> None:
        if self._timer.phase in (Phase.IDLE, Phase.STOPPED):
            pending = self._timer.pending_break
            if pending is not None:
                self._total_seconds = (
                    self._timer.long_break_duration if pending == Phase.LONG_BREAK
                    else self._timer.break_duration
                )
            else:
                self._total_seconds = self._timer.work_duration
            self._timer.start()
            self._btn_start.setText("Stop")
            self._btn_start.setStyleSheet(self._btn_style(_COLOR_STOP))
            self._btn_pause.setVisible(True)
        else:
            self._timer.stop()

    def refresh_projects(self) -> None:
        self._projects_page.refresh()

    def _set_project_label(self, name: str) -> None:
        self._lbl_project.setText(f"▸ {name}" if name else "")

    def _on_pause_resume(self) -> None:
        if self._timer.phase == Phase.PAUSED:
            self._timer.resume()
        else:
            self._timer.pause()

    def _on_settings(self) -> None:
        from app import config
        from app.settings import SettingsDialog
        dlg = SettingsDialog(cfg=self._cfg, notifier=self._notifier, parent=self)
        if dlg.exec():
            # update in place: main.py and the Projects tab hold references to this dict
            self._cfg.update(dlg.updated_cfg())
            config.save(self._cfg)
            self._timer.update_durations(
                self._cfg["work_duration"],
                self._cfg["break_duration"],
                self._cfg["long_break_duration"],
                self._cfg["pomodoros_until_long_break"],
            )
            self._timer.auto_start_break = self._cfg.get("auto_start_break", False)
            if self._notifier:
                self._notifier.set_volume(self._cfg["volume"])

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                event.ignore()
                self.hide()
                return
        super().changeEvent(event)

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()

    # ------------------------------------------------------------------

    @staticmethod
    def _btn_style(color: QColor) -> str:
        return (
            f"QPushButton {{"
            f"  background-color: {color.name()};"
            f"  color: white;"
            f"  border-radius: 8px;"
            f"  font-size: 15px;"
            f"  font-weight: bold;"
            f"}}"
            f"QPushButton:hover {{ background-color: {color.lighter(120).name()}; }}"
            f"QPushButton:pressed {{ background-color: {color.darker(120).name()}; }}"
        )
