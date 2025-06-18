'use client';

import { useEffect, useRef, useState } from 'react';
import { Stage, Layer, Image as KonvaImage, Rect } from 'react-konva';
import Konva from 'konva';
import type { GameState } from '~/game-state/GameState.types';

interface AnnotatedScreenshotProps {
  src: string;
  alt: string;
  className?: string;
  maxWidth?: number;
  maxHeight?: number;
  onClick?: () => void;
  gameState?: GameState;
  showAnnotations?: boolean;
}

export function AnnotatedScreenshot({
  src,
  alt,
  className = '',
  maxWidth = 800,
  maxHeight = 600,
  onClick,
  gameState,
  showAnnotations = true,
}: AnnotatedScreenshotProps) {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<Konva.Image>(null);

  const calculateDimensions = (
    img: HTMLImageElement,
    containerWidth: number,
    containerHeight: number,
  ) => {
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

  const renderWalkabilityOverlay = () => {
    if (!gameState?.tile_matrix || !image) return null;

    const { tiles, width, height } = gameState.tile_matrix;
    const overlays: React.ReactNode[] = [];

    // GameBoy screen is 160x144 pixels, typically scaled up
    const gameWidth = 160;
    const gameHeight = 144;
    const tileSize = 8; // Each tile is 8x8 pixels on GameBoy

    // Calculate scale factors
    const scaleX = dimensions.width / gameWidth;
    const scaleY = dimensions.height / gameHeight;

    for (let y = 0; y < height && y < tiles.length; y++) {
      for (let x = 0; x < width && x < tiles[y].length; x++) {
        const tile = tiles[y][x];
        if (!tile) continue;

        // Calculate pixel position on screen
        const pixelX = x * tileSize * scaleX;
        const pixelY = y * tileSize * scaleY;
        const tileWidth = tileSize * scaleX;
        const tileHeight = tileSize * scaleY;

        // Determine color based on walkability
        let fillColor = 'transparent';
        let strokeColor = 'transparent';

        if (tile.is_walkable) {
          fillColor = 'rgba(0, 255, 0, 0.3)'; // Green for walkable
          strokeColor = 'rgba(0, 255, 0, 0.8)';
        } else {
          fillColor = 'rgba(255, 0, 0, 0.3)'; // Red for blocked
          strokeColor = 'rgba(255, 0, 0, 0.8)';
        }

        // Special colors for special tiles
        if (tile.is_encounter_tile) {
          fillColor = 'rgba(255, 255, 0, 0.4)'; // Yellow for grass/encounters
          strokeColor = 'rgba(255, 255, 0, 0.9)';
        }
        if (tile.is_warp_tile) {
          fillColor = 'rgba(0, 0, 255, 0.4)'; // Blue for doors/warps
          strokeColor = 'rgba(0, 0, 255, 0.9)';
        }
        if (tile.is_ledge_tile) {
          fillColor = 'rgba(255, 165, 0, 0.4)'; // Orange for ledges
          strokeColor = 'rgba(255, 165, 0, 0.9)';
        }

        // Highlight player position (2x2 tiles starting at 8,9)
        const isPlayerTile = x >= 8 && x <= 9 && y >= 8 && y <= 9;
        if (isPlayerTile) {
          fillColor = 'rgba(255, 0, 255, 0.6)'; // Magenta for player position
          strokeColor = 'rgba(255, 0, 255, 1.0)';
        }

        overlays.push(
          <Rect
            key={`tile-${x}-${y}`}
            x={pixelX}
            y={pixelY}
            width={tileWidth}
            height={tileHeight}
            fill={fillColor}
            stroke={strokeColor}
            strokeWidth={0.5}
          />,
        );
      }
    }

    return overlays;
  };

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
          height: 'auto',
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
          {showAnnotations && gameState?.tile_matrix && renderWalkabilityOverlay()}
        </Layer>
      </Stage>
    </div>
  );
}
