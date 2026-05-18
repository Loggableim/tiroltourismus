import sys
try:
    import requests
    print(f"requests OK v{requests.__version__}")
except ImportError:
    print("no requests")
    sys.exit(1)
