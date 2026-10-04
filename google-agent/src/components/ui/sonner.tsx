'use client'

import { Toaster as Sonner } from 'sonner'

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="system"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            'group toast group-[.toaster]:bg-popover group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:rounded-xl group-[.toaster]:shadow-[0_12px_32px_-8px_hsl(var(--foreground)/0.18)] group-[.toaster]:font-sans',
          description: 'group-[.toast]:text-muted-foreground',
          actionButton:
            'group-[.toast]:bg-foreground group-[.toast]:text-background',
          cancelButton:
            'group-[.toast]:bg-muted group-[.toast]:text-foreground',
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
