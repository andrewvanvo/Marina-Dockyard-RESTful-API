from flask import Flask, request
import boat
import load
import user

app = Flask(__name__)
app.register_blueprint(boat.bp)
app.register_blueprint(load.bp)
app.register_blueprint(user.bp)


@app.route('/')
def index():
    return "Andrew Vo's Boat Management API"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
