# coding: utf-8
"""
In this file we cannot use a relative import here, else Drive will not start when packaged.
See https://github.com/pyinstaller/pyinstaller/issues/2560
"""
import os
import sys
from contextlib import suppress
from typing import Any, Set

from nxdrive.constants import APP_NAME, COMPANY
from nxdrive.options import Options


STATE_FILE = Options.nxdrive_home / "metrics.state"


def show_metrics_acceptance() -> None:
    """ Display a "friendly" dialog box to ask user for metrics approval. """

    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QLabel,
        QVBoxLayout,
    )

    app = QApplication([])
    app.setQuitOnLastWindowClosed(True)

    dialog = QDialog()
    dialog.setWindowTitle(f"{APP_NAME} - Improving Together")
    dialog.setStyleSheet("background-color: #ffffff;")
    layout = QVBoxLayout()

    with suppress(Exception):
        from nxdrive.utils import find_icon

        dialog.setWindowIcon(QIcon(str(find_icon("app_icon.svg"))))

    text = (
        f"At {COMPANY}, we care about your privacy. However, to improve your experience,"
        " it is crucial to share technical information with the developers, in case we ever need to help you."
        " <span style='font-weight:bold;'>No sensitive data will ever be shared</span>."
    )
    info = QLabel(text)
    info.setTextFormat(Qt.RichText)
    info.setWordWrap(True)
    layout.addWidget(info)

    def analytics_choice(state) -> None:
        Options.use_analytics = bool(state)

    def errors_choice(state) -> None:
        Options.use_sentry = bool(state)

    # Checkboxes
    em_analytics = QCheckBox(
        "Allow sharing error reports when something unusual happens"
    )
    em_analytics.setChecked(True)
    em_analytics.stateChanged.connect(errors_choice)
    layout.addWidget(em_analytics)

    cb_analytics = QCheckBox(
        "Share anonymous usage analytics to help the developers build the best experience for you"
    )
    cb_analytics.stateChanged.connect(analytics_choice)
    layout.addWidget(cb_analytics)

    # Buttons
    buttons = QDialogButtonBox()
    buttons.setStandardButtons(QDialogButtonBox.Apply)
    buttons.clicked.connect(dialog.close)
    layout.addWidget(buttons)
    dialog.setLayout(layout)
    dialog.resize(400, 200)
    dialog.show()
    app.exec_()

    states = []
    if Options.use_analytics:
        states.append("analytics")
    if Options.use_sentry:
        states.append("sentry")
    STATE_FILE.write_text("\n".join(states))


def ask_for_metrics_approval() -> None:
    """Should we setup and use Sentry and/or Google Analytics?"""

    # Check the user choice first
    Options.nxdrive_home.mkdir(parents=True, exist_ok=True)

    if STATE_FILE.is_file():
        lines = STATE_FILE.read_text().splitlines()
        Options.use_sentry = "sentry" in lines
        Options.use_analytics = "analytics" in lines
        # Abort now, the user already decided to use Sentry or not
        return

    # The user did not choose yet, display a message box
    show_metrics_acceptance()


def before_send(event: Any, hint: Any) -> Any:
    """
    Alter an event before sending to the Sentry server.
    The event will not be sent if None is returned.
    """

    # Sentry may have been disabled later, via a CLI argument or GUI parameter
    if not Options.use_sentry:
        return None

    # Local vars to hide from Sentry reports
    to_redact: Set[str] = {"password", "pwd", "token"}
    replace: str = "<REDACTED>"

    # Remove passwords from locals
    with suppress(KeyError):
        for thread in event["threads"]:
            for frame in thread["stacktrace"]["frames"]:
                for var in to_redact:
                    # Only alter the value if it exists
                    if var in frame["vars"]:
                        frame["vars"][var] = replace

    return event


def section(header: str, content: str) -> str:
    """Format a "section" of information."""
    return f"{header}\n```\n{content.strip()}\n```"


def setup_sentry() -> None:
    """ Setup Sentry. """

    # TODO: Replace the testing DSN by "DSN_PLACEHOLDER" that will be replaced at when generating installers.
    sentry_dsn: str = os.getenv(
        "SENTRY_DSN", "https://c4daa72433b443b08bd25e0c523ecef5@sentry.io/1372714"
    )
    if not sentry_dsn:
        return

    sentry_env: str = os.getenv("SENTRY_ENV", "production")
    assert sentry_env in {
        "production",
        "testing",
    }, "Bad SENTRY_ENV value (production or testing)"

    import sentry_sdk

    version = None
    with suppress(ImportError):
        from nxdrive import __version__

        version = __version__

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=sentry_env,
        release=version,
        attach_stacktrace=True,
        before_send=before_send,
    )


def show_critical_error() -> None:
    """ Display a "friendly" dialog box on fatal error. """

    import traceback

    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import (
        QApplication,
        QDialog,
        QDialogButtonBox,
        QLabel,
        QTextEdit,
        QVBoxLayout,
    )

    app = QApplication([])
    app.setQuitOnLastWindowClosed(True)

    dialog = QDialog()
    dialog.setWindowTitle(f"{APP_NAME} - Fatal error")
    dialog.resize(600, 400)
    layout = QVBoxLayout()
    css = "font-family: monospace; font-size: 12px;"
    details = []

    with suppress(Exception):
        from nxdrive.utils import find_icon

        dialog.setWindowIcon(QIcon(find_icon("app_icon.svg")))

    # Display a little message to apologize
    text = f"""Ooops! Unfortunately, a fatal error occurred and {APP_NAME} has stopped.
Please share the following informations with {COMPANY} support: we’ll do our best to fix it!
"""
    info = QLabel(text)
    info.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
    layout.addWidget(info)

    # Display CLI arguments
    if sys.argv[1:]:
        text = "Command line arguments:"
        label_cli = QLabel(text)
        label_cli.setAlignment(Qt.AlignVCenter)
        cli_args = QTextEdit()
        cli_args.setStyleSheet(css)
        cli_args.setReadOnly(True)
        args = "\n".join(arg for arg in sys.argv[1:])
        details.append(section(text, args))
        cli_args.setText(args)
        cli_args.setSizeAdjustPolicy(QTextEdit.AdjustToContents)
        layout.addWidget(label_cli)
        layout.addWidget(cli_args)

    # Display the exception
    text = "Exception:"
    label_exc = QLabel(text)
    label_exc.setAlignment(Qt.AlignVCenter)
    exception = QTextEdit()
    exception.setStyleSheet(css)
    exception.setReadOnly(True)
    exc_formatted = "".join(traceback.format_exception(*sys.exc_info()))
    details.append(section(text, exc_formatted))
    exception.setText(exc_formatted)
    layout.addWidget(label_exc)
    layout.addWidget(exception)

    # Display last lines from the memory log
    with suppress(Exception):
        from nxdrive.report import Report

        # Last 20th lines
        raw_lines = Report.export_logs(-20)
        lines = b"\n".join(raw_lines).decode(errors="replace")

        text = "Logs before the crash:"
        label_log = QLabel(text)
        details.append(section(text, lines))
        label_log.setAlignment(Qt.AlignVCenter)
        layout.addWidget(label_log)

        logs = QTextEdit()
        logs.setStyleSheet(css)
        logs.setReadOnly(True)
        logs.setLineWrapColumnOrWidth(4096)
        logs.setLineWrapMode(QTextEdit.FixedPixelWidth)
        logs.setText(lines)
        layout.addWidget(logs)

    # Buttons
    buttons = QDialogButtonBox()
    buttons.setStandardButtons(QDialogButtonBox.Ok)
    buttons.accepted.connect(dialog.close)
    layout.addWidget(buttons)

    def copy() -> None:
        """Copy details to the clipboard and change the text of the button. """
        copy_to_clipboard("\n".join(details))
        copy_paste.setText("Details copied!")

    # "Copy details" button
    with suppress(Exception):
        from nxdrive.utils import copy_to_clipboard

        copy_paste = buttons.addButton("Copy details", QDialogButtonBox.ActionRole)
        copy_paste.clicked.connect(copy)

    dialog.setLayout(layout)
    dialog.show()
    app.exec_()


def main() -> int:
    """ Entry point. """

    if sys.version_info < (3, 6):
        raise RuntimeError(f"{APP_NAME} requires Python 3.6+")

    try:
        ask_for_metrics_approval()
        # Setup Sentry even if the user did not allow it because it can be tweaked
        # later via the "use-sentry" parameter. It will be useless if Sentry is not installed first.
        setup_sentry()

        from nxdrive.commandline import CliHandler

        return CliHandler().handle(sys.argv[1:])
    except SystemExit as exc:
        if exc.code != 0:
            show_critical_error()
        return exc.code
    except:
        show_critical_error()
        return 1


sys.exit((main()))
