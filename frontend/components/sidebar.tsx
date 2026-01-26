"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import {
    MessageSquare,
    FileText,
    Settings,
    LogOut,
    Briefcase
} from 'lucide-react';
import { useRouter } from 'next/navigation';

export function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();

    const handleLogout = () => {
        localStorage.removeItem('token');
        router.push('/login');
    };

    const navItems = [
        { href: '/chat', label: 'Chat', icon: MessageSquare },
        { href: '/artifacts', label: 'Artifacts', icon: FileText },
        { href: '/documents', label: 'Brain', icon: FileText },
        { href: '/settings', label: 'Settings', icon: Settings },
    ];

    return (
        <div className="flex h-screen w-64 flex-col border-r bg-slate-900 text-slate-50">
            <div className="flex items-center gap-2 p-6">
                <Briefcase className="h-6 w-6 text-blue-400" />
                <span className="text-xl font-bold">VC Co-Pilot</span>
            </div>

            <div className="flex-1 px-4 py-4 space-y-2">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname.startsWith(item.href);

                    return (
                        <Link key={item.href} href={item.href}>
                            <Button
                                variant="ghost"
                                className={`w-full justify-start gap-3 ${isActive ? 'bg-slate-800 text-blue-400' : 'text-slate-400 hover:text-slate-100'
                                    }`}
                            >
                                <Icon className="h-5 w-5" />
                                {item.label}
                            </Button>
                        </Link>
                    );
                })}
            </div>

            <div className="p-4 border-t border-slate-800">
                <Button
                    variant="ghost"
                    className="w-full justify-start gap-3 text-slate-400 hover:text-red-400 hover:bg-slate-800"
                    onClick={handleLogout}
                >
                    <LogOut className="h-5 w-5" />
                    Logout
                </Button>
            </div>
        </div>
    );
}
