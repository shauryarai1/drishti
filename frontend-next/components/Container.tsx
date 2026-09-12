import React from 'react';

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  id?: string;
}

export function Container({
  children,
  className = '',
  size = 'lg',
  id,
}: ContainerProps) {
  const sizeClasses = {
    sm: 'max-w-3xl',
    md: 'max-w-5xl',
    lg: 'max-w-7xl',
    xl: 'max-w-[1536px]',
    full: 'max-w-full',
  }[size];

  return (
    <div
      id={id}
      className={`w-full mx-auto px-5 sm:px-8 md:px-12 lg:px-16 ${sizeClasses} ${className}`}
    >
      {children}
    </div>
  );
}
