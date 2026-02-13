"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Upload } from "lucide-react";

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  "text/plain",
];

interface StepDocumentProps {
  onUpload: (file: File) => void;
  onSkip: () => void;
  isPending: boolean;
  uploadProgress: number;
}

export function StepDocument({
  onUpload,
  onSkip,
  isPending,
  uploadProgress,
}: StepDocumentProps) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const validateFile = useCallback((file: File): boolean => {
    if (file.size > MAX_FILE_SIZE) {
      setError("File is too large. Maximum size is 50MB.");
      return false;
    }
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError("Unsupported file type. Please upload PDF, DOCX, PPTX, or TXT.");
      return false;
    }
    setError(null);
    return true;
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file && validateFile(file)) {
        setSelectedFile(file);
      }
    },
    [validateFile]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file && validateFile(file)) {
        setSelectedFile(file);
      }
    },
    [validateFile]
  );

  return (
    <div className="space-y-4">
      <div
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
          dragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
      >
        <Upload className="mb-4 h-8 w-8 text-muted-foreground" />
        <p className="mb-2 text-sm font-medium">
          Drag & drop a document, or click to browse
        </p>
        <p className="text-xs text-muted-foreground">
          PDF, DOCX, PPTX, or TXT (max 50MB)
        </p>
        <input
          type="file"
          accept=".pdf,.docx,.pptx,.txt"
          className="absolute inset-0 cursor-pointer opacity-0"
          onChange={handleFileSelect}
          style={{ position: "relative", marginTop: "1rem" }}
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {selectedFile && (
        <div className="rounded-lg border p-3">
          <p className="text-sm font-medium">{selectedFile.name}</p>
          <p className="text-xs text-muted-foreground">
            {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
          </p>
          {isPending && (
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          )}
        </div>
      )}

      <div className="flex gap-3">
        <Button
          className="flex-1"
          disabled={!selectedFile || isPending}
          onClick={() => selectedFile && onUpload(selectedFile)}
        >
          {isPending ? `Uploading... ${uploadProgress}%` : "Upload & Continue"}
        </Button>
        <Button variant="outline" onClick={onSkip} disabled={isPending}>
          Skip
        </Button>
      </div>
    </div>
  );
}
