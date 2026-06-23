"""Flask application factory."""

from __future__ import annotations

import atexit
import os
from pathlib import Path

from flask import Flask

from .controller import VisualizationController
from .hardware import create_strip
from .routes import web


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "development-only-change-me"),
        MAX_CONTENT_LENGTH=32 * 1024 * 1024,
        UPLOAD_FOLDER=str(Path(app.root_path).parent / "uploads"),
        LED_COUNT=144,
        LED_PIN=18,
        LED_FREQ_HZ=800_000,
        LED_DMA=10,
        LED_BRIGHTNESS=255,
        LED_INVERT=False,
        LED_CHANNEL=0,
        AUDIO_RATE=44_100,
        AUDIO_CHUNK_SIZE=1024,
        AUDIO_INPUT_DEVICE_INDEX=None,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    strip = create_strip(app.config)
    controller = VisualizationController(strip=strip, config=app.config)
    app.extensions["visualizer"] = controller

    app.register_blueprint(web)
    atexit.register(controller.shutdown)
    return app
