import React from "react";

const SignUpProgressIndicator = ({pageNumber}:{pageNumber:number}) => {
	return (
		<div className="mb-10 flex items-center justify-center">
			<div className="flex items-center">
				<div className={`flex h-10 w-10 items-center justify-center rounded-full ${pageNumber >= 1 ? 'bg-blue-600' : 'bg-gray-300'} text-white`}>
					1
				</div>
				<div className={`w-[20vw] xl:w-32 h-1 ${pageNumber >= 1 ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
				<div className={`flex h-10 w-10 items-center justify-center rounded-full ${pageNumber >= 2 ? 'bg-blue-600' : 'bg-gray-300'} text-white`}>
					2
				</div>
				<div className={`w-[20vw] xl:w-32 h-1 ${pageNumber >= 2 ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
				<div className={`flex h-10 w-10 items-center justify-center rounded-full ${pageNumber >= 3 ? 'bg-blue-600' : 'bg-gray-300'} text-white`}>
					3
				</div>
			</div>
		</div>
	);
};

export default SignUpProgressIndicator;
