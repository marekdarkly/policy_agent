import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

export const TelemedicineAccount = () => {
	const [upcomingAppointments, setUpcomingAppointments] = useState(2);
	const [totalAppointments] = useState(8);

	return (
		<div className="h-full flex flex-col">
			<CardHeader className="pb-3">
				<div className="flex items-center justify-between">
					<CardTitle className="text-lg font-semibold text-blue-600">
						Telemedicine Services
					</CardTitle>
					<Badge variant="secondary" className="bg-blue-100 text-blue-800">
						{upcomingAppointments} Upcoming
					</Badge>
				</div>
			</CardHeader>
			<CardContent className="flex-1 flex flex-col">
				<div className="space-y-4">
					<div className="flex items-center justify-between">
						<span className="text-sm text-gray-600">Appointment Status</span>
						<span className="text-sm font-medium">
							{upcomingAppointments}/{totalAppointments}
						</span>
					</div>
					<Progress
						value={(upcomingAppointments / totalAppointments) * 100}
						className="h-2"
					/>
					
					<div className="space-y-3">
						<div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Dr. Sarah Johnson</p>
								<p className="text-xs text-gray-500">Tomorrow, 2:00 PM</p>
							</div>
							<Badge variant="outline" className="text-blue-600 border-blue-600">
								Confirmed
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Dr. Michael Chen</p>
								<p className="text-xs text-gray-500">Friday, 10:30 AM</p>
							</div>
							<Badge variant="outline" className="text-blue-600 border-blue-600">
								Confirmed
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Dr. Emily Rodriguez</p>
								<p className="text-xs text-gray-500">Next week</p>
							</div>
							<Badge variant="outline" className="text-gray-600 border-gray-600">
								Pending
							</Badge>
						</div>
					</div>
					
					<div className="mt-auto pt-4 space-y-2">
						<Button className="w-full bg-blue-600 hover:bg-blue-700">
							Schedule Appointment
						</Button>
						<Button variant="outline" className="w-full">
							Join Meeting
						</Button>
					</div>
				</div>
			</CardContent>
		</div>
	);
}; 