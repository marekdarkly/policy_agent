import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export interface WellnessManagementGraphDataType {
	month: string;
	wellnessScore: number;
}

export const WellnessManagementGraph = ({ data }: { data: WellnessManagementGraphDataType[] }) => {
	return (
		<div className="w-full h-full">
			<div className="flex items-center justify-between mb-4">
				<h3 className="text-lg font-semibold text-green-600">Wellness Score Trend</h3>
				<div className="text-sm text-gray-500">
					Current Score: {data[data.length - 1]?.wellnessScore || 0}
				</div>
			</div>
			<ResponsiveContainer width="100%" height={300}>
				<LineChart data={data}>
					<CartesianGrid strokeDasharray="3 3" />
					<XAxis dataKey="month" />
					<YAxis domain={[0, 100]} />
					<Tooltip 
						formatter={(value: any) => [`${value}`, 'Wellness Score']}
						labelFormatter={(label) => `Month: ${label}`}
					/>
					<Line 
						type="monotone" 
						dataKey="wellnessScore" 
						stroke="#10b981" 
						strokeWidth={3}
						dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
					/>
				</LineChart>
			</ResponsiveContainer>
		</div>
	);
}; 