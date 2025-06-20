'use client';

import { useEffect, useRef, useState } from 'react';
import { Stage, Layer, Image as KonvaImage, Rect, Line, Text } from 'react-konva';
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

        // Determine color based on walkability (original logic)
        let fillColor = 'transparent';
        if (tile.is_walkable) {
          fillColor = 'rgba(0, 255, 0, 0.3)'; // Green for walkable
        } else {
          fillColor = 'rgba(255, 0, 0, 0.3)'; // Red for blocked
        }

        // Collect special tile labels (for text overlays)
        const tileLabels: string[] = [];
        if (tile.has_sign) tileLabels.push('S');
        if (tile.has_bookshelf) tileLabels.push('B');
        if (tile.strength_boulder) tileLabels.push('R');
        if (tile.cuttable_tree) tileLabels.push('T');
        if (tile.pc_accessible) tileLabels.push('PC');
        if (tile.hidden_item_id !== null) tileLabels.push('H');
        if (tile.game_corner_tile) tileLabels.push('G');
        if (tile.is_fly_destination) tileLabels.push('F');

        // Special colors for special tiles (original priority)
        if (tile.is_encounter_tile) {
          fillColor = 'rgba(255, 255, 0, 0.4)'; // Yellow for grass/encounters
        }
        if (tile.is_warp_tile) {
          fillColor = 'rgba(0, 0, 255, 0.4)'; // Blue for doors/warps
        }
        if (tile.is_ledge_tile) {
          fillColor = 'rgba(255, 165, 0, 0.4)'; // Orange for ledges
        }

        // Special stroke for trainer sight lines
        if (tile.trainer_sight_line) {
          fillColor = 'rgba(255, 0, 0, 1.0)';
        }

        // Highlight player position (2x2 tiles starting at 8,9) - highest priority
        const isPlayerTile = x >= 8 && x <= 9 && y >= 8 && y <= 9;
        if (isPlayerTile) {
          fillColor = 'rgba(255, 0, 255, 0.6)'; // Magenta for player position
        }

        overlays.push(
          <Rect
            key={`tile-${x}-${y}`}
            x={pixelX}
            y={pixelY}
            width={tileWidth}
            height={tileHeight}
            fill={fillColor}
            stroke={`rgba(0, 0, 0, 0.2)`}
            strokeWidth={1}
          />,
        );

        // Add text labels for special tiles
        if (tileLabels.length > 0) {
          const labelText = tileLabels.join(',');
          const fontSize = Math.min(tileWidth, tileHeight) * 0.4;

          overlays.push(
            <Text
              key={`tile-label-${x}-${y}`}
              x={pixelX}
              y={pixelY}
              width={tileWidth}
              height={tileHeight}
              text={labelText}
              fontSize={fontSize}
              fill="black"
              stroke="white"
              strokeWidth={0.2}
              align="center"
              verticalAlign="middle"
              fontFamily="monospace"
              fontStyle="bold"
            />,
          );
        }

        // Add ledge direction arrows
        if (tile.is_ledge_tile && tile.ledge_direction) {
          const arrowCenterX = pixelX + tileWidth / 2;
          const arrowCenterY = pixelY + tileHeight / 2;
          const arrowSize = Math.min(tileWidth, tileHeight) * 0.3;

          let arrowPoints: number[] = [];

          // Create triangle points based on direction
          switch (tile.ledge_direction.toLowerCase()) {
            case 'up':
            case 'north':
              arrowPoints = [
                arrowCenterX,
                arrowCenterY - arrowSize,
                arrowCenterX - arrowSize * 0.6,
                arrowCenterY + arrowSize * 0.3,
                arrowCenterX + arrowSize * 0.6,
                arrowCenterY + arrowSize * 0.3,
              ];
              break;
            case 'down':
            case 'south':
              arrowPoints = [
                arrowCenterX,
                arrowCenterY + arrowSize,
                arrowCenterX - arrowSize * 0.6,
                arrowCenterY - arrowSize * 0.3,
                arrowCenterX + arrowSize * 0.6,
                arrowCenterY - arrowSize * 0.3,
              ];
              break;
            case 'left':
            case 'west':
              arrowPoints = [
                arrowCenterX - arrowSize,
                arrowCenterY,
                arrowCenterX + arrowSize * 0.3,
                arrowCenterY - arrowSize * 0.6,
                arrowCenterX + arrowSize * 0.3,
                arrowCenterY + arrowSize * 0.6,
              ];
              break;
            case 'right':
            case 'east':
              arrowPoints = [
                arrowCenterX + arrowSize,
                arrowCenterY,
                arrowCenterX - arrowSize * 0.3,
                arrowCenterY - arrowSize * 0.6,
                arrowCenterX - arrowSize * 0.3,
                arrowCenterY + arrowSize * 0.6,
              ];
              break;
          }

          if (arrowPoints.length > 0) {
            overlays.push(
              <Line
                key={`ledge-arrow-${x}-${y}`}
                points={arrowPoints}
                fill="rgba(0, 0, 0, 0.8)"
                closed={true}
              />,
            );
          }
        }
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

  const containerProps = onClick
    ? {
        onClick,
        onKeyDown: (e: React.KeyboardEvent) => e.key === 'Enter' && onClick(),
        role: 'button' as const,
        tabIndex: 0,
      }
    : {};

  return (
    <div
      ref={containerRef}
      className={`${className} flex items-center justify-center`}
      style={{ width: '100%', height: 'auto' }}
      {...containerProps}
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
