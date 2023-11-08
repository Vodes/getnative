import logging
from rich.logging import RichHandler

__all__ = ["crit", "debug", "error", "exit", "info", "warn", "logger"]

FORMAT = "%(name)s | %(message)s"  #
logging.basicConfig(format=FORMAT, datefmt="[%X]", handlers=[RichHandler(markup=True, omit_repeated_times=False, show_path=False)])

logger = logging.getLogger("getnativef")
logger.setLevel(logging.DEBUG)


def _format_msg(msg: str, caller: any) -> str:
    if caller and not isinstance(caller, str):
        caller = caller.__class__.__qualname__ if hasattr(caller, "__class__") and caller.__class__.__name__ not in ["function", "method"] else caller
        caller = caller.__name__ if not isinstance(caller, str) else caller
    return msg if caller is None else f"[bold]{caller}:[/] {msg}"


def debug(msg: str, caller: any = None):
    message = _format_msg(msg, caller)
    logger.debug(message)


def info(msg: str, caller: any = None):
    message = _format_msg(msg, caller)
    logger.info(message)


def warn(msg: str, caller: any = None, sleep: int = 0):
    message = _format_msg(msg, caller)
    logger.warning(message)
    if sleep:
        time.sleep(sleep)


def error(msg: str, caller: any = None) -> Exception:
    message = _format_msg(msg, caller)
    logger.error(message)
    return Exception(message)
