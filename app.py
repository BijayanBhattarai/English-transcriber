from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
#from werkzeug.exceptions import RequestEntityTooLarge
import os
from dotenv import load_dotenv
from utils.audio_converter import convert_audio
from utils.transcriber import AudioTranscriber

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 16MB max file size

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'input')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'output')

# Ensure upload directories exist
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a', 'flac', 'mov', 'mp4', 'avi', 'mkv', 'wmv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/download/<filename>')
def download_file(filename):
    """Download a file from the output folder"""
    try:
        return send_from_directory(
            OUTPUT_FOLDER, 
            filename, 
            as_attachment=True  # This will prompt download instead of playing in browser
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error downloading file: {str(e)}'
        }), 404
@app.route('/')
def index():
    # Get list of converted files
    converted_files = []
    if os.path.exists(OUTPUT_FOLDER):
        converted_files = [f for f in os.listdir(OUTPUT_FOLDER) 
                         if os.path.isfile(os.path.join(OUTPUT_FOLDER, f)) 
                         and f.endswith('.mp3')]
    return render_template('index.html', files=converted_files)

@app.route('/convert', methods=['POST'])
def convert():
    if 'audio' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        })

    files = request.files.getlist('audio')
    results = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            
            # Convert the audio file
            result = convert_audio(file)
            results.append(result)
        else:
            results.append({
                'success': False,
                'error': f'Invalid file type for {file.filename}. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            })
    
    # Return all results
    return jsonify({
        'success': True,
        'results': results
    })

@app.route('/get_audio/<filename>')
def get_audio(filename):
    """Serve audio files from the output directory"""
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/transcribe/<filename>')
def transcribe_file(filename):
    try:
        transcriber = AudioTranscriber(
            speech_key=os.getenv('AZURE_SPEECH_KEY'),
            service_region=os.getenv('AZURE_REGION')
        )
        
        result = transcriber.transcribe(filename)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

        # Initialize transcriber
        transcriber = AudioTranscriber(speech_key, service_region)
        
        # Perform transcription
        result = transcriber.transcribe(filename)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Transcription error: {str(e)}'
        })
@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a converted audio file"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': f'File {filename} deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error deleting file: {str(e)}'
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'success': False,
        'error': 'File is too large. Maximum size is 16MB'
    }), 413

@app.errorhandler(500)
def server_error(e):
    """Handle internal server errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error occurred'
    }), 500

def cleanup_old_files():
    """Clean up old input files that weren't properly deleted"""
    try:
        for filename in os.listdir(INPUT_FOLDER):
            file_path = os.path.join(INPUT_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Error cleaning up files: {str(e)}")

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)  # Changed port to 5001
    except Exception as e:
        print(f"Error starting server: {e}")
        # Try alternative ports
        for port in [5002, 5003, 8080, 8000]:
            try:
                print(f"Trying port {port}...")
                app.run(debug=True, host='0.0.0.0', port=port)
                break
            except Exception:
                continue
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)