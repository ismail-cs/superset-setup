import logging
import os
from typing import Optional

from superset.utils.date_parser import get_since_until
from superset.utils.core import merge_extra_filters

from flask import Flask, redirect
from flask_appbuilder import expose, IndexView
from superset.superset_typing import FlaskResponse

from cachelib.file import FileSystemCache
from celery.schedules import crontab

logger = logging.getLogger()


def get_env_variable(var_name: str, default: Optional[str] = None) -> str:
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = "The environment variable {} was missing, abort...".format(
                var_name
            )
            raise OSError(error_msg)


DATABASE_DIALECT = get_env_variable("DATABASE_DIALECT")
DATABASE_USER = get_env_variable("DATABASE_USER")
DATABASE_PASSWORD = get_env_variable("DATABASE_PASSWORD")
DATABASE_HOST = get_env_variable("DATABASE_HOST")
DATABASE_PORT = get_env_variable("DATABASE_PORT")
DATABASE_DB = get_env_variable("DATABASE_DB")

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = "{}://{}:{}@{}:{}/{}".format(
    DATABASE_DIALECT,
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_DB,
)

REDIS_HOST = get_env_variable("REDIS_HOST")
REDIS_PORT = get_env_variable("REDIS_PORT")
REDIS_PASSWORD = get_env_variable("REDIS_PASSWORD")
REDIS_CELERY_DB = get_env_variable("REDIS_CELERY_DB", "0")
REDIS_RESULTS_DB = get_env_variable("REDIS_RESULTS_DB", "1")

RESULTS_BACKEND = FileSystemCache("/app/superset_home/sqllab")

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_PASSWORD": REDIS_PASSWORD,
    "CACHE_REDIS_DB": REDIS_RESULTS_DB,
}
DATA_CACHE_CONFIG = CACHE_CONFIG


class CeleryConfig:
    broker_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    imports = ("superset.sql_lab",)
    result_backend = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=10, hour=0),
        },
    }


CELERY_CONFIG = CeleryConfig

FEATURE_FLAGS = {"ALERT_REPORTS": True}
ALERT_REPORTS_NOTIFICATION_DRY_RUN = True
WEBDRIVER_BASEURL = "http://superset:8088/"
WEBDRIVER_BASEURL_USER_FRIENDLY = WEBDRIVER_BASEURL

SQLLAB_CTAS_NO_LIMIT = True

try:
    import superset_config_docker
    from superset_config_docker import *  # noqa

    logger.info(
        f"Loaded your Docker configuration at " f"[{superset_config_docker.__file__}]"
    )
except ImportError:
    logger.info("Using default Docker config...")

ENABLE_PROXY_FIX = True
FORWARDED_ALLOW_IPS = "*"
PREFERRED_URL_SCHEME = "http"
SUPERSET_WEBSERVER_DOMAINS = "report-jamunahris.jamunabank.com.bd"
WTF_CSRF_ENABLED = False
SESSION_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = False
TALISMAN_ENABLED = False

SECRET_KEY = get_env_variable('SECRET_KEY')

SUPERSET_WEBSERVER_DOMAINS = ["report-jamunahris.jamunabank.com.bd"]

#MAPBOX_API_KEY = get_env_variable('MAPBOX_API_KEY')

DEFAULT_FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "ENABLE_TEMPLATE_REMOVE_FILTERS": True,
    "VERSIONED_EXPORT": True,
    "GENERIC_CHART_AXES": True,
}


def time_filter() -> Optional[str]:
    from superset.views.utils import get_form_data
    form_data, _ = get_form_data()
    merge_extra_filters(form_data)
    time_range = form_data.get("time_range")
    since, until = get_since_until(time_range)
    time_format = '%Y-%m-%d %H:%M:%S'
    if not until:
        return None
    until = until.strftime(time_format)
    if not since:
        return '<= \'{}\''.format(until)
    since = since.strftime(time_format)
    return [since, until]

#custome filter data for inner query
def custome_split_filter(column: str) -> str:
    from superset.views.utils import get_form_data
    form_data, _ = get_form_data()
    merge_extra_filters(form_data)
    filters = form_data.get('filters')
    matching_index = None
    response = []
    for index, filter_dict in enumerate(filters):
        if filter_dict['col'] == column:
            matching_index = index
            break  # Once a match is found, exit the loop
    if matching_index != None:
        for v in filters[matching_index]['val']:
            response.append(v.split('.')[0])
        return ', '.join(response)
    else:
        matching_index

def custome_filter(column: str) -> str:
    from superset.views.utils import get_form_data
    form_data, _ = get_form_data()
    merge_extra_filters(form_data)
    filters = form_data.get('filters')
    matching_index = None
    response = []
    for index, filter_dict in enumerate(filters):
        if filter_dict['col'] == column:
            matching_index = index
            break  # Once a match is found, exit the loop
    if matching_index != None:
        return ', '.join(f'"{s}"' for s in filters[matching_index]['val'])
    else:
        matching_index


class SupersetDashboardIndexView(IndexView):
    @expose("/")
    def index(self) -> FlaskResponse:
        return redirect("/dashboard/list/")

FAB_INDEX_VIEW = f"{SupersetDashboardIndexView.__module__}.{SupersetDashboardIndexView.__name__}"

# A dictionary of items that gets merged into the Jinja context for
# SQL Lab. The existing context gets updated with this dictionary,
# meaning values for existing keys get overwritten by the content of this
# dictionary. Exposing functionality through JINJA_CONTEXT_ADDONS has security
# implications as it opens a window for a user to execute untrusted code.
# It's important to make sure that the objects exposed (as well as objects attached
# to those objets) are harmless. We recommend only exposing simple/pure functions that
# return native types.
JINJA_CONTEXT_ADDONS = {
    'time_filter': time_filter,
    'custome_filter': custome_filter,
    'custome_split_filter': custome_split_filter
}
# CSV Download encording fix
CSV_EXPORT = {
  "encoding": "utf_8_sig"
}


SQL_MAX_ROW = 100000

