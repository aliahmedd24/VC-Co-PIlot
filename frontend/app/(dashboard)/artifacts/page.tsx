"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, Plus, ExternalLink, Calendar } from 'lucide-react';

interface Artifact {
    id: string;
    title: string;
    type: string;
    status: string;
    created_at: string;
    updated_at: string;
}

export default function ArtifactsPage() {
    const [artifacts, setArtifacts] = useState<Artifact[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchArtifacts();
    }, []);

    const fetchArtifacts = async () => {
        try {
            // TODO: Get real workspace ID
            const response = await api.get('/artifacts?workspace_id=default');
            setArtifacts(response.data.items);
        } catch (error) {
            console.error('Failed to fetch artifacts', error);
            // Mock data for dev if API fails
            setArtifacts([
                {
                    id: '1',
                    title: 'Seed Pitch Deck',
                    type: 'deck',
                    status: 'draft',
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Artifacts</h1>
                    <p className="text-slate-500 mt-2">Manage your venture documents and deliverables</p>
                </div>
                <Button className="gap-2">
                    <Plus className="h-4 w-4" />
                    New Artifact
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {artifacts.map((artifact) => (
                    <Card key={artifact.id} className="hover:shadow-lg transition-shadow">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-500 uppercase tracking-wider">
                                {artifact.type}
                            </CardTitle>
                            <Badge variant={artifact.status === 'draft' ? 'secondary' : 'default'}>
                                {artifact.status}
                            </Badge>
                        </CardHeader>
                        <CardContent>
                            <div className="text-xl font-bold mb-4">{artifact.title}</div>
                            <div className="flex items-center text-sm text-slate-500 gap-4">
                                <div className="flex items-center gap-1">
                                    <Calendar className="h-3 w-3" />
                                    {new Date(artifact.updated_at).toLocaleDateString()}
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter>
                            <Link href={`/artifacts/${artifact.id}`} className="w-full">
                                <Button variant="outline" className="w-full gap-2 group">
                                    View Details
                                    <ExternalLink className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                                </Button>
                            </Link>
                        </CardFooter>
                    </Card>
                ))}
            </div>
        </div>
    );
}
