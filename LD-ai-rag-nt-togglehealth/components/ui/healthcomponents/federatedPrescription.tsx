import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export const FederatedPrescriptionAccount = () => {
	const [connectedProviders, setConnectedProviders] = useState(2);

	return (
		<div className="h-full flex flex-col">
			<CardHeader className="pb-3">
				<div className="flex items-center justify-between">
					<CardTitle className="text-lg font-semibold text-green-600">
						Federated Prescriptions
					</CardTitle>
					<Badge variant="secondary" className="bg-green-100 text-green-800">
						{connectedProviders} Connected
					</Badge>
				</div>
			</CardHeader>
			<CardContent className="flex-1 flex flex-col">
				<div className="space-y-4">
					<div className="space-y-3">
						<div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Kaiser Permanente</p>
								<p className="text-xs text-gray-500">5 active prescriptions</p>
							</div>
							<Badge variant="outline" className="text-green-600 border-green-600">
								Connected
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Blue Cross Blue Shield</p>
								<p className="text-xs text-gray-500">3 active prescriptions</p>
							</div>
							<Badge variant="outline" className="text-green-600 border-green-600">
								Connected
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Aetna</p>
								<p className="text-xs text-gray-500">Not connected</p>
							</div>
							<Badge variant="outline" className="text-gray-600 border-gray-600">
								Available
							</Badge>
						</div>
					</div>
					
					<div className="mt-auto pt-4 space-y-2">
						<Button className="w-full bg-green-600 hover:bg-green-700">
							Connect Provider
						</Button>
						<Button variant="outline" className="w-full">
							View All Prescriptions
						</Button>
					</div>
				</div>
			</CardContent>
		</div>
	);
}; 