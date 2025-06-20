import { promises as fs, existsSync } from 'node:fs';
import { join } from 'node:path';
import type { GameState } from '~/game-state/GameState.types';
import type { CaptureDetail, CaptureFile, CaptureListItem } from './Capture.types';

const CAPTURES_DIR = join(process.cwd(), '..', 'captures');

/**
 * Parse timestamp from capture filename
 * Expected format: screenshot_YYYYMMDD_HHMMSS.png or gamestate_YYYYMMDD_HHMMSS.json
 */
function parseTimestampFromFilename(filename: string): string | null {
  const match = filename.match(/(?:screenshot_|gamestate_)(\d{8}_\d{6})/);
  return match ? match[1] : null;
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: string): string {
  // Convert YYYYMMDD_HHMMSS to Date
  const year = timestamp.slice(0, 4);
  const month = timestamp.slice(4, 6);
  const day = timestamp.slice(6, 8);
  const hour = timestamp.slice(9, 11);
  const minute = timestamp.slice(11, 13);
  const second = timestamp.slice(13, 15);

  const date = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`);
  return date.toLocaleString();
}

/**
 * Get all capture files from the captures directory
 */
export async function getCaptureFiles(): Promise<CaptureFile[]> {
  try {
    if (!existsSync(CAPTURES_DIR)) {
      return [];
    }

    const files = await fs.readdir(CAPTURES_DIR);
    const captureMap = new Map<string, CaptureFile>();

    for (const file of files) {
      const timestamp = parseTimestampFromFilename(file);
      if (!timestamp) continue;

      if (!captureMap.has(timestamp)) {
        captureMap.set(timestamp, {
          timestamp,
          screenshotPath: '',
          gamestatePath: '',
          screenshotExists: false,
          gamestateExists: false,
        });
      }

      const capture = captureMap.get(timestamp);
      if (!capture) {
        continue;
      }
      if (file.startsWith('screenshot_') && file.endsWith('.png')) {
        capture.screenshotPath = join(CAPTURES_DIR, file);
        capture.screenshotExists = true;
      } else if (file.startsWith('gamestate_') && file.endsWith('.json')) {
        capture.gamestatePath = join(CAPTURES_DIR, file);
        capture.gamestateExists = true;
      }
    }

    return Array.from(captureMap.values()).sort((a, b) =>
      b.timestamp.localeCompare(a.timestamp),
    );
  } catch (error) {
    console.error('Error reading captures directory:', error);
    return [];
  }
}

/**
 * Get capture list items for display
 */
export async function getCaptureListItems(): Promise<CaptureListItem[]> {
  const captureFiles = await getCaptureFiles();

  return captureFiles.map(
    (capture): CaptureListItem => ({
      captureId: capture.timestamp,
      timestamp: capture.timestamp,
      formattedTimestamp: formatTimestamp(capture.timestamp),
      screenshotPath: capture.screenshotPath,
      gamestatePath: capture.gamestatePath,
      isComplete: capture.screenshotExists && capture.gamestateExists,
    }),
  );
}

/**
 * Get a specific capture by timestamp
 */
export async function getCaptureDetail(captureId: string): Promise<CaptureDetail | null> {
  try {
    const captureFiles = await getCaptureFiles();
    const capture = captureFiles.find((c) => c.timestamp === captureId);

    if (!capture || !capture.screenshotExists || !capture.gamestateExists) {
      return null;
    }

    // Read screenshot file and convert to data URL
    const screenshotBuffer = await fs.readFile(capture.screenshotPath);
    const screenshotDataUrl = `data:image/png;base64,${screenshotBuffer.toString('base64')}`;

    // Read and parse game state file
    const gamestateContent = await fs.readFile(capture.gamestatePath, 'utf-8');
    const gameState: GameState = JSON.parse(gamestateContent);

    return {
      timestamp: capture.timestamp,
      screenshotDataUrl,
      gameState,
      captureId,
    };
  } catch (error) {
    console.error('Error reading capture detail:', error);
    return null;
  }
}

/**
 * Check if captures directory exists
 */
export function capturesDirectoryExists(): boolean {
  return existsSync(CAPTURES_DIR);
}
