import { NavLink } from "react-router";
import dayjs from "~/dayjs";
import type { MLFlowRun } from "~/mflow/MLFlowClient";
import { BoxContainer } from "./BoxContainer";

export default function ExperimentsNav({ runs }: { runs: MLFlowRun[] }) {
	const getLatestMetric = (run: MLFlowRun, metricKey: string) => {
		const metrics = run.data.metrics || [];
		const metric = metrics.find((m) => m.key === metricKey);
		return metric?.value;
	};

	const getRunDuration = (run: MLFlowRun) => {
		if (!run.info.end_time) return "Running...";
		const duration = (run.info.end_time - run.info.start_time) / 1000;
		return `${Math.round(duration)}s`;
	};

	const getStatusColor = (status: string) => {
		switch (status) {
			case "FINISHED":
				return "text-success";
			case "FAILED":
				return "text-error";
			case "RUNNING":
				return "text-info";
			default:
				return "text-muted";
		}
	};

	return (
		<BoxContainer
			as="nav"
			shear="top"
			className="min-w-[16ch] h-full flex flex-col"
			title={`Runs (${runs.length})`}
		>
			<div className="my-[1lh] px-[1ch] flex-1 min-h-0">
				<div className="overflow-y-auto gap-[1lh] h-full">
					<ul>
						{runs.map((run) => {
							const badges = getLatestMetric(run, "badges");
							const partyCount = getLatestMetric(run, "party_count");

							return (
								<li
									key={run.info.run_id}
									className="border-b border-subtle pb-[0.5lh]"
								>
									<NavLink
										to={`/run/${run.info.run_id}`}
										className={({ isActive }) =>
											`block hover:bg-hover p-[0.5ch] transition-colors ${
												isActive ? "bg-active" : ""
											}`
										}
									>
										<div
											className="font-medium truncate"
											title={run.info.run_name}
										>
											{run.info.run_name}
										</div>
										<div className={`${getStatusColor(run.info.status)}`}>
											{run.info.status}
										</div>
										<div className="text-muted mt-[0.25lh]">
											{getRunDuration(run)}
										</div>
										{(badges !== undefined || partyCount !== undefined) && (
											<div className="text-subtle mt-[0.25lh] space-y-[0.125lh]">
												{badges !== undefined && <div>🏆 {badges} badges</div>}
												{partyCount !== undefined && (
													<div>👥 {partyCount} pokemon</div>
												)}
											</div>
										)}
										<div className="text-muted mt-[0.25lh]">
											{dayjs
												.duration(dayjs(run.info.end_time).diff(dayjs()))
												.humanize(true)}
										</div>
									</NavLink>
								</li>
							);
						})}
					</ul>
				</div>
			</div>
		</BoxContainer>
	);
}
