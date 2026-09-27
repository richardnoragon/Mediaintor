"""Profile appearance with immediate preview and atomic persistence rollback."""
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QEvent
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QFormLayout, QComboBox, QPushButton, QMessageBox, QLabel, QTableView
from .settings import APPEARANCE_CHOICES, appearance_defaults, validate_appearance, SettingsError

SCALES = {"Small": .9, "Default": 1., "Large": 1.2, "Extra Large": 1.4}
ACCENTS = {"Blue": "#245ca6", "Green": "#226b43", "Purple": "#75449c", "Orange": "#914900", "Red": "#aa3038"}

class AppearanceController(QObject):
    changed = pyqtSignal(dict)

    def __init__(self, store, state, parent=None):
        super().__init__(parent)
        self.store, self.state = store, state
        self.app = QApplication.instance()
        # Capture once per application, never from a previously scaled font.
        if not hasattr(self.app, "_appearance_baseline"):
            self.app._appearance_baseline = (QFont(self.app.font()), QPalette(self.app.palette()), self.app.styleSheet())
        self.font, self.palette, self.stylesheet = self.app._appearance_baseline
        self.saved = validate_appearance(state.get("appearance", appearance_defaults()))
        self.current = dict(self.saved)
        self.app.installEventFilter(self)
        self.apply(self.saved)
        self.app.styleHints().colorSchemeChanged.connect(self.system_changed)

    def system_changed(self, *args):
        self.apply(self.saved)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Show and isinstance(watched, QTableView):
            self.size_table(watched)
        return False

    def size_table(self, table):
        spacing = {"Compact": 2, "Normal": 4, "Comfortable": 7}[self.current["density"]]
        minimum = table.fontMetrics().height() + round(2 * spacing * SCALES[self.current["size"]]) + 4
        table.verticalHeader().setMinimumSectionSize(minimum)
        table.verticalHeader().setDefaultSectionSize(minimum)

    def apply(self, value):
        self.current = dict(value)
        scale = SCALES[value["size"]]
        font = QFont(self.font)
        if font.pointSizeF() > 0:
            font.setPointSizeF(self.font.pointSizeF() * scale)
        else:
            font.setPixelSize(max(1, round(self.font.pixelSize() * scale)))
        self.app.setFont(font)
        palette = QPalette(self.palette)
        dark = value["theme"] == "Dark" or (value["theme"] == "System" and self.app.styleHints().colorScheme() == Qt.ColorScheme.Dark)
        if value["theme"] != "System" or self.app.styleHints().colorScheme() != Qt.ColorScheme.Unknown:
            colors = {"Window": "#242424" if dark else "#f2f2f2", "Base": "#191919" if dark else "#ffffff",
                      "AlternateBase": "#303030" if dark else "#e8e8e8", "Button": "#333333" if dark else "#e8e8e8",
                      "WindowText": "#eeeeee" if dark else "#202020", "Text": "#eeeeee" if dark else "#202020",
                      "ButtonText": "#eeeeee" if dark else "#202020", "ToolTipBase": "#242424" if dark else "#ffffff",
                      "ToolTipText": "#eeeeee" if dark else "#202020"}
            for role, color in colors.items():
                palette.setColor(getattr(QPalette.ColorRole, role), QColor(color))
        # PlaceholderText is independent of Text: retaining the desktop's
        # light-theme brush makes placeholders almost black on a dark Base.
        # Set an opaque brush for each group, including inactive dialogs.
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive,
                      QPalette.ColorGroup.Disabled):
            base = palette.color(group, QPalette.ColorRole.Base)
            placeholder = "#aaaaaa" if base.lightnessF() < .5 else "#666666"
            palette.setColor(group, QPalette.ColorRole.PlaceholderText, QColor(placeholder))
        accent = QColor(ACCENTS[value["accent"]]) if value["accent"] != "System" else self.palette.color(QPalette.ColorRole.Highlight)
        palette.setColor(QPalette.ColorRole.Highlight, accent)
        # Contrast-based selection text also handles a light system accent.
        channels = [accent.redF(), accent.greenF(), accent.blueF()]
        channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
        luminance = sum(a*b for a,b in zip(channels, (.2126,.7152,.0722)))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000" if luminance > .179 else "#ffffff"))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#999999" if dark else "#666666"))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#999999" if dark else "#666666"))
        self.app.setPalette(palette)
        spacing = round({"Compact": 2, "Normal": 4, "Comfortable": 7}[value["density"]] * scale)
        icon = round(16 * scale)
        self.app.setStyleSheet(self.stylesheet + f"""
            QPushButton, QToolButton {{ padding: {spacing}px; icon-size: {icon}px; }}
            QLineEdit, QComboBox, QSpinBox {{ padding: {spacing}px; }}
            QCheckBox, QRadioButton {{ spacing: {spacing + 3}px; }}
            QAbstractItemView::item {{ padding: {spacing}px; }}
            QTabBar::tab {{ padding: {spacing + 2}px; }}
        """)
        for widget in self.app.allWidgets():
            if isinstance(widget, QTableView):
                self.size_table(widget)
        self.changed.emit(dict(value))

    def change(self, requested):
        requested = validate_appearance(requested)
        self.apply(requested)
        candidate = dict(self.state, appearance=requested)
        try:
            self.store.save(candidate)
        except SettingsError:
            self.apply(self.saved)
            raise
        self.state["appearance"] = dict(requested)
        self.saved = dict(requested)

class AppearanceDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Settings — Appearance")
        layout = QVBoxLayout(self)
        note = QLabel("Appearance applies to this profile on this device. Reader and workspace preferences stay unchanged.")
        note.setWordWrap(True); layout.addWidget(note)
        form = QFormLayout(); layout.addLayout(form)
        self.controls = {}
        for key, choices in APPEARANCE_CHOICES.items():
            combo = QComboBox(); combo.addItems(choices)
            self.controls[key] = combo
            form.addRow({"theme":"Theme", "accent":"Accent color", "size":"UI size", "density":"Density"}[key], combo)
            combo.currentTextChanged.connect(lambda text, k=key: self.request(dict(self.controller.saved, **{k:text})))
        controller.changed.connect(self.sync)
        self.sync(controller.saved)
        reset = QPushButton("Reset appearance…"); reset.clicked.connect(self.reset); layout.addWidget(reset)
        close = QPushButton("Close settings"); close.clicked.connect(self.close); layout.addWidget(close)

    def sync(self, value):
        for key, combo in self.controls.items():
            previous = combo.blockSignals(True)
            combo.setCurrentText(value[key]); combo.blockSignals(previous)

    def request(self, requested):
        while True:
            try:
                self.controller.change(requested)
                return
            except SettingsError as exc:
                box = QMessageBox(self)
                box.setWindowTitle("Unable to save appearance settings")
                box.setText("Unable to save appearance settings. The previous appearance has been restored.")
                box.setDetailedText(str(exc)); box.setIcon(QMessageBox.Icon.Warning)
                box.setStandardButtons(QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close)
                if box.exec() != QMessageBox.StandardButton.Retry:
                    return

    def reset(self):
        answer = QMessageBox.question(self, "Reset appearance?", "Reset theme, accent color, UI size and density? Layouts and tool preferences will remain unchanged.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Yes:
            self.request(appearance_defaults())
