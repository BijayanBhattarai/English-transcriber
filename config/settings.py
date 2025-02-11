import os

# File upload settings
ALLOWED_EXTENSIONS = {
    # Audio formats
    'wav', 'mp3', 'ogg', 'm4a', 'flac', 'aac', 
    # Video formats
    'mov', 'mp4', 'avi', 'mkv', 'wmv'
}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 16MB max file size
UPLOAD_SIZE_LIMIT = {
    'MB': 500,
    'BYTES': 500 * 1024 * 1024
}
# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'input')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'output')