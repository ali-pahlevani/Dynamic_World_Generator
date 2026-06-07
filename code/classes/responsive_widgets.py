from PyQt5.QtWidgets import QWidget, QPushButton, QBoxLayout, QSizePolicy


class WrapButton(QPushButton):
    """QPushButton that breaks multi-word text to two lines when narrow.

    Below _WRAP_WIDTH px the text is split into two lines so the button
    stays readable without clipping.  Above the threshold the original
    single-line text is restored automatically.
    """
    _WRAP_WIDTH = 110   # button width (px) below which wrapping activates

    def __init__(self, text, role=None, parent=None):
        super().__init__(text, parent)
        self._full_text = text
        self._words = text.split()
        if role:
            self.setProperty("btnRole", role)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if len(self._words) < 2:
            return
        w = event.size().width()
        wants_wrap = (w < self._WRAP_WIDTH)
        # Split at the midpoint so neither line is too long
        mid = len(self._words) // 2
        wrapped = '\n'.join([
            ' '.join(self._words[:mid]),
            ' '.join(self._words[mid:]),
        ])
        cur = self.text()
        if wants_wrap and cur == self._full_text:
            self.setText(wrapped)
        elif not wants_wrap and cur != self._full_text:
            self.setText(self._full_text)


class ButtonRow(QWidget):
    """Two or more buttons arranged horizontally.

    When the widget's own width drops below _STACK_WIDTH the direction
    switches to vertical so buttons stack rather than overlap.  When
    width recovers the horizontal layout is restored.
    """
    _STACK_WIDTH = 190  # ButtonRow width (px) below which buttons stack

    def __init__(self, *buttons, parent=None):
        super().__init__(parent)
        self._buttons = buttons
        self._layout = QBoxLayout(QBoxLayout.LeftToRight, self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        for b in buttons:
            self._layout.addWidget(b)
        self._horiz = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        horiz = event.size().width() >= self._STACK_WIDTH
        if horiz != self._horiz:
            self._horiz = horiz
            self._layout.setDirection(
                QBoxLayout.LeftToRight if horiz else QBoxLayout.TopToBottom
            )
