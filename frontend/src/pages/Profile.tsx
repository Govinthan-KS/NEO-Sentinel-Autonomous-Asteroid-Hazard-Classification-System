import React from 'react';
import { useAuth } from '@/context/AuthContext';
import { GlassCard } from '@/components/ui/GlassCard';
import { LogOut, Copy, User as UserIcon } from 'lucide-react';
import { showInfoToast } from '@/utils/toast';
import { AnimatedBackground } from '@/components/layout/AnimatedBackground';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';

export const Profile: React.FC = () => {
  const { user, signOut } = useAuth();

  const handleCopyId = () => {
    if (user?.id) {
      navigator.clipboard.writeText(user.id);
      showInfoToast('Copied', 'User ID copied to clipboard!');
    }
  };

  const getInitials = (name: string | undefined) => {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
  };

  const fullName = user?.user_metadata?.full_name;
  const avatarUrl = user?.user_metadata?.avatar_url;
  const email = user?.email;
  
  const joinDate = user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown';
  const lastSession = user?.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleString() : 'Unknown';

  return (
    <div className="relative min-h-screen flex flex-col">
      <AnimatedBackground />
      <Navbar />

      <main className="flex-grow relative z-10 max-w-4xl mx-auto w-full px-6 md:px-10 py-11 pb-[100px]">
        <h1 className="text-3xl font-bold text-slate-100 mb-8">User Profile</h1>

      <GlassCard className="p-6 md:p-8 overflow-hidden">
        <div className="flex flex-col md:flex-row items-center gap-6 md:gap-8 w-full min-w-0">
          
          {/* Avatar Section */}
          <div className="relative">
            {avatarUrl ? (
              <img 
                src={avatarUrl} 
                alt="Profile Avatar" 
                className="w-32 h-32 rounded-full object-cover border-4 border-slate-800 shadow-xl"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                  e.currentTarget.parentElement?.querySelector('.fallback-avatar')?.classList.remove('hidden');
                }}
              />
            ) : null}
            
            <div className={`fallback-avatar ${avatarUrl ? 'hidden' : ''} w-32 h-32 rounded-full bg-slate-800 flex items-center justify-center text-4xl font-bold text-slate-300 border-4 border-slate-700 shadow-xl`}>
              {fullName ? getInitials(fullName) : <UserIcon className="w-12 h-12 text-slate-400" />}
            </div>
          </div>

          {/* User Details */}
          <div className="flex-1 text-center md:text-left min-w-0">
            <h2 className="text-2xl font-bold text-slate-100 mb-1 truncate">{fullName || 'Unknown User'}</h2>
            <p className="text-slate-400 mb-4 truncate">{email}</p>

            <div className="flex flex-col md:flex-row items-center justify-center md:justify-start gap-2 md:gap-4 mb-6 text-sm text-slate-400 w-full min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-slate-500">Joined:</span> <span className="truncate">{joinDate}</span>
              </div>
              <div className="w-1 h-1 rounded-full bg-slate-700 hidden md:block"></div>
              <div className="flex items-center gap-1.5 min-w-0 max-w-full">
                <span className="font-semibold text-slate-500 shrink-0">Last Session:</span> 
                <span className="truncate">{lastSession}</span>
              </div>
            </div>

            <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-800/50 flex items-center gap-3 w-full mt-2 mx-auto md:mx-0 min-w-0">
              <div className="flex-1 min-w-0 overflow-hidden">
                <code className="block text-sm text-cyan-400 font-mono bg-black/40 px-3 py-1.5 rounded truncate text-left w-full">
                  {user?.id}
                </code>
              </div>
              <button
                onClick={handleCopyId}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-md transition-colors shrink-0"
                title="Copy User ID"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-800/50 flex justify-center md:justify-end">
          <button
            onClick={signOut}
            className="w-full md:w-auto flex items-center justify-center gap-2 px-6 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 rounded-lg font-medium transition-colors border border-red-500/20"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </GlassCard>
      </main>
      <Footer />
    </div>
  );
};
