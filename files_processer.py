import os
import asyncio
import aiosqlite
import time
from typing import Dict, Any
import uuid
from datetime import datetime


from intent_extraction import AudioProcessor
from concurrent.futures import ThreadPoolExecutor

# Database setup
db_path = 'transcriptions_async.db'


async def process_file(file_path, cursor, processor, loop, _executor):
    # result = await loop.run_in_executor(_executor, processor.process_audio, file_path)
    result = await processor.process_audio(file_path)
    print(f"Processing result: {result}")

    # transcription_id = str(uuid.uuid4())
    # entities = str(result.get('entities', [])).replace("'", '"')
    # await cursor.execute('''
    #         INSERT INTO transcriptions 
    #         (id, original_filename, transcribed_text, intent, entities, timestamp, status, resolution_notes) 
    #         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    #         ''', 
    #         (
    #             transcription_id,
    #             file_path,
    #             result['text'],
    #             result['intent'],
    #             entities,
    #             datetime.now(),
    #             'unresolved',
    #             ''
    #         )
    #     )
        
    # await cursor.connection.commit()


async def filename_exists_in_db(cursor, filename):
    await cursor.execute('SELECT 1 FROM transcriptions WHERE original_filename = ?', (filename,))
    return await cursor.fetchone() is not None

async def insert_filename_into_db(cursor,
                             original_filename: str, 
                             result: Dict[str, Any]) -> str:
    """
    Store transcription in SQLite database
    
    :param original_filename: Original audio filename
    :param transcription: Transcription details
    :return: Unique ID of the stored transcription
    """
    print(result)
    transcription_id = str(uuid.uuid4())
    entities = str(result.get('entities', [])).replace("'", '"')
    await cursor.execute('''
            INSERT INTO transcriptions 
            (id, original_filename, transcribed_text, intent, entities, timestamp, status, resolution_notes) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', 
            (
                transcription_id,
                file_path,
                result['text'],
                result['intent'],
                entities,
                datetime.now(),
                'unresolved',
                ''
            )
        )
        
    await cursor.connection.commit()

        

async def main(folder_path):
    async with aiosqlite.connect(db_path) as db:
        async with db.cursor() as cursor:
           
            await cursor.execute('''
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
            await db.commit()
            loop = asyncio.get_event_loop()

            _executor = ThreadPoolExecutor(1)
            processor = AudioProcessor(
                    whisper_model='small',  # You can change model size
                    ollama_model='mistral:v0.3'  # Choose your Ollama model
            )


            while True:
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        if not await filename_exists_in_db(cursor, filename):
                            result = await process_file(file_path, cursor, processor, loop, _executor)
                            # await insert_filename_into_db(cursor, filename, result)
                        else:
                            print(f"File {filename} already processed.")
                await asyncio.sleep(10)  # Wait for 10 seconds before checking the folder again

if __name__ == '__main__':
    folder_path = 'data'  # Replace with your folder path
    asyncio.run(main(folder_path))
    # loop.run_until_complete(main(folder_path))
    # loop.close()