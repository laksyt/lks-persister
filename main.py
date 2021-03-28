from persister.application import Application
from persister.startup.config import Config


if __name__ == "__main__":
    Application(Config()).launch()
