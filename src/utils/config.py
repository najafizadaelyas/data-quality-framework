"""Config loader — reads from environment / .env file."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "warehouse")
    db_user: str = os.getenv("DB_USER", "dq_user")
    db_password: str = os.getenv("DB_PASSWORD", "")

    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    alert_email: str = os.getenv("ALERT_EMAIL", "")

    ge_docs_bucket: str = os.getenv("GE_DOCS_BUCKET", "")
    ge_docs_backend: str = os.getenv("GE_DOCS_BACKEND", "local")

    openlineage_url: str = os.getenv("OPENLINEAGE_URL", "http://localhost:5000")
    openlineage_namespace: str = os.getenv("OPENLINEAGE_NAMESPACE", "data_quality")

    env: str = os.getenv("ENV", "dev")


config = Config()
