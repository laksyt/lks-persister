from persister.application import Application
from persister.config.config import Config

if __name__ == "__main__":
    Application(Config()).launch()
