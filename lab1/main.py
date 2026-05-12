
from flask import Flask

from api.books import books_bp


def create_app() -> Flask:

    app = Flask(__name__)
    app.json.ensure_ascii = False

    app.register_blueprint(books_bp, url_prefix="/api/v1")

    @app.get("/")
    def index():

        return {"status": "ok", "service": "Library API", "version": "1.0.0"}, 200

    return app


app = create_app()


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5001, debug=True)
