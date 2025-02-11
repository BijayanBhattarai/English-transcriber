import os
import azure.cognitiveservices.speech as speechsdk
import ffmpeg
from pydub import AudioSegment
from config.settings import OUTPUT_FOLDER

class AudioTranscriber:
    def __init__(self, speech_key, service_region):
        if not speech_key or not service_region:
            raise ValueError("Azure Speech Key and Region are required")
        
        self.speech_key = speech_key
        self.service_region = service_region
        self.chunk_length_ms = 30000  # 30 seconds per chunk

    def split_audio(self, audio_path):
        """Split audio into smaller chunks"""
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_path)
            chunks = []
            
            # Split audio into chunks
            for i in range(0, len(audio), self.chunk_length_ms):
                chunk = audio[i:i + self.chunk_length_ms]
                chunk_path = f"{audio_path}_chunk_{i//self.chunk_length_ms}.wav"
                chunk.export(chunk_path, format="wav")
                chunks.append(chunk_path)
            
            return chunks
        except Exception as e:
            print(f"Error splitting audio: {str(e)}")
            return None

    def prepare_chunk(self, chunk_path):
        """Prepare audio chunk for transcription"""
        try:
            temp_path = chunk_path + '_prepared.wav'
            
            # Convert to required format
            stream = ffmpeg.input(chunk_path)
            stream = ffmpeg.output(
                stream,
                temp_path,
                acodec='pcm_s16le',
                ac=1,
                ar='16000',
                loglevel='error'
            )
            ffmpeg.run(stream, overwrite_output=True)
            
            return temp_path
        except Exception as e:
            print(f"Error preparing chunk: {str(e)}")
            return None

    def transcribe_chunk(self, chunk_path):
        """Transcribe a single audio chunk"""
        try:
            # Prepare the chunk
            temp_path = self.prepare_chunk(chunk_path)
            if not temp_path:
                return None

            try:
                # Configure speech service
                speech_config = speechsdk.SpeechConfig(
                    subscription=self.speech_key,
                    region=self.service_region
                )
                speech_config.speech_recognition_language = "en-US"
                
                # Configure audio
                audio_config = speechsdk.AudioConfig(filename=temp_path)
                
                # Create recognizer
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config,
                    audio_config=audio_config
                )

                # Initialize variables
                chunk_text = []
                done = False
                had_error = False
                error_details = None

                # Define callbacks
                def handle_result(evt):
                    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                        chunk_text.append(evt.result.text)

                def handle_canceled(evt):
                    nonlocal done, had_error, error_details
                    done = True
                    had_error = True
                    if evt.reason == speechsdk.CancellationReason.Error:
                        error_details = evt.error_details

                def handle_stopped(evt):
                    nonlocal done
                    done = True

                # Connect callbacks
                recognizer.recognized.connect(handle_result)
                recognizer.canceled.connect(handle_canceled)
                recognizer.session_stopped.connect(handle_stopped)

                # Start recognition
                recognizer.start_continuous_recognition()
                while not done:
                    pass
                recognizer.stop_continuous_recognition()

                return ' '.join(chunk_text) if chunk_text else None

            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            print(f"Error transcribing chunk: {str(e)}")
            return None

    def transcribe(self, filename):
        """Transcribe complete audio file by processing chunks"""
        try:
            # Get full path
            audio_path = os.path.join(OUTPUT_FOLDER, filename)
            
            if not os.path.exists(audio_path):
                return {
                    'success': False,
                    'error': f'Audio file not found: {filename}'
                }

            # Split audio into chunks
            chunk_paths = self.split_audio(audio_path)
            if not chunk_paths:
                return {
                    'success': False,
                    'error': 'Failed to split audio into chunks'
                }

            try:
                # Process each chunk
                transcription_parts = []
                for chunk_path in chunk_paths:
                    chunk_text = self.transcribe_chunk(chunk_path)
                    if chunk_text:
                        transcription_parts.append(chunk_text)

                # Combine results
                if transcription_parts:
                    return {
                        'success': True,
                        'transcription': ' '.join(transcription_parts)
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No speech could be recognized in any chunk'
                    }

            finally:
                # Clean up chunk files
                for chunk_path in chunk_paths:
                    try:
                        if os.path.exists(chunk_path):
                            os.remove(chunk_path)
                    except Exception:
                        pass

        except Exception as e:
            return {
                'success': False,
                'error': f'Transcription error: {str(e)}'
            }