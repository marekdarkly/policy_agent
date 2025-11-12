import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export const FederatedTelemedicineAccount = () => {
	const [connectedServices, setConnectedServices] = useState(3);

	return (
		<div className="h-full flex flex-col">
			<CardHeader className="pb-3">
				<div className="flex items-center justify-between">
					<CardTitle className="text-lg font-semibold text-blue-600">
						Federated Telemedicine
					</CardTitle>
					<Badge variant="secondary" className="bg-blue-100 text-blue-800">
						{connectedServices} Connected
					</Badge>
				</div>
			</CardHeader>
			<CardContent className="flex-1 flex flex-col">
				<div className="space-y-4">
					<div className="space-y-3">
						<div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Teladoc Health</p>
								<p className="text-xs text-gray-500">2 upcoming appointments</p>
							</div>
							<Badge variant="outline" className="text-blue-600 border-blue-600">
								Connected
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Amwell</p>
								<p className="text-xs text-gray-500">1 upcoming appointment</p>
							</div>
							<Badge variant="outline" className="text-blue-600 border-blue-600">
								Connected
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">MDLive</p>
								<p className="text-xs text-gray-500">No upcoming appointments</p>
							</div>
							<Badge variant="outline" className="text-blue-600 border-blue-600">
								Connected
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">PlushCare</p>
								<p className="text-xs text-gray-500">Not connected</p>
							</div>
							<Badge variant="outline" className="text-gray-600 border-gray-600">
								Available
							</Badge>
						</div>
					</div>
					
					<div className="mt-auto pt-4 space-y-2">
						<Button className="w-full bg-blue-600 hover:bg-blue-700">
							Connect Service
						</Button>
						<Button variant="outline" className="w-full">
							View All Appointments
						</Button>
					</div>
				</div>
			</CardContent>
		</div>
	);
}; 