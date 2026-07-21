import json
import logging
import os

logger = logging.getLogger("app.secrets")


def load_secrets_into_environment(prefix: str, region_name: str) -> None:
    """Fetch the JSON secret at f"{prefix}/app" from AWS Secrets Manager and
    merge it into os.environ.

    Per policy, values from Secrets Manager take precedence over whatever is
    already in the environment (a stale value baked into a systemd
    EnvironmentFile must never silently win over the source of truth in
    Secrets Manager). The bootstrap toggles themselves (ENVIRONMENT,
    USE_AWS_SECRETS_MANAGER, AWS_SECRETS_MANAGER_PREFIX, AWS_REGION) are read
    from the environment before this function runs, since something has to
    tell us which secret to fetch in the first place.
    """
    if not prefix:
        logger.warning("USE_AWS_SECRETS_MANAGER is enabled but AWS_SECRETS_MANAGER_PREFIX is empty; skipping.")
        return

    secret_name = f"{prefix.rstrip('/')}/app"

    try:
        import boto3
    except ImportError:
        logger.error("boto3 is required to load secrets from AWS Secrets Manager.")
        return

    try:
        client_kwargs: dict = {"region_name": region_name}
        access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        session_token = os.environ.get("AWS_SESSION_TOKEN")
        if access_key:
            client_kwargs["aws_access_key_id"] = access_key
        if secret_access_key:
            client_kwargs["aws_secret_access_key"] = secret_access_key
        if session_token:
            client_kwargs["aws_session_token"] = session_token

        client = boto3.client("secretsmanager", **client_kwargs)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString")
        if not secret_string:
            logger.warning("Secret %s has no SecretString payload.", secret_name)
            return

        secret_values = json.loads(secret_string)
        for key, value in secret_values.items():
            os.environ[key] = str(value)
        logger.info("Loaded %d values from Secrets Manager secret %s", len(secret_values), secret_name)
    except Exception:
        logger.exception("Failed to load secrets from AWS Secrets Manager secret=%s", secret_name)
