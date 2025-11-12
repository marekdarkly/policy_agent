import { WellnessManagementGraphDataType } from "@/utils/typescriptTypesInterfaceIndustry";
import { Card, CardContent, CardHeader, CardTitle } from "../card";
import { Badge } from "../badge";

interface WellnessManagementGraphProps {
	data: WellnessManagementGraphDataType[];
}

export const WellnessManagementGraph: React.FC<WellnessManagementGraphProps> = ({ data }) => {
	const maxScore = Math.max(...data.map(item => item.wellnessScore));
	const minScore = Math.min(...data.map(item => item.wellnessScore));
	const avgScore = Math.round(data.reduce((sum, item) => sum + item.wellnessScore, 0) / data.length);

	const getScoreColor = (score: number) => {
		if (score >= 80) return "text-green-600";
		if (score >= 60) return "text-yellow-600";
		return "text-red-600";
	};

	const getScoreBadge = (score: number) => {
		if (score >= 80) return "bg-green-100 text-green-800";
		if (score >= 60) return "bg-yellow-100 text-yellow-800";
		return "bg-red-100 text-red-800";
	};

	return (
		<div className="space-y-6">
			<div className="grid grid-cols-3 gap-4">
				<Card className="border-purple-200">
					<CardContent className="p-4">
						<div className="text-center">
							<p className="text-sm text-gray-600">Average</p>
							<p className={`text-2xl font-bold ${getScoreColor(avgScore)}`}>{avgScore}</p>
						</div>
					</CardContent>
				</Card>
				<Card className="border-purple-200">
					<CardContent className="p-4">
						<div className="text-center">
							<p className="text-sm text-gray-600">Highest</p>
							<p className="text-2xl font-bold text-green-600">{maxScore}</p>
						</div>
					</CardContent>
				</Card>
				<Card className="border-purple-200">
					<CardContent className="p-4">
						<div className="text-center">
							<p className="text-sm text-gray-600">Lowest</p>
							<p className="text-2xl font-bold text-red-600">{minScore}</p>
						</div>
					</CardContent>
				</Card>
			</div>

			<div className="space-y-3">
				<h3 className="text-lg font-semibold text-purple-800">Monthly Mental Wellness Scores</h3>
				{data.map((item, index) => (
					<div key={index} className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
						<div className="flex items-center space-x-3">
							<span className="text-sm font-medium text-purple-700">{item.month}</span>
							<div className="w-32 bg-gray-200 rounded-full h-2">
								<div
									className={`h-2 rounded-full ${
										item.wellnessScore >= 80 ? "bg-green-500" :
										item.wellnessScore >= 60 ? "bg-yellow-500" : "bg-red-500"
									}`}
									style={{ width: `${(item.wellnessScore / 100) * 100}%` }}
								></div>
							</div>
						</div>
						<Badge className={getScoreBadge(item.wellnessScore)}>
							{item.wellnessScore}
						</Badge>
					</div>
				))}
			</div>

			<div className="text-xs text-gray-500 p-3 bg-purple-50 rounded-lg">
				<p className="font-semibold text-purple-700 mb-1">Score Guide:</p>
				<ul className="space-y-1">
					<li>• 80-100: Excellent mental wellness</li>
					<li>• 60-79: Good mental wellness</li>
					<li>• Below 60: Needs attention</li>
				</ul>
			</div>
		</div>
	);
};
