import aiosqlite
import os
import whisper
import ollama
from typing import Dict, Any
import uuid
from datetime import datetime
import json
import logging
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import aiosqlite

class AudioProcessor:
    def __init__(self, 
                 whisper_model: str = 'small', 
                 database_path: str = 'transcriptions.db',
                 ollama_model: str = 'llama3'):
        # Previous initialization code
        self.database_path = database_path

        self.conn = None  # Explicitly initialize conn attribute


    async def _ensure_connection(self):
        """Ensure a single database connection is maintained"""
        if self.conn is None:
            self.conn = await aiosqlite.connect(self.database_path)
            await self._create_table(self.conn)
        return self.conn

    async def _create_table(self, conn):
        """Create SQLite table for storing transcriptions"""
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions (
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
        await conn.commit()

    async def store_transcription(self, 
                             original_filename: str, 
                             transcription: Dict[str, Any], 
                             nlp_result: Dict[str, Any]) -> str:
        """Store transcription in SQLite database"""
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            transcription_id = str(uuid.uuid4())
            entities = str(nlp_result.get('entities', [])).replace("'", '"')
            
            await cursor.execute('''
                INSERT INTO transcriptions 
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
            
            await conn.commit()
            return transcription_id

    async def close_connection(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            self.conn = None


# class AudioProcessor:
    def __init__(self, 
                 whisper_model: str = 'small', 
                 database_path: str = 'transcriptions.db',
                 ollama_model: str = 'llama3'):
        """
        Initialize AudioProcessor with Whisper model, database, and Ollama model
        """
        # Load Whisper model
        print(f"Loading Whisper model: {whisper_model}")
        self.whisper_model = whisper.load_model(whisper_model)
        
        # Ollama model for NLP
        self.ollama_model = ollama_model
        
        # Database path
        self.database_path = database_path

    async def _get_db_connection(self):
        """Get an async database connection"""
        return await aiosqlite.connect(self.database_path)

    async def _create_table(self, conn):
        """Create SQLite table for storing transcriptions"""
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions (
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
        await conn.commit()

    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper
        
        :param audio_path: Path to audio file
        :return: Dictionary with transcription details
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print(f"Transcribing audio: {audio_path}")
        result = self.whisper_model.transcribe(audio_path)
        
        return {
            'text': result['text'],
            'language': result.get('language', 'Unknown')
        }

    def extract_intent_and_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract intent and entities from transcribed text using Ollama
        
        :param text: Transcribed text
        :return: Dictionary with intent and entities
        """
        # Simplified prompt to reduce complexity
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
            logger.debug(f"Sending prompt to Ollama model: {self.ollama_model}")
            logger.debug(f"Prompt text length: {len(text)}")
            
            # Retry mechanism with different approaches
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    response = ollama.chat(
                        model=self.ollama_model,
                        messages=[
                            {
                                'role': 'user',
                                'content': prompt
                            }
                        ]
                    )
                    
                    # Log the raw response
                    raw_content = response['message']['content']
                    logger.debug(f"Raw Ollama response: {raw_content}")
                    
                    # Try parsing the response
                    try:
                        result = json.loads(raw_content)
                        return result
                    except json.JSONDecodeError as json_err:
                        logger.warning(f"JSON Parsing attempt {attempt + 1} failed: {json_err}")
                        
                        # Define the regular expression pattern to match the JSON part
                        pattern = r'\{.*\}'

                        # Search for the pattern in the text
                        match = re.search(pattern, raw_content, re.DOTALL)

                        if match:
                            # Extract the matched JSON string
                            raw_content = match.group(0)

                        try:
                            result = json.loads(raw_content)
                            return result
                        except Exception as e:
                            logger.error(f"Failed to parse JSON after cleaning: {e}")
                
                except Exception as attempt_err:
                    logger.error(f"Ollama request attempt {attempt + 1} failed: {attempt_err}")
            
            # If all attempts fail, return default
            return {
                'intent': 'UNKNOWN',
                'entities': []
            }
        
        except Exception as e:
            logger.error(f"Comprehensive error in intent extraction: {e}")
            return {
                'intent': 'UNKNOWN',
                'entities': []
            }
    
    # Modify other methods to be async and use aiosqlite
    # For example, store_transcription would look like:
    async def store_transcription(self, 
                             original_filename: str, 
                             transcription: Dict[str, Any], 
                             nlp_result: Dict[str, Any]) -> str:
        """
        Store transcription in SQLite database
        """
        async with await self._get_db_connection() as conn:
            await self._create_table(conn)
            async with conn.cursor() as cursor:
                transcription_id = str(uuid.uuid4())
                entities = str(nlp_result.get('entities', [])).replace("'", '"')
                
                await cursor.execute('''
                    INSERT INTO transcriptions 
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
                
                await conn.commit()
                return transcription_id

    async def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Complete audio processing workflow
        """
        # Transcribe audio
        transcription = self.transcribe_audio(audio_path)
        
        # Extract intent and entities
        nlp_result = self.extract_intent_and_entities(transcription['text'])
        
        # Store in database
        transcription_id = await self.store_transcription(
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
    def process_dummy(self, file_path):
        return {"status": "processed", "file": file_path, "result": "result from intent"}


    # Other methods remain mostly the same, just modify to be async where database interactions occur