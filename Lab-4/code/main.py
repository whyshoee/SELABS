import os
import warnings

# Silence pygame's internal pkg_resources deprecation warning and greeting.
# These must be set BEFORE pygame is imported (GameEngine imports it).
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

from game.game_engine import GameEngine

if __name__ == "__main__":
    engine = GameEngine()
    engine.run()