import asyncio
import sys

import qasync
from PyQt6.QtWidgets import QApplication

from src.config import APP_NAME
from src.utils.logger import setup_logging, get_logger


def main():
    setup_logging()
    logger = get_logger("main")
    logger.info("%s starting...", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    from src.app import App
    sage_app = App()

    logger.info("Event loop starting")
    with loop:
        exit_code = loop.run_forever()
    logger.info("Exiting with code %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
