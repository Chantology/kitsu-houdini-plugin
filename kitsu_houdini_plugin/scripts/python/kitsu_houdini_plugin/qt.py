"""Qt binding shim for the classes this plugin uses.

Houdini bundles its own Qt binding — PySide2 through Houdini 20.5, PySide6
in later Qt6 builds — and ships `hutil.PySide`, its own official shim that
picks the right one (it switches on the `__HOUDINI_USE_QT6__` environment
variable Houdini sets internally). Every other module imports its Qt
classes from here instead, so the rest of the code never needs to care
which binding is actually loaded.
"""

from hutil.PySide.QtCore import QObject, QRectF, QSettings, Qt, QTimer, Signal
from hutil.PySide.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from hutil.PySide.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


def exec_dialog(dialog):
    """QDialog.exec() on a Qt6 binding, QDialog.exec_() on PySide2 —
    `exec` was a reserved word in Python 2, so PySide2 only exposes the
    trailing-underscore spelling; Qt6 bindings dropped it in favor of the
    plain name. Houdini 20.5 only ships PySide2, but this keeps working
    unchanged on a future Qt6 Houdini build."""
    if hasattr(dialog, "exec"):
        return dialog.exec()
    return dialog.exec_()
