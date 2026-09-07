import argparse
import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()

# Determine environment from FLASK_ENV or default to development
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Flask web application.')
    parser.add_argument('--host', default=os.environ.get('APP_HOST', '127.0.0.1'), help='Host to bind to.')
    parser.add_argument('--port', type=int, default=int(os.environ.get('APP_PORT', 5050)), help='Port to bind to (default: 5050).')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    
    args = parser.parse_args()
    
    if env == 'production':
        # Use Waitress for production on Windows
        try:
            from waitress import serve
            print(f"Starting server with Waitress on {args.host}:{args.port}")
            serve(app, host=args.host, port=args.port)
        except ImportError:
            print("Waitress not installed. Falling back to Flask development server.")
            app.run(host=args.host, port=args.port, debug=args.debug)
    else:
        # Use Flask development server
        app.run(host=args.host, port=args.port, debug=args.debug or app.config['DEBUG'])
