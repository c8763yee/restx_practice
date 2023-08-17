class BaseCeleryConfig:
    timezone = "Asia/Taipei"
    backend_url = "redis://localhost:6379/0"
    broker_url = "redis://localhost:6379/1"
    broker_connection_retry_on_startup = False


# flask
class BaseFlaskConfig:
    CELERY_BROKER_URL = BaseCeleryConfig.broker_url
    HOST = "0.0.0.0"
    PORT = 8763
    DEBUG = False
    ENV = "production"
    SECRET_KEY = __import__("os").urandom(24)


class DevelopmentFlaskConfig(BaseFlaskConfig):
    DEBUG = True
    ENV = "development"
