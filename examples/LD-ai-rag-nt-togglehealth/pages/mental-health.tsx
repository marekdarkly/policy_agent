import { useIndustry } from "@/utils/industryHook";
import MentalHealthHomePage from "@/components/ui/mentalhealthcomponents/mentalHealthHomePage";
import MentalHealthUserDashboard from "@/components/ui/mentalhealthcomponents/mentalHealthUserDashboard";
import { useContext } from "react";
import LoginContext from "@/utils/contexts/login";

export default function MentalHealthPage() {
	const { industry } = useIndustry();
	const { isLoggedIn } = useContext(LoginContext);

	// Check if the current industry is mental-health
	if (industry !== "mental-health") {
		return (
			<div className="min-h-screen flex items-center justify-center">
				<div className="text-center">
					<h1 className="text-2xl font-bold text-gray-800 mb-4">
						Mental Health Experience Not Available
					</h1>
					<p className="text-gray-600">
						Please set the industry to "mental-health" to view this experience.
					</p>
				</div>
			</div>
		);
	}

	return (
		<div>
			{isLoggedIn ? <MentalHealthUserDashboard /> : <MentalHealthHomePage />}
		</div>
	);
}
