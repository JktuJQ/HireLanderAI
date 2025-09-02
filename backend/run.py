from application import socketio, application


def run(port: int = 8080, host: str = "127.0.0.1"):
    """Runs application on "http://{host}:{port}/"""
    socketio.run(app=application, port=port, host=host, debug=True)


if __name__ == "__main__":
    run(port=5000, host="127.0.0.1")