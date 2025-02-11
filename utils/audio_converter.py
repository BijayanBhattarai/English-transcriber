import os
import ffmpeg
from config.settings import INPUT_FOLDER, OUTPUT_FOLDER

def convert_audio(file):
    try:
        # Create input and output paths
        input_filename = file.filename
        base_name = os.path.splitext(input_filename)[0]
        output_filename = f"{base_name}.mp3"
        
        input_path = os.path.join(INPUT_FOLDER, input_filename)
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Save uploaded file
        file.save(input_path)
        
        # Convert to MP3 using ffmpeg
        try:
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(stream, output_path, 
                                 acodec='libmp3lame', 
                                 ab='192k',  # Set bitrate
                                 ar='44100'  # Set sample rate
                                 )
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            # Clean up input file
            os.remove(input_path)
            
            return {
                'success': True,
                'filename': output_filename
            }
            
        except ffmpeg.Error as e:
            return {
                'success': False,
                'error': f"FFmpeg error: {e.stderr.decode()}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        # Ensure input file is cleaned up even if conversion fails
        if os.path.exists(input_path):
            os.remove(input_path)