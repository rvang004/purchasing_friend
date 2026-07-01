import socket
import sys

def check_port(host, port):
    """Check if a port is listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

# Check localhost
if check_port('127.0.0.1', 8100):
    print("[OK] Server is listening on http://127.0.0.1:8100")
    print("Try: http://localhost:8100 in your browser")
else:
    print("[ERROR] Server NOT listening on port 8100")
    print("Check if the server process is running")
    sys.exit(1)
