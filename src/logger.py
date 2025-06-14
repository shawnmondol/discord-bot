import logging
from logging.handlers import RotatingFileHandler

# 1) Basic console logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)

# 2) Rotating file handler
file_handler = RotatingFileHandler(
    "logs/discord-bot.log", maxBytes=5_000_000, backupCount=3
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
))
logging.getLogger().addHandler(file_handler)
