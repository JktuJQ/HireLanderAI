import dotenv

SECRETS: dict[str, str] = dotenv.dotenv_values()

DEBUG: bool = True
HOST: str = "127.0.0.1"
PORT: int = 5000