import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Transcription Dashboard',
  description: 'View and manage transcriptions',
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      {children}
    </div>
  );
}

