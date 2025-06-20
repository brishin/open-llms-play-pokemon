import { type ElementType, type ReactNode } from 'react';
import { twMerge } from 'tailwind-merge';

interface BoxContainerProps {
  children: ReactNode;
  className?: string;
  shear?: 'top' | boolean;
  as?: ElementType;
  title?: string;
}

export function BoxContainer({
  children,
  className = '',
  shear = false,
  as: Element = 'div',
  title,
}: BoxContainerProps) {
  const shearAttr = shear === true ? 'top' : shear || undefined;

  return (
    <Element
      box-="square"
      shear-={shearAttr}
      className={twMerge('bg-background1 px-[1ch]', className)}
    >
      {title && <span variant-="background">{title}</span>}
      {children}
    </Element>
  );
}

export function BoxContainerContent({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={twMerge('mt-[0.5lh] mx-[1ch]', className)}>{children}</div>;
}
