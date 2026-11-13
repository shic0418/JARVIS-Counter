"""작은 자비스 HUD — 반격 전용 자비스의 유일한 창.

울트론은 창 제목이 정확히 'J.A.R.V.I.S' 인 파이썬 창을 자비스로 알아본다 (Ultron-main/jarvis/rival.py).
이 창은 숨지 않는다 — 울트론에게 흡수당한 뒤 안에서 깨어나 되찾는 것이 보안 프로토콜이기 때문이다.
크기와 엠블럼 자리는 원래 자비스의 '작게 보기' (230x356, 엠블럼은 위쪽 가운데) 와 같다 — 반격 장면의 고리가
이 엠블럼으로 날아와 겹친다 (counter.emblem_in).
"""
from __future__ import annotations

import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from . import counter as C
from .counter_view import _c, draw_emblem

TITLE = "J.A.R.V.I.S"          # 울트론이 찾는 창 제목 그대로 (tests/test_guard.py 가 확인한다)
SIZE = (230, 356)              # 원래 자비스의 작게 보기와 같은 크기 — 반격 장면의 고리가 엠블럼에 정확히 겹친다


def emblem_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    g = QPainter(pm)
    g.setRenderHint(QPainter.Antialiasing)
    draw_emblem(g, QPointF(32, 32), 28, 0.0, 1.0)
    g.end()
    return QIcon(pm)


class Hud(QWidget):
    def __init__(self, on_quit) -> None:
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowTitle(TITLE)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(*SIZE)
        self.status = "SECURITY PROTOCOL // STANDBY"
        self.message = ""
        self._drag: QPointF | None = None
        self._t0 = time.monotonic()
        icon = emblem_icon()
        self.setWindowIcon(icon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("J.A.R.V.I.S — 보안 프로토콜")
        menu = QMenu()
        show = QAction("보이기", menu)
        show.triggered.connect(self.show_external)
        quit_ = QAction("종료", menu)
        quit_.triggered.connect(on_quit)
        menu.addAction(show)
        menu.addAction(quit_)
        self._menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.show_external() if reason == QSystemTrayIcon.Trigger else None)
        self.tray.show()
        timer = QTimer(self)
        timer.setInterval(33)
        timer.timeout.connect(self.update)
        timer.start()
        self._place()

    def _place(self) -> None:
        scr = QApplication.primaryScreen().availableGeometry()
        self.move(scr.right() - SIZE[0] - 24, scr.top() + 48)

    def show_external(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def say(self, text: str, status: str | None = None) -> None:
        """말 대신 글로 알린다 (반격 전용 자비스는 음성이 없다). 트레이 알림도 띄운다."""
        self.message = text
        if status:
            self.status = status
        self.tray.showMessage("J.A.R.V.I.S", text, QSystemTrayIcon.Information, 8000)
        self.update()

    # -------------------------------------------------------------- 그리기
    def paintEvent(self, _e) -> None:
        w, h = self.width(), self.height()
        t = time.monotonic() - self._t0
        g = QPainter(self)
        g.setRenderHint(QPainter.Antialiasing)
        g.setPen(QPen(_c(C.CYAN, 0.55), 1.2))
        g.setBrush(QColor(4, 14, 24, 215))
        g.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 14, 14)
        cx, cy, r = C.emblem_in((0.0, 0.0, float(w), float(h)))
        draw_emblem(g, QPointF(cx, cy), r * 0.86, t, 1.0)
        top = cy + r
        g.setPen(_c(C.CYAN_HOT, 0.95))
        g.setFont(QFont("Segoe UI", 13, QFont.Bold))
        g.drawText(QRectF(0, top + 4, w, 24), Qt.AlignHCenter, TITLE)
        g.setPen(_c(C.CYAN, 0.75))
        g.setFont(QFont("Consolas", 7))
        g.drawText(QRectF(0, top + 30, w, 16), Qt.AlignHCenter, self.status)
        if self.message:
            g.setPen(_c(C.CYAN_HOT, 0.9))
            g.setFont(QFont("Malgun Gothic", 8))
            g.drawText(QRectF(14, top + 50, w - 28, h - top - 58), Qt.AlignHCenter | Qt.TextWordWrap, self.message)
        g.end()

    # -------------------------------------------------------------- 끌어 옮기기 · 메뉴
    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition() - QPointF(self.pos())

    def mouseMoveEvent(self, e) -> None:
        if self._drag is not None:
            p = e.globalPosition() - self._drag
            self.move(int(p.x()), int(p.y()))

    def mouseReleaseEvent(self, _e) -> None:
        self._drag = None

    def contextMenuEvent(self, e) -> None:
        self._menu.exec(e.globalPos())
