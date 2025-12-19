"""
Sentry logging configuration for Epic Events CRM
"""

import os
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize Sentry SDK for error tracking and logging"""
    sentry_dsn = os.getenv('SENTRY_DSN')

    if not sentry_dsn:
        logger.warning("SENTRY_DSN not configured. Sentry logging is disabled.")
        return False

    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[sentry_logging],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment=os.getenv('ENVIRONMENT', 'development'),
        release=os.getenv('APP_VERSION', '1.0.0')
    )

    logger.info("Sentry initialized successfully")
    return True


def capture_exception(exception):
    """Capture and send exception to Sentry"""
    sentry_sdk.capture_exception(exception)
    logger.error(f"Exception captured: {exception}")


def capture_message(message, level='info'):
    """Capture and send message to Sentry"""
    sentry_sdk.capture_message(message, level=level)
    logger.log(getattr(logging, level.upper(), logging.INFO), message)


def log_user_action(action_type, user_info, details=None):
    """Log user actions to Sentry"""
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("action_type", action_type)
        scope.set_user({
            "id": user_info.get('user_id'),
            "email": user_info.get('email'),
            "username": user_info.get('name')
        })

        if details:
            scope.set_extra("details", details)

        message = f"User action: {action_type}"
        if details:
            message += f" - {details}"

        sentry_sdk.capture_message(message, level='info')
        logger.info(f"[{action_type}] User: {user_info.get('name', 'Unknown')} - {details or 'No details'}")


def log_user_creation(user_info, created_user_info):
    """Log user creation event"""
    log_user_action(
        action_type="user_created",
        user_info=user_info,
        details=f"Created user: {created_user_info.get('name')} ({created_user_info.get('email')}) - Department: {created_user_info.get('department')}"
    )


def log_user_modification(user_info, modified_user_info, changes):
    """Log user modification event"""
    log_user_action(
        action_type="user_modified",
        user_info=user_info,
        details=f"Modified user: {modified_user_info.get('name')} - Changes: {changes}"
    )


def log_user_deletion(user_info, deleted_user_info):
    """Log user deletion event"""
    log_user_action(
        action_type="user_deleted",
        user_info=user_info,
        details=f"Deleted user: {deleted_user_info.get('name')} ({deleted_user_info.get('email')})"
    )


def log_contract_signed(user_info, contract_info):
    """Log contract signature event"""
    log_user_action(
        action_type="contract_signed",
        user_info=user_info,
        details=f"Contract #{contract_info.get('id')} signed - Client: {contract_info.get('client_name')} - Amount: {contract_info.get('total_amount')}"
    )


def sentry_track(action_type):
    """Decorator to track function calls with Sentry"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                capture_exception(e)
                raise
        return wrapper
    return decorator
