from app.main import app as application

def create_app():
    return application

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=8000) 