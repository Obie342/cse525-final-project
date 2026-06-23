from audio_led_visualizer import create_app


def test_home_page_loads():
    app = create_app({"TESTING": True})
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert b"Audio LED Visualizer" in response.data


def test_unknown_page_returns_custom_404():
    app = create_app({"TESTING": True})
    response = app.test_client().get("/does-not-exist")
    assert response.status_code == 404
    assert b"Page Not Found" in response.data
