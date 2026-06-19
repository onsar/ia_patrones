import sys
import os
import logging

# Ensure project root is on sys.path so tests can import local modules like `services`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def pytest_configure(config):
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, "pytest.log")

    handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    config._pytest_log_handler = handler


def pytest_unconfigure(config):
    handler = getattr(config, "_pytest_log_handler", None)
    if handler is not None:
        logging.getLogger().removeHandler(handler)
        handler.close()


def pytest_sessionfinish(session, exitstatus):
    terminal_reporter = session.config.pluginmanager.getplugin("terminalreporter")
    if terminal_reporter is None or not hasattr(terminal_reporter, "stats"):
        return

    stats = terminal_reporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))
    errors = len(stats.get("error", []))

    logger = logging.getLogger(__name__)
    logger.info(
        "Pytest finished: passed=%s failed=%s skipped=%s errors=%s exitstatus=%s",
        passed,
        failed,
        skipped,
        errors,
        exitstatus,
    )
