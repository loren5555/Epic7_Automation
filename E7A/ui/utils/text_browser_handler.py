import logging

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QTextBrowser, QScrollBar


class QTextBrowserHandler(logging.Handler):
    """
    Custom logging handler to display logs in a QTextBrowser widget.
    """
    def __init__(self, text_browser: QTextBrowser):
        super().__init__()
        self.text_browser: QTextBrowser = text_browser
        self.auto_scroll = False
        self.vertical_scroll_bar: QScrollBar = self.text_browser.verticalScrollBar()
        self.vertical_scroll_bar.valueChanged.connect(self.check_scroll_position)

    def check_scroll_position(self):
        max_value = self.vertical_scroll_bar.maximum()
        current_value = self.vertical_scroll_bar.value()

        if current_value > max_value - 5:
            self.auto_scroll = True
        else:
            self.auto_scroll = False

    def emit(self, record):
        """
        Emit a log record to the QTextBrowser.
        """
        msg = self.format(record)
        self.text_browser.append(msg)
        if self.auto_scroll:
            self.vertical_scroll_bar.setValue(self.vertical_scroll_bar.maximum())
