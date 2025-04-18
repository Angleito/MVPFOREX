"""Main entry point for the Flask application with diagnostics."""
import sys
import os
print("--- application.py starting ---", flush=True)
print(f"CWD: {os.getcwd()}", flush=True)
print(f"sys.path: {sys.path}", flush=True)
sys.stdout.flush()
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from app import create_app


print("--- Importing create_app successful ---", flush=True)
sys.stdout.flush()

app = create_app()

# Health check route for deployment verification
from flask import Flask

@app.route("/")
def health():
    return "MVPFOREX backend is running!", 200

print("--- create_app() returned successfully ---", flush=True)
sys.stdout.flush()

if __name__ == '__main__':
    print("--- Running locally via __main__ ---", flush=True)
    sys.stdout.flush()
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000, help='Port to run the Flask app on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the Flask app on')
    args, _ = parser.parse_known_args()
    print(f"--- Starting Flask on {args.host}:{args.port} ---", flush=True)
    sys.stdout.flush()
    app.run(debug=True, port=args.port, host=args.host)
else:
    print("--- Gunicorn importing 'app' object ---", flush=True)
    sys.stdout.flush()
