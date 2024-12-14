import { NextRequest, NextResponse } from 'next/server';
import dbPromise from '../../../lib/db';

export async function POST(request: NextRequest) {
  const { id, status } = await request.json();

  if (!id || !status) {
    return NextResponse.json({ error: 'Missing transcription ID or status' }, { status: 400 });
  }

  if (!['unresolved', 'in_progress', 'resolved'].includes(status)) {
    return NextResponse.json({ error: 'Invalid status' }, { status: 400 });
  }

  try {
    const db = await dbPromise;
    await db.run('UPDATE transcriptions_cont SET status = ? WHERE id = ?', status, id);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error updating transcription status:', error);
    return NextResponse.json({ error: 'Failed to update transcription status' }, { status: 500 });
  }
}

