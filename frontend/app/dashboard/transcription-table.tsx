'use client'

import { useState } from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type Transcription = {
  id: string;
  original_filename: string;
  transcribed_text: string;
  intent: string;
  entities: string;
  timestamp: string;
  status: 'unresolved' | 'in_progress' | 'resolved';
  resolution_notes: string;
};

export function TranscriptionTable({ transcriptions: initialTranscriptions }: { transcriptions: Transcription[] }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [transcriptions, setTranscriptions] = useState(initialTranscriptions);

  const filteredTranscriptions = transcriptions.filter(
    (t) =>
      t.transcribed_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.intent.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.original_filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleStatusChange = async (id: string, newStatus: string) => {
    try {
      const response = await fetch('/api/update-transcription-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id, status: newStatus }),
      });

      if (!response.ok) {
        throw new Error('Failed to update transcription status');
      }

      setTranscriptions(transcriptions.map(t => 
        t.id === id ? { ...t, status: newStatus as Transcription['status'] } : t
      ));
    } catch (error) {
      console.error('Error updating transcription status:', error);
      alert('Failed to update transcription status. Please try again.');
    }
  };

  const getStatusBadge = (status: Transcription['status']) => {
    switch (status) {
      case 'resolved':
        return <Badge variant="success">Resolved</Badge>;
      case 'in_progress':
        return <Badge variant="warning">In Progress</Badge>;
      case 'unresolved':
        return <Badge variant="destructive">Unresolved</Badge>;
      default:
        return null;
    }
  };

  return (
    <div>
      <Input
        type="search"
        placeholder="Search transcriptions..."
        className="max-w-sm mb-4"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>File Name</TableHead>
              <TableHead>Transcribed Text</TableHead>
              <TableHead>Intent</TableHead>
              <TableHead>Entities</TableHead>
              <TableHead>Timestamp</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTranscriptions.map((t) => (
              <TableRow key={t.id}>
                <TableCell>{t.original_filename}</TableCell>
                <TableCell className="max-w-md truncate">{t.transcribed_text}</TableCell>
                <TableCell>{t.intent}</TableCell>
                <TableCell>
                  {JSON.parse(t.entities).map((entity: { text: string; label: string }, index: number) => (
                    <Badge key={index} variant="secondary" className="mr-1 mb-1">
                      {entity.text}: {entity.label}
                    </Badge>
                  ))}
                </TableCell>
                <TableCell>{new Date(t.timestamp).toLocaleString()}</TableCell>
                <TableCell>{getStatusBadge(t.status)}</TableCell>
                <TableCell>
                  <Select
                    value={t.status}
                    onValueChange={(value) => handleStatusChange(t.id, value)}
                  >
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Update status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unresolved">Unresolved</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="resolved">Resolved</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

