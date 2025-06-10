import { type ReactNode, type ElementType } from 'react';
import { twMerge } from 'tailwind-merge';

interface BoxContainerProps {
  children: ReactNode;
  className?: string;
  shear?: 'top' | boolean;
  as?: ElementType;
}

export function BoxContainer({ 
  children, 
  className = '', 
  shear = false,
  as: Element = 'div'
}: BoxContainerProps) {
  const shearAttr = shear === true ? 'top' : shear || undefined;
  
  return (
    <Element
      box-="square"
      shear-={shearAttr}
      className={twMerge('bg-background1', className)}
    >
      {children}
    </Element>
  );
}