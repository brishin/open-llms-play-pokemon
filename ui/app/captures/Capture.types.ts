import type { GameState } from '~/game-state/GameState.types';

export interface CaptureFile {
  timestamp: string;
  screenshotPath: string;
  gamestatePath: string;
  screenshotExists: boolean;
  gamestateExists: boolean;
}

export interface CaptureDetail {
  timestamp: string;
  screenshotDataUrl: string;
  gameState: GameState;
  captureId: string;
}

export interface CaptureListItem {
  captureId: string;
  timestamp: string;
  formattedTimestamp: string;
  screenshotPath: string;
  gamestatePath: string;
  isComplete: boolean; // Both screenshot and gamestate exist
}