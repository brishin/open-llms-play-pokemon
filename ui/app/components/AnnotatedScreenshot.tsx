'use client';

import { useEffect, useRef, useState } from 'react';
import { Stage, Layer, Image as KonvaImage } from 'react-konva';
import Konva from 'konva';

interface AnnotatedScreenshotProps {
  src: string;
  alt: string;
  className?: string;
  maxWidth?: number;
  maxHeight?: number;
  onClick?: () => void;
}

export function AnnotatedScreenshot({
  src,
  alt,
  className = '',
  maxWidth = 800,
  maxHeight = 600,
  onClick,
}: AnnotatedScreenshotProps) {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<Konva.Image>(null);

  const calculateDimensions = (img: HTMLImageElement, containerWidth: number, containerHeight: number) => {
    const aspectRatio = img.width / img.height;

    // Use container dimensions as constraints, but respect maxWidth/maxHeight
    const effectiveMaxWidth = Math.min(maxWidth, containerWidth || maxWidth);
    const effectiveMaxHeight = Math.min(maxHeight, containerHeight || maxHeight);

    // Calculate scale to fit within container (can scale up or down)
    const scaleX = effectiveMaxWidth / img.width;
    const scaleY = effectiveMaxHeight / img.height;
    const scale = Math.min(scaleX, scaleY);

    const width = img.width * scale;
    const height = img.height * scale;

    return { width, height };
  };

  useEffect(() => {
    const img = new window.Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      setImage(img);

      // Get container dimensions if available
      const container = containerRef.current;
      const containerWidth = container?.clientWidth || maxWidth;
      const containerHeight = container?.clientHeight || maxHeight;

      const newDimensions = calculateDimensions(img, containerWidth, containerHeight);
      setDimensions(newDimensions);
    };

    img.onerror = () => {
      console.error('Failed to load image:', src);
    };

    img.src = src;

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [src, maxWidth, maxHeight]);

  // Handle container resize
  useEffect(() => {
    if (!image) return;

    const handleResize = () => {
      const container = containerRef.current;
      if (!container) return;

      const containerWidth = container.clientWidth;
      const containerHeight = container.clientHeight;
      const newDimensions = calculateDimensions(image, containerWidth, containerHeight);
      setDimensions(newDimensions);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [image, maxWidth, maxHeight]);

  if (!image || dimensions.width === 0) {
    return (
      <div
        ref={containerRef}
        className={`flex items-center justify-center bg-gray-100 ${className}`}
        style={{ minHeight: '200px', width: '100%' }}
      >
        <span className="text-gray-500">Loading...</span>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`${className} flex items-center justify-center`}
      onClick={onClick}
      style={{ width: '100%', height: 'auto' }}
    >
      <Stage
        width={dimensions.width}
        height={dimensions.height}
        style={{ 
          cursor: onClick ? 'pointer' : 'default',
          maxWidth: '100%',
          height: 'auto'
        }}
      >
        <Layer>
          <KonvaImage
            ref={imageRef}
            image={image}
            width={dimensions.width}
            height={dimensions.height}
            imageSmoothingEnabled={false}
          />
        </Layer>
      </Stage>
    </div>
  );
}
