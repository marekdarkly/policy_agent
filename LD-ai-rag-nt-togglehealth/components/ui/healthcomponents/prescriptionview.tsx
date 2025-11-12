import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

export const PrescriptionAccount = () => {
	const [activePrescriptions, setActivePrescriptions] = useState(3);
	const [totalPrescriptions] = useState(5);

	return (
		<div className="h-full flex flex-col">
			<CardHeader className="pb-3">
				<div className="flex items-center justify-between">
					<CardTitle className="text-lg font-semibold text-green-600">
						Active Prescriptions
					</CardTitle>
					<Badge variant="secondary" className="bg-green-100 text-green-800">
						{activePrescriptions} Active
					</Badge>
				</div>
			</CardHeader>
			<CardContent className="flex-1 flex flex-col">
				<div className="space-y-4">
					<div className="flex items-center justify-between">
						<span className="text-sm text-gray-600">Prescription Status</span>
						<span className="text-sm font-medium">
							{activePrescriptions}/{totalPrescriptions}
						</span>
					</div>
					<Progress
						value={(activePrescriptions / totalPrescriptions) * 100}
						className="h-2"
					/>
					
					<div className="space-y-3">
						<div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Lisinopril 10mg</p>
								<p className="text-xs text-gray-500">Refill due: 3 days</p>
							</div>
							<Badge variant="outline" className="text-green-600 border-green-600">
								Active
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Metformin 500mg</p>
								<p className="text-xs text-gray-500">Refill due: 1 week</p>
							</div>
							<Badge variant="outline" className="text-green-600 border-green-600">
								Active
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Atorvastatin 20mg</p>
								<p className="text-xs text-gray-500">Refill due: 2 weeks</p>
							</div>
							<Badge variant="outline" className="text-gray-600 border-gray-600">
								Pending
							</Badge>
						</div>
					</div>
					
					<div className="mt-auto pt-4">
						<Button className="w-full bg-green-600 hover:bg-green-700">
							Request Refill
						</Button>
					</div>
				</div>
			</CardContent>
		</div>
	);
}; 