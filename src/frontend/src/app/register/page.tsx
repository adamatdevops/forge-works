'use client';

/**
 * Register Page
 * ForgeWorks Authentication
 */

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Hammer } from 'lucide-react';

import { RegisterForm } from '@/components/auth';
import { useAuth } from '@/lib/auth';
import { useEffect } from 'react';

export default function RegisterPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  const handleSuccess = () => {
    router.push('/');
  };

  const handleLoginClick = () => {
    router.push('/login');
  };

  // Show nothing while checking auth status
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  // Don't render form if already authenticated (redirect will happen)
  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
          <Hammer className="h-6 w-6 text-primary-foreground" />
        </div>
        <span className="text-2xl font-bold">ForgeWorks</span>
      </div>

      {/* Register Form */}
      <RegisterForm onSuccess={handleSuccess} onLoginClick={handleLoginClick} />

      {/* Footer */}
      <p className="mt-8 text-center text-xs text-muted-foreground">
        By creating an account, you agree to our{' '}
        <Link href="/terms" className="underline hover:text-primary">
          Terms of Service
        </Link>{' '}
        and{' '}
        <Link href="/privacy" className="underline hover:text-primary">
          Privacy Policy
        </Link>
      </p>
    </div>
  );
}
