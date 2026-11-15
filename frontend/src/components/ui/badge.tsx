import * as React from 'react'
import { cn } from '@/lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'info' | 'warning' | 'exception' | 'success' | 'request' | 'outline'
}

export function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  const baseStyles =
    'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors'

  const variants = {
    default: 'bg-slate-100 text-slate-800 border border-slate-200',
    info: 'bg-blue-50 text-blue-700 border border-blue-200',
    warning: 'bg-amber-50 text-amber-800 border border-amber-200',
    exception: 'bg-red-50 text-red-700 border border-red-200',
    success: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    request: 'bg-purple-50 text-purple-700 border border-purple-200',
    outline: 'border border-border text-foreground',
  }

  return <div className={cn(baseStyles, variants[variant], className)} {...props} />
}
