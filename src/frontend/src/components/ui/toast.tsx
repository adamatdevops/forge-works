'use client';

/**
 * Toast Notification System
 * Lightweight toast notifications for real-time WebSocket events
 */

import { memo, useCallback, useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, Info, X, XCircle, Bell } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  sound?: boolean;
}

interface ToastItemProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

const ToastIcon = memo(function ToastIcon({ type }: { type: ToastType }) {
  const iconClass = 'h-5 w-5';

  switch (type) {
    case 'success':
      return <CheckCircle className={cn(iconClass, 'text-green-500')} />;
    case 'warning':
      return <AlertTriangle className={cn(iconClass, 'text-yellow-500')} />;
    case 'error':
      return <XCircle className={cn(iconClass, 'text-red-500')} />;
    case 'info':
    default:
      return <Info className={cn(iconClass, 'text-blue-500')} />;
  }
});

const ToastItem = memo(function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const [isExiting, setIsExiting] = useState(false);

  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => onDismiss(toast.id), 200);
  }, [toast.id, onDismiss]);

  useEffect(() => {
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      const timer = setTimeout(handleDismiss, duration);
      return () => clearTimeout(timer);
    }
  }, [toast.duration, handleDismiss]);

  const bgColors: Record<ToastType, string> = {
    info: 'bg-blue-500/10 border-blue-500/20',
    success: 'bg-green-500/10 border-green-500/20',
    warning: 'bg-yellow-500/10 border-yellow-500/20',
    error: 'bg-red-500/10 border-red-500/20',
  };

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border shadow-lg backdrop-blur-sm',
        'transition-all duration-200 ease-in-out',
        isExiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0',
        bgColors[toast.type]
      )}
      role="alert"
      aria-live="polite"
    >
      <ToastIcon type={toast.type} />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{toast.title}</p>
        {toast.message && (
          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
            {toast.message}
          </p>
        )}
        {toast.action && (
          <button
            onClick={toast.action.onClick}
            className="text-xs font-medium text-primary hover:underline mt-2"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        onClick={handleDismiss}
        className="p-1 hover:bg-muted/50 rounded transition-colors"
        aria-label="Dismiss notification"
      >
        <X className="h-4 w-4 text-muted-foreground" />
      </button>
    </div>
  );
});

interface ToastContainerProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  maxVisible?: number;
}

export function ToastContainer({
  toasts,
  onDismiss,
  position = 'top-right',
  maxVisible = 5,
}: ToastContainerProps) {
  const positionClasses: Record<string, string> = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
  };

  const visibleToasts = toasts.slice(-maxVisible);

  if (visibleToasts.length === 0) return null;

  return (
    <div
      className={cn(
        'fixed z-50 flex flex-col gap-2 w-80',
        positionClasses[position]
      )}
      aria-label="Notifications"
    >
      {visibleToasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

// Toast store/context for global toast management
type ToastListener = (toasts: Toast[]) => void;

class ToastStore {
  private toasts: Toast[] = [];
  private listeners: Set<ToastListener> = new Set();
  private idCounter = 0;

  subscribe(listener: ToastListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify() {
    this.listeners.forEach((listener) => listener([...this.toasts]));
  }

  add(toast: Omit<Toast, 'id'>) {
    const id = `toast-${++this.idCounter}-${Date.now()}`;
    const newToast: Toast = { ...toast, id };

    // Play sound for critical events
    if (toast.sound && typeof window !== 'undefined') {
      this.playNotificationSound(toast.type);
    }

    this.toasts.push(newToast);
    this.notify();
    return id;
  }

  remove(id: string) {
    this.toasts = this.toasts.filter((t) => t.id !== id);
    this.notify();
  }

  clear() {
    this.toasts = [];
    this.notify();
  }

  private playNotificationSound(type: ToastType) {
    try {
      const AudioContext = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof window.AudioContext }).webkitAudioContext;
      if (!AudioContext) return;

      const audioContext = new AudioContext();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      // Different tones for different types
      const frequencies: Record<ToastType, number> = {
        info: 440,
        success: 523,
        warning: 392,
        error: 330,
      };

      oscillator.frequency.value = frequencies[type];
      oscillator.type = type === 'error' ? 'square' : 'sine';
      gainNode.gain.value = 0.1;

      oscillator.start();
      oscillator.stop(audioContext.currentTime + 0.15);
    } catch {
      // Audio not supported or blocked
    }
  }
}

export const toastStore = new ToastStore();

// Convenience functions
export const toast = {
  info: (title: string, message?: string, options?: Partial<Toast>) =>
    toastStore.add({ type: 'info', title, message, ...options }),
  success: (title: string, message?: string, options?: Partial<Toast>) =>
    toastStore.add({ type: 'success', title, message, ...options }),
  warning: (title: string, message?: string, options?: Partial<Toast>) =>
    toastStore.add({ type: 'warning', title, message, sound: true, ...options }),
  error: (title: string, message?: string, options?: Partial<Toast>) =>
    toastStore.add({ type: 'error', title, message, sound: true, ...options }),
  dismiss: (id: string) => toastStore.remove(id),
  clear: () => toastStore.clear(),
};

// Hook for using toasts
export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    return toastStore.subscribe(setToasts);
  }, []);

  return {
    toasts,
    add: toastStore.add.bind(toastStore),
    remove: toastStore.remove.bind(toastStore),
    clear: toastStore.clear.bind(toastStore),
  };
}

// Provider component to render toasts globally
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const { toasts, remove } = useToasts();

  return (
    <>
      {children}
      <ToastContainer toasts={toasts} onDismiss={remove} />
    </>
  );
}

export default ToastContainer;
