import type { Route } from "./+types/home";

export function loader() {
	return { name: "React Router" };
}

export default function Home({ loaderData }: Route.ComponentProps) {
	return (
		<div className="flex-row gap-1 grow">
			<nav box-="square" shear-="top" className="max-w-32 grow px-2">
				<span variant-="background">Traces</span>
				<div className="mt-[1lh] px-1">
					<div className="flex-row gap-[1lh] overflow-y-auto">
						<a href="/">Test</a>
					</div>
				</div>
			</nav>
		</div>
	);
}
