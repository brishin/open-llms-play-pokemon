import { useEffect, useState } from "react";
import { useFetcher } from "react-router";
import type { GameState } from "../game-state/GameState.types";
import {
	findClosestGameStateStep,
	getGameStateApiUrl,
	getGameStateFiles,
} from "../game-state/GameStates";
import { AnnotatedScreenshot } from "./AnnotatedScreenshot";
import { BoxContainer } from "./BoxContainer";

interface ScreenshotsPaneProps {
	artifacts: any[];
	runId: string;
	currentIndex: number;
	setCurrentIndex: (index: number) => void;
}

export function ScreenshotsPane({
	artifacts,
	runId,
	currentIndex,
	setCurrentIndex,
}: ScreenshotsPaneProps) {
	const [showAnnotations, setShowAnnotations] = useState(true);
	const [selectedArtifactPath, setSelectedArtifactPath] = useState<string>("");
	const fetcher = useFetcher<GameState>();

	// Filter for screenshot artifacts and sort by step number
	const screenshots = artifacts
		.filter(
			(artifact) =>
				artifact?.path?.startsWith("screenshot_") &&
				artifact?.path?.endsWith(".png"),
		)
		.sort((a, b) => {
			const stepA = Number.parseInt(
				a.path.match(/screenshot_(\d+)\.png/)?.[1] || "0",
			);
			const stepB = Number.parseInt(
				b.path.match(/screenshot_(\d+)\.png/)?.[1] || "0",
			);
			return stepA - stepB;
		});

	const getArtifactUrl = (artifactPath: string) => {
		return `/api/mlflow/artifact?runId=${encodeURIComponent(runId)}&artifactPath=${encodeURIComponent(artifactPath)}`;
	};

	const getCurrentScreenshot = () => {
		if (screenshots.length === 0) return null;
		return screenshots[currentIndex];
	};

	const getCurrentStepNumber = () => {
		const screenshot = getCurrentScreenshot();
		if (!screenshot) return 0;
		const stepMatch = screenshot.path.match(/screenshot_(\d+)\.png/);
		return stepMatch ? Number.parseInt(stepMatch[1]) : currentIndex + 1;
	};

	const gameStateFiles = getGameStateFiles(artifacts);

	const loadGameData = (artifactPath: string) => {
		setSelectedArtifactPath(artifactPath);
		fetcher.load(getGameStateApiUrl(runId, artifactPath));
	};

	// Load game state based on current step
	useEffect(() => {
		const currentStepNumber = getCurrentStepNumber();
		const closestStep = findClosestGameStateStep(
			gameStateFiles,
			currentStepNumber,
		);
		if (closestStep && closestStep.path !== selectedArtifactPath) {
			loadGameData(closestStep.path);
		}
	}, [currentIndex, gameStateFiles, selectedArtifactPath, runId]);

	const handleSliderChange = (event: React.ChangeEvent<HTMLInputElement>) => {
		setCurrentIndex(Number.parseInt(event.target.value));
	};

	const handlePrevious = () => {
		setCurrentIndex(Math.max(0, currentIndex - 1));
	};

	const handleNext = () => {
		setCurrentIndex(Math.min(screenshots.length - 1, currentIndex + 1));
	};

	// Keyboard navigation
	useEffect(() => {
		const handleKeyDown = (event: KeyboardEvent) => {
			if (event.key === "ArrowLeft") {
				event.preventDefault();
				setCurrentIndex(Math.max(0, currentIndex - 1));
			} else if (event.key === "ArrowRight") {
				event.preventDefault();
				setCurrentIndex(Math.min(screenshots.length - 1, currentIndex + 1));
			}
		};

		window.addEventListener("keydown", handleKeyDown);
		return () => window.removeEventListener("keydown", handleKeyDown);
	}, [currentIndex, screenshots.length, setCurrentIndex]);

	if (screenshots.length === 0) {
		return (
			<BoxContainer
				shear="top"
				title="Screenshots"
				className="px-[1ch] pb-[1ch]"
			>
				<div className="mt-[0.5lh] text-sm text-muted">
					No screenshots found for this run.
				</div>
			</BoxContainer>
		);
	}

	const currentScreenshot = getCurrentScreenshot();
	const currentStepNumber = getCurrentStepNumber();

	return (
		<BoxContainer
			shear="top"
			title={`Step ${currentStepNumber} (${currentIndex + 1}/${screenshots.length})`}
			className="px-[1ch]"
		>
			<div className="flex flex-col">
				{/* Main screenshot display */}
				<div className="flex justify-center min-h-[20lh]">
					{currentScreenshot && (
						<AnnotatedScreenshot
							src={getArtifactUrl(currentScreenshot.path)}
							alt={`Screenshot ${currentStepNumber}`}
							className="max-w-[60ch] min-w-3/4"
							maxWidth={480}
							maxHeight={320}
							gameState={fetcher.data}
							showAnnotations={showAnnotations}
						/>
					)}
				</div>

				{/* Controls */}
				<div className="flex flex-col">
					{/* Toggle Annotations Button */}
					<div className="flex justify-center">
						<button
							type="button"
							onClick={() => setShowAnnotations(!showAnnotations)}
						>
							{showAnnotations ? "Hide Annotations" : "Show Annotations"}
						</button>
					</div>

					{/* Slider */}
					<div className="flex items-center gap-[1ch]">
						<div box-="square">
							<button
								type="button"
								onClick={handlePrevious}
								disabled={currentIndex === 0}
							>
								←
							</button>
						</div>

						<div className="flex-grow flex items-center gap-[1ch]">
							<span className="text-sm text-subtle min-w-[3ch]">1</span>
							<input
								type="range"
								min="0"
								max={screenshots.length - 1}
								value={currentIndex}
								onChange={handleSliderChange}
								className="flex-grow h-[0.5lh] bg-surface rounded-lg appearance-none cursor-pointer slider"
							/>
							<span className="text-sm text-subtle min-w-[3ch]">
								{screenshots.length}
							</span>
						</div>

						<div box-="square">
							<button
								type="button"
								onClick={handleNext}
								disabled={currentIndex === screenshots.length - 1}
							>
								→
							</button>
						</div>
					</div>

					{/* Step info */}
					<div className="text-center text-subtle italic">
						Use arrow keys or slider to navigate
					</div>
				</div>
			</div>
		</BoxContainer>
	);
}
