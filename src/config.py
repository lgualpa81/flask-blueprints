"""App configuration."""
from os import environ, path
import logging.config
from datetime import timedelta

DEFAULT_ENV = environ.get('DEFAULT_ENV')


class BaseConfig:
    """Set Flask configuration vars from .env file."""
    # General Config
    FLASK_ENV = 'development'
    ENV = 'development'
    # environ.get('SECRET_KEY')
    SECRET_KEY = 't4pS3cr3TK2y'

    FLASK_DEBUG = True
    DEBUG = True

    # Database configuration
    SQLALCHEMY_DATABASE_URI = environ.get('DB_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    URL_AUTH_COMMERCE_NEW_JWT = environ.get("URL_AUTH_COMMERCE_NEW_JWT")
    URL_AUTH_COMMERCE_CHECK_JWT = environ.get("URL_AUTH_COMMERCE_CHECK_JWT")
    URL_AUTH_COMMERCE_REFRESH_JWT = environ.get(
        "URL_AUTH_COMMERCE_REFRESH_JWT")

    URL_PAYMENT_CARD_VOID = environ.get("URL_PAYMENT_CARD_VOID")

    # NOTIFICATION MKT
    MKT_CRM_NOTIFICATION = environ.get("MKT_CRM_NOTIFICATION")
    MONITOR_TASKS_TRACER = environ.get("MONITOR_TASKS_TRACER")

    # URL_CHECKOUT
    URL_CHECKOUT_WEB = environ.get("URL_CHECKOUT_WEB")

    SVC_COMMERCE_UPLOAD_FILES_GCP = environ.get("SVC_COMMERCE_UPLOAD_FILES_GCP")


class LocalConfig(BaseConfig):
    # docker, ip container (sudo docker network inspect bridge)
    pass


class DevConfig(BaseConfig):
    pass


class ProdConfig(BaseConfig):
    FLASK_ENV = 'production'
    DEBUG = False
    SECRET_KEY = 'el3U7U0GB7jC3Cy2-1hg55RbwA7Eo36jtoXBQR_qMqk'


app_config = {"local": LocalConfig,
              "development": DevConfig,
              "production": ProdConfig}
