'use client';

/**
 * User Menu Component
 * Shows user info and logout option
 */

import { LogOut, User as UserIcon } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useAuth, useUser } from '@/lib/auth';

interface UserMenuProps {
  onLogout?: () => void;
}

export function UserMenu({ onLogout }: UserMenuProps) {
  const { logout } = useAuth();
  const user = useUser();

  if (!user) {
    return null;
  }

  const handleLogout = async () => {
    await logout();
    onLogout?.();
  };

  // Get initials from full name
  const initials = user.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="flex items-center gap-3">
      {/* Avatar */}
      <div className="bg-primary text-primary-foreground flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium">
        {initials}
      </div>

      {/* User Info */}
      <div className="hidden flex-col sm:flex">
        <span className="text-sm font-medium">{user.full_name}</span>
        <span className="text-muted-foreground text-xs">{user.email}</span>
      </div>

      {/* Logout Button */}
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={handleLogout}
        title="Sign out"
      >
        <LogOut className="h-4 w-4" />
      </Button>
    </div>
  );
}

/**
 * Auth Button Component
 * Shows login button when not authenticated, user menu when authenticated
 */
interface AuthButtonProps {
  onLoginClick?: () => void;
  onLogout?: () => void;
}

export function AuthButton({ onLoginClick, onLogout }: AuthButtonProps) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="bg-muted h-8 w-8 animate-pulse rounded-full" />
    );
  }

  if (isAuthenticated) {
    return <UserMenu onLogout={onLogout} />;
  }

  return (
    <Button variant="outline" size="sm" onClick={onLoginClick}>
      <UserIcon className="mr-2 h-4 w-4" />
      Sign in
    </Button>
  );
}

export default UserMenu;
