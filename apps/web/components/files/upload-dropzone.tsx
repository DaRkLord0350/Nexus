'use client';

import { UploadCloud } from 'lucide-react';
import { useRef, useState } from 'react';

interface UploadDropzoneProps {
  onFiles: (files: FileList) => void;
  uploading: boolean;
}

export function UploadDropzone({ onFiles, uploading }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  return (
    <div
      onDragOver={(e) => {
        if (e.dataTransfer.types.includes('Files')) {
          e.preventDefault();
          setIsDragOver(true);
        }
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragOver(false);
        if (e.dataTransfer.files.length > 0) {
          onFiles(e.dataTransfer.files);
        }
      }}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed p-8 text-center transition ${
        isDragOver
          ? 'border-cyan-500 bg-cyan-500/10'
          : 'border-slate-300 bg-slate-50/50 hover:border-slate-400 dark:border-slate-700 dark:bg-slate-900/40 dark:hover:border-slate-600'
      }`}
    >
      <UploadCloud size={24} className="text-slate-400 dark:text-slate-500" />
      <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
        {uploading ? 'Uploading…' : 'Drag & drop files here, or click to browse'}
      </p>
      <input
        ref={inputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            onFiles(e.target.files);
            e.target.value = '';
          }
        }}
      />
    </div>
  );
}
