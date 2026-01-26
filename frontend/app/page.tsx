"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.push('/chat');
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <p className="text-lg text-slate-500 animate-pulse">Redirecting to VC Co-Pilot...</p>
    </div>
  );
}
