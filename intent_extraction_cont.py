import os
import time
import whisper
import sqlite3
import ollama
from typing import Dict, Any
import uuid
from datetime import datetime
import json
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, 
                 audio_folder: str = 'data/unprocessed',
                 processed_folder: str = 'data/processed', 
                 whisper_model: str = 'small', 
                 database_path: str = 'transcriptions_cont.db',
                 ollama_model: str = 'llama3',
                 poll_interval: int = 10):
        """
        Initialize AudioProcessor with folder monitoring capabilities
        
        :param audio_folder: Folder to monitor for new audio files
        :param processed_folder: Folder to move processed files
        :param whisper_model: Size of Whisper model to use
        :param database_path: Path to SQLite database
        :param ollama_model: Ollama model for intent and entity extraction
        :param poll_interval: Time between folder checks in seconds
        """
        # Create folders if they don't exist
        os.makedirs(audio_folder, exist_ok=True)
        os.makedirs(processed_folder, exist_ok=True)
        
        # Configuration
        self.audio_folder = audio_folder
        self.processed_folder = processed_folder
        self.poll_interval = poll_interval
        
        # Load Whisper model
        print(f"Loading Whisper model: {whisper_model}")
        self.whisper_model = whisper.load_model(whisper_model)
        
        # Ollama model for NLP
        self.ollama_model = ollama_model
        
        # Setup database connection
        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()
        
        # Create transcriptions table if not exists
        self._create_table()
    
    def _create_table(self):
        """Create SQLite table for storing transcriptions"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions_cont (
                id TEXT PRIMARY KEY,
                original_filename TEXT,
                transcribed_text TEXT,
                intent TEXT,
                entities TEXT,
                timestamp DATETIME,
                status TEXT CHECK(status IN ('unresolved', 'in_progress', 'resolved')),
                resolution_notes TEXT
            )
        ''')
        self.conn.commit()
    
    def _is_file_processed(self, filename: str) -> bool:
        """
        Check if file has already been processed in database
        
        :param filename: Name of the audio file
        :return: Boolean indicating if file is processed
        """
        self.cursor.execute('SELECT COUNT(*) FROM transcriptions_cont WHERE original_filename = ?', (filename,))
        return self.cursor.fetchone()[0] > 0
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        # Same implementation as before
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print(f"Transcribing audio: {audio_path}")
        result = self.whisper_model.transcribe(audio_path)
        
        return {
            'text': result['text'],
            'language': result.get('language', 'Unknown')
        }
    
    def extract_intent_and_entities(self, text: str) -> Dict[str, Any]:
        # Same implementation as before (intent extraction method)
        prompt = f"""Given the text: "{text}"
                    Perform these tasks:
                    1. Identify the primary intent of the text. Choose from these categories:
                    - SCHEDULE_MAINTAINCE
                    - REQUEST_SUPPORT
                    - GENERAL_INQUIRY
                    - OTHER

                    2. List important named entities with their types.

                    Respond EXACTLY in this JSON format:
                    {{
                        "intent": "INTENT_CATEGORY",
                        "entities": [
                            {{
                                "text": "Entity Name",
                                "label": "Entity Type"
                            }}
                        ]
                    }}

                    If unsure, use "OTHER" for intent and leave entities as an empty list."""
                            
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            raw_content = response['message']['content']
            
            # Try parsing the response
            try:
                result = json.loads(raw_content)
                return result
            except json.JSONDecodeError:
                # Try extracting JSON from text
                pattern = r'\{.*\}'
                match = re.search(pattern, raw_content, re.DOTALL)
                
                if match:
                    raw_content = match.group(0)
                    result = json.loads(raw_content)
                    return result
                
                return {'intent': 'UNKNOWN', 'entities': []}
        
        except Exception as e:
            logger.error(f"Error in intent extraction: {e}")
            return {'intent': 'UNKNOWN', 'entities': []}
    
    def store_transcription(self, 
                             original_filename: str, 
                             transcription: Dict[str, Any], 
                             nlp_result: Dict[str, Any]) -> str:
        # Same implementation as before
        transcription_id = str(uuid.uuid4())
        entities = str(nlp_result.get('entities', [])).replace("'", '"')
        
        self.cursor.execute('''
            INSERT INTO transcriptions_cont 
            (id, original_filename, transcribed_text, intent, entities, timestamp, status, resolution_notes) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', 
            (
                transcription_id,
                original_filename,
                transcription['text'],
                nlp_result.get('intent', 'UNKNOWN'),
                entities,
                datetime.now(),
                'unresolved',
                ''
            )
        )
        
        self.conn.commit()
        return transcription_id
    
    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        # Transcribe audio
        transcription = self.transcribe_audio(audio_path)
        
        # Extract intent and entities
        nlp_result = self.extract_intent_and_entities(transcription['text'])
        
        # Store in database
        transcription_id = self.store_transcription(
            os.path.basename(audio_path), 
            transcription, 
            nlp_result
        )
        
        return {
            'transcription_id': transcription_id,
            'text': transcription['text'],
            'intent': nlp_result.get('intent', 'UNKNOWN'),
            'entities': nlp_result.get('entities', [])
        }
    
    def monitor_folder(self):
        """
        Continuously monitor folder for new audio files
        """
        logger.info(f"Monitoring folder: {self.audio_folder}")
        
        while True:
            for filename in os.listdir(self.audio_folder):
                # Check file extensions (add more if needed)
                if filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac')):
                    filepath = os.path.join(self.audio_folder, filename)
                    
                    # Check if file is already processed
                    if not self._is_file_processed(filename):
                        try:
                            logger.info(f"Processing new file: {filename}")
                            result = self.process_audio(filepath)
                            
                            # Move processed file
                            processed_path = os.path.join(self.processed_folder, filename)
                            os.rename(filepath, processed_path)
                            
                            logger.info(f"Successfully processed: {filename}")
                            logger.info(f"Intent: {result['intent']}")
                        except Exception as e:
                            logger.error(f"Error processing {filename}: {e}")
            
            # Wait before next check
            time.sleep(self.poll_interval)
    
    def close_connection(self):
        """Close database connection"""
        self.conn.close()

def main():
    processor = AudioProcessor(
        audio_folder='data2/unprocessed',
        processed_folder='data2/processed',
        whisper_model='small',  
        ollama_model='mistral:v0.3'
    )
    
    try:
        processor.monitor_folder()
    except KeyboardInterrupt:
        logger.info("Stopping folder monitoring...")
    finally:
        processor.close_connection()

if __name__ == "__main__":
    main()