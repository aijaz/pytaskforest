import os
from pytf_flask import create_app

flask_app = create_app(os.getenv('FLASK_ENV') or 'default')
if __name__ == "__main__":
    flask_app.run(host='127.0.0.1', port=8080, debug=True)
