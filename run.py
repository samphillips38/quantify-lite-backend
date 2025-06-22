from app import create_app
from app import database_models

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001) 