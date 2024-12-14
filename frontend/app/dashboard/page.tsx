import dbPromise from '../../lib/db';
import { TranscriptionTable } from './transcription-table';
// import sqlite3 from 'sqlite3'
// import { open } from 'sqlite'

async function getTranscriptions() {
  try {

    const db = await dbPromise;
  
    // const transcriptions = await db.all('SELECT * FROM transcriptions ORDER BY timestamp DESC');
    const transcriptions = await db.all('SELECT * FROM transcriptions_cont ORDER BY timestamp DESC');
    return transcriptions;
  } catch (error) {
    console.error('Database query error:', error);
    throw new Error('Failed to fetch transcriptions');
  }
}

export default async function DashboardPage() {
  try {
    const transcriptions = await getTranscriptions();

    return (
      <div className="container mx-auto py-10">
        <h1 className="text-4xl font-bold mb-8">Transcription Dashboard</h1>
        <TranscriptionTable transcriptions={transcriptions} />
      </div>
    );
  } catch (error) {
    return (
      <div className="container mx-auto py-10">
        <h1 className="text-4xl font-bold mb-8">Error</h1>
        <p className="text-red-500">Failed to load transcriptions. Please check your database connection.</p>
      </div>
    );
  }
}

