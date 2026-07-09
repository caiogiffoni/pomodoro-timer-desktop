from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)

_PRESET_TAGS = ["Coding", "Writing", "Reading", "Learning", "Meetings", "Planning", "Other"]


class SessionReviewDialog(QDialog):
    def __init__(
        self,
        parent=None,
        prefill_notes: str | None = None,
        prefill_tag: str | None = None,
        prefill_focus: int | None = None,
        projects: list[str] | None = None,
        prefill_project: str | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Session complete")
        self.setFixedWidth(340)
        self.setModal(True)
        self.setStyleSheet("font-size: 14px;")

        self._project = QComboBox()
        self._project.setEditable(True)
        self._project.addItem("")
        self._project.addItems(projects or [])
        self._project.setCurrentIndex(0)
        self._project.lineEdit().setPlaceholderText("Project (optional)")
        if prefill_project:
            idx = self._project.findText(prefill_project)
            if idx >= 0:
                self._project.setCurrentIndex(idx)
            else:
                self._project.setCurrentText(prefill_project)

        self._notes = QLineEdit()
        self._notes.setPlaceholderText("What did you work on? (optional)")
        if prefill_notes:
            self._notes.setText(prefill_notes)

        self._tag = QComboBox()
        self._tag.setEditable(True)
        self._tag.addItem("")
        self._tag.addItems(_PRESET_TAGS)
        self._tag.setCurrentIndex(0)
        self._tag.lineEdit().setPlaceholderText("Tag (optional)")
        if prefill_tag:
            idx = self._tag.findText(prefill_tag)
            if idx >= 0:
                self._tag.setCurrentIndex(idx)
            else:
                self._tag.setCurrentText(prefill_tag)

        self._focus_group = QButtonGroup(self)
        focus_row = QHBoxLayout()
        focus_row.addWidget(QLabel("Focus:"))
        for i in range(1, 6):
            rb = QRadioButton(str(i))
            self._focus_group.addButton(rb, i)
            focus_row.addWidget(rb)
        if prefill_focus is not None:
            btn = self._focus_group.button(prefill_focus)
            if btn:
                btn.setChecked(True)
        focus_row.addStretch()

        form = QFormLayout()
        form.addRow("Project:", self._project)
        form.addRow("Notes:", self._notes)
        form.addRow("Tag:", self._tag)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Save")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Skip")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(focus_row)
        layout.addWidget(buttons)
        self.setLayout(layout)

    @property
    def project(self) -> str | None:
        v = self._project.currentText().strip()
        return v or None

    @property
    def notes(self) -> str | None:
        v = self._notes.text().strip()
        return v or None

    @property
    def tag(self) -> str | None:
        v = self._tag.currentText().strip()
        return v or None

    @property
    def focus_score(self) -> int | None:
        btn = self._focus_group.checkedButton()
        return self._focus_group.id(btn) if btn else None
