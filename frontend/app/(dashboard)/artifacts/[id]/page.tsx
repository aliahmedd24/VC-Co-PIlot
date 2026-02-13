"use client";

import { useRouter, useParams } from "next/navigation";
import { ArtifactDetail } from "@/components/artifacts/ArtifactDetail";

export default function ArtifactDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <ArtifactDetail artifactId={id} onBack={() => router.push("/artifacts")} />
    </div>
  );
}
