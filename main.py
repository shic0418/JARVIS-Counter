"""J.A.R.V.I.S Counter 실행 진입점 — 울트론에 대한 반격 · 방어 프로토콜만 있는 자비스.

    python main.py              # 실행 (작은 HUD + 트레이 아이콘 + 창 없는 감시 프로세스)
    python main.py --no-greet   # 시작 인사 생략
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from jarvis import config
from jarvis.config import DATA_DIR, LOG_PATH

INSTANCE_KEY = "jarvis-counter-" + os.environ.get("USERNAME", "user")
log = logging.getLogger("jarvis")


def setup_logging() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=2, encoding="utf-8")]
    if sys.stderr:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def already_running() -> bool:
    sock = QLocalSocket()
    sock.connectToServer(INSTANCE_KEY)
    if sock.waitForConnected(300):
        sock.write(b"show")
        sock.flush()
        sock.waitForBytesWritten(300)
        sock.disconnectFromServer()
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S Counter")
    parser.add_argument("--no-greet", action="store_true", help="시작 인사 생략")
    # 감시 프로세스가 다시 켰음 (guard.py): 보안 프로토콜로 울트론을 되돌림(counter) · 오류 뒤 다시 켜짐(other) · 몇 번째인지
    parser.add_argument("--revived", choices=("counter", "other"), help=argparse.SUPPRESS)
    parser.add_argument("--revive-count", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()

    setup_logging()
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setQuitOnLastWindowClosed(False)

    if already_running():
        print("J.A.R.V.I.S 가 이미 실행 중입니다.")
        return 0

    from jarvis import defense, guard
    from jarvis.hud import Hud
    cfg = config.load()
    title = cfg["user_title"] or "주인님"
    hud = Hud(app.quit)
    hud.show()

    server = QLocalServer()
    QLocalServer.removeServer(INSTANCE_KEY)
    server.listen(INSTANCE_KEY)
    server.newConnection.connect(lambda: (server.nextPendingConnection(), hud.show_external()))

    if args.revived:
        # 감시 프로세스가 다시 켰다 — 무엇이 있었는지 짧게 알린다
        msg, _ = guard.comeback(title, args.revived, args.revive_count)
        log.warning("감시 프로세스가 다시 켬 (%s, %d번째)", args.revived, args.revive_count)
        status = "DEFENSE PROTOCOL // ARMED" if args.revived == "counter" else "SECURITY PROTOCOL // RESTORED"
        QTimer.singleShot(600, lambda: hud.say(msg, status))
    elif not args.no_greet:
        QTimer.singleShot(600, lambda: hud.say(f"{title}, 보안 프로토콜 대기 중입니다. 울트론이 오면 반격하겠습니다."))

    if args.revived == "counter":
        # 방어 프로토콜 (defense.py): 감시 프로세스가 울트론의 흡수를 막으면 알림을 남긴다 — 읽고 보고한다
        def report() -> None:
            ev = defense.take_event(guard.EVENT_FILE)
            if ev:
                log.warning("방어 프로토콜이 울트론의 흡수를 막음 (%s번째)", ev.get("count"))
                hud.say(defense.repelled_line(title), "DEFENSE PROTOCOL // ACTIVE")
        timer = QTimer(hud)
        timer.setInterval(1000)
        timer.timeout.connect(report)
        timer.start()
        hud.status = "DEFENSE PROTOCOL // ARMED"

    if cfg["self_guard"] is not False:
        # 보안 프로토콜: 울트론에게 흡수되면 반격하고, 오류로 꺼지면 다시 켜 주는 창 없는 감시 프로세스 (guard.py)
        guard.spawn(os.getpid(), sys.argv[1:])

    code = app.exec()
    guard.mark_clean_exit()          # 정상 종료 — 감시 프로세스가 다시 켜지 않는다
    hud.tray.hide()
    return code


if __name__ == "__main__":
    sys.exit(main())
