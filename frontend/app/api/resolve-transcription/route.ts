import { NextRequest, NextResponse } from 'next/server';
import dbPromise from '../../../lib/db';

export async function POST(request: NextRequest) {
  const { id } = await request.json();

  if (!id) {
    return NextResponse.json({ error: 'Missing transcription ID' }, { status: 400 });
  }

  try {
    const db = await dbPromise;
    await db.run('UPDATE transcriptions SET is_resolved = 1 WHERE id = ?', id);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error resolving transcription:', error);
    return NextResponse.json({ error: 'Failed to resolve transcription' }, { status: 500 });
  }
}
