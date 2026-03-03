"""
Seoul Watch Admin API Configuration
"""
import os
import secrets

# Generate a random secret key if not set
SECRET_KEY = os.environ.get('SEOULWATCH_SECRET_KEY', secrets.token_hex(32))

# Admin password (should be set via environment variable in production)
ADMIN_PASSWORD = os.environ.get('SEOULWATCH_ADMIN_PASSWORD', 'seoulwatch2024')

# JWT settings
JWT_EXPIRY_HOURS = 24

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.json')
IMAGES_DIR = os.path.join(BASE_DIR, 'images', 'products')

# Upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
