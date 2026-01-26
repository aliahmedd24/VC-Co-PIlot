"use client";

import { useEffect, useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, Upload, CheckCircle, Clock, AlertTriangle, File, X } from 'lucide-react';

interface Document {
    id: string;
    name: string;
    type: string;
    status: string;
    created_at: string;
    size: number;
}

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [uploading, setUploading] = useState(false);

    const fetchDocuments = async () => {
        try {
            const response = await api.get('/documents?workspace_id=default');
            // Backend returns { documents: [...], total: int }
            setDocuments(response.data.documents || []);
        } catch (error) {
            console.error('Failed to fetch documents', error);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        setUploading(true);
        try {
            for (const file of acceptedFiles) {
                const formData = new FormData();
                formData.append('file', file);

                await api.post('/documents/upload?workspace_id=default', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
            }
            await fetchDocuments();
        } catch (error) {
            console.error('Upload failed', error);
            // TODO: Add toast notification
        } finally {
            setUploading(false);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'indexed': return <CheckCircle className="h-4 w-4 text-green-500" />;
            case 'processing': return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
            case 'failed': return <AlertTriangle className="h-4 w-4 text-red-500" />;
            default: return <Clock className="h-4 w-4 text-slate-400" />;
        }
    };

    return (
        <div className="p-8 max-w-6xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Knowledge Base</h1>
                <p className="text-slate-500 mt-2">Upload pitch decks, financial models, and research to power the Brain.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Upload Area */}
                <Card className="lg:col-span-1">
                    <CardHeader>
                        <CardTitle>Upload Documents</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div
                            {...getRootProps()}
                            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'
                                }`}
                        >
                            <input {...getInputProps()} />
                            <div className="flex flex-col items-center gap-4">
                                <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center">
                                    <Upload className="h-6 w-6 text-slate-400" />
                                </div>
                                <div className="space-y-1">
                                    <p className="font-medium text-slate-900">Click to upload or drag and drop</p>
                                    <p className="text-sm text-slate-500">PDF, DOCX, PPTX (max 10MB)</p>
                                </div>
                                {uploading && <div className="text-sm text-blue-600 font-medium animate-pulse">Uploading...</div>}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Document List */}
                <Card className="lg:col-span-2 flex flex-col h-[600px]">
                    <CardHeader>
                        <CardTitle>Files</CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 overflow-hidden p-0">
                        <ScrollArea className="h-full">
                            <div className="p-6 space-y-4">
                                {documents.length === 0 ? (
                                    <div className="text-center text-slate-400 py-12">
                                        <File className="h-12 w-12 mx-auto mb-4 opacity-20" />
                                        <p>No documents uploaded yet</p>
                                    </div>
                                ) : (
                                    documents.map((doc) => (
                                        <div key={doc.id} className="flex items-center justify-between p-4 rounded-lg border bg-slate-50 hover:bg-slate-100 transition-colors">
                                            <div className="flex items-center gap-4">
                                                <div className="h-10 w-10 rounded bg-white border flex items-center justify-center">
                                                    <FileText className="h-5 w-5 text-blue-500" />
                                                </div>
                                                <div>
                                                    <div className="font-medium text-slate-900">{doc.name}</div>
                                                    <div className="text-xs text-slate-500 flex items-center gap-2">
                                                        <span>{(doc.size / 1024).toFixed(0)} KB</span>
                                                        <span>•</span>
                                                        <span className="capitalize">{doc.type.replace('_', ' ')}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <Badge variant="outline" className="gap-1 bg-white">
                                                    {getStatusIcon(doc.status)}
                                                    <span className="capitalize">{doc.status}</span>
                                                </Badge>
                                                <Button variant="ghost" size="icon" className="text-slate-400 hover:text-red-500">
                                                    <X className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
