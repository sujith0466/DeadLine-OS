"""
DeadlineOS — Async Task Foundation
====================================
Provides a lightweight foundation for running background orchestration
and agent tasks without blocking the main API thread.

Usage:
    from utils.async_task import run_async

    def my_long_task(user_id, data):
        # ... logic ...

    run_async(my_long_task, g.user_id, some_data)
"""

import logging
import threading
from flask import current_app

logger = logging.getLogger(__name__)


def run_async(func, *args, **kwargs):
    """
    Executes a function in a background thread, preserving the Flask
    application context so that database operations and app config
    can be accessed safely.

    Parameters
    ----------
    func : callable
        The function to execute in the background.
    *args :
        Positional arguments to pass to the function.
    **kwargs :
        Keyword arguments to pass to the function.

    Returns
    -------
    threading.Thread
        The started thread instance.
    """
    app = current_app._get_current_object()

    def background_task(app_context, f, *a, **kw):
        with app_context:
            try:
                f(*a, **kw)
            except Exception as e:
                logger.error(
                    "[async_task] Unhandled exception in background task '%s': %s",
                    f.__name__,
                    e,
                    exc_info=True,
                )

    thread = threading.Thread(
        target=background_task, args=(app.app_context(), func) + args, kwargs=kwargs
    )
    thread.daemon = True
    thread.start()
    return thread
