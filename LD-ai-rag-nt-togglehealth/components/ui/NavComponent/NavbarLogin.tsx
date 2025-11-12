import { useRef, useState, useContext } from "react";
import { AvatarImage, Avatar } from "../avatar";
import { User } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "../popover";
import LoginContext from "@/utils/contexts/login";
import { Button } from "@/components/ui/button";
import { QuickLoginDialog } from "@/components/ui/quicklogindialog";
import { capitalizeFirstLetter } from "@/utils/utils";
import { NAV_ELEMENTS_VARIANT } from "@/utils/constants";
import { useIsMobile } from "@/components/hooks/use-mobile";
import {
	Sheet,
	SheetContent,
	SheetClose,
	SheetTrigger,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { COMPANY_LOGOS, STARTER_PERSONAS } from "@/utils/constants";

const NavBarLoginInterface = ({ children }: { children?: React.ReactNode }) => {
	const { isLoggedIn, userObject, logoutUser, loginUser } =
		useContext(LoginContext);

	const inputRef = useRef<HTMLInputElement>(null);
	const [defaultEmail, setDefaultEmail] = useState<string>(
		STARTER_PERSONAS[0].personaemail
	);

	function handleLogin(): void {
		if (!defaultEmail) return;

		loginUser(defaultEmail);
	}

	return (
		<>
			<div className="w-full bg-white shadow-2xl mx-auto text-black p-4 sm:p-8 h-full flex flex-col sm:flex-none justify-center lg:justify-normal">
				<div className="flex flex-col justify-between h-full">
					<div>
						<div className="mx-auto flex place-content-center w-full">
							{isLoggedIn && (
								<img
									src={userObject?.personaimage || "personas/ToggleAvatar.png"}
									className="rounded-full h-48 mb-4"
								/>
							)}

							{!isLoggedIn && (
								<img
									src={COMPANY_LOGOS["bank"].vertical.src}
									className="pt-4 pb-8"
								/>
							)}
						</div>

						<div className="w-full flex flex-col gap-y-4">
							{!isLoggedIn && (
								<Input
									placeholder="Email"
									value={defaultEmail}
									ref={inputRef}
									required
									className=" outline-none border-0 border-b-2 text-xl"
									onChange={(e) => setDefaultEmail(e.target.value)}
								/>
							)}

							{isLoggedIn && (
								<div className="mx-auto text-center items-center align-center flex text-black font-sohnelight text-xl align-center">
									<p>
										{NAV_ELEMENTS_VARIANT["bank"]?.popoverMessage}
										{userObject?.personaname || userObject.personaname}, as a
										<br></br>
										<span className="text-2xl">
											{capitalizeFirstLetter(userObject?.personatier)} Tier
										</span>
										!
									</p>
								</div>
							)}

							<Button
								onClick={() => {
									isLoggedIn ? logoutUser() : handleLogin();
								}}
								className={` w-full mx-auto font-sohnelight rounded-none  text-lg bg-loginComponentBlue text-white`}
							>
								{isLoggedIn ? "Logout" : "Login with SSO"}
							</Button>
							<QuickLoginDialog />

							{!isLoggedIn && (
								<div
									className="flex flex-row items-start sm:items-baseline
                     font-sohnelight font-extralight sm:flex-col text-xs justify-between gap-y-2"
								>
									<div className="">
										<p>Forgot Password?</p>
									</div>
									<div>
										<p className="text-right flex flex-col sm:flex-row ">
											Don't have an account?{" "}
											<a href="#" className=" ml-2 cursor-auto">
												Sign Up
											</a>
										</p>
									</div>
								</div>
							)}
						</div>
					</div>

					{children}
				</div>
			</div>
		</>
	);
};

const NavbarLogin = () => {
	const { userObject, isLoggedIn } = useContext(LoginContext);

	const isMobile = useIsMobile();

	if (isMobile) {
		return (
			<Sheet>
				<SheetTrigger>
					<Avatar className="shadow-xl flex items-center justify-center bg-bankdarkblue animate-pulse">
						{isLoggedIn ? (
							<AvatarImage src={userObject?.personaimage} className="" />
						) : (
							<User className="text-white" />
						)}
					</Avatar>
				</SheetTrigger>
				<SheetContent
					data-sidebar="sidebar"
					data-mobile="true"
					className="w-full h-full bg-sidebar p-0 text-sidebar-foreground !border-0 [&>button]:hidden font-audimat"
					side={"right"}
					id="sidebar-mobile"
				>
					<div className="flex h-full w-full flex-col ">
						<NavBarLoginInterface>
							<SheetClose className="h-10 w-full bg-airlinedarkblue text-white mt-auto">
								Close
							</SheetClose>
						</NavBarLoginInterface>
					</div>
				</SheetContent>
			</Sheet>
		);
	}

	return (
		<Popover>
			<PopoverTrigger>
				<Avatar className="shadow-xl flex items-center justify-center bg-bankdarkblue animate-pulse">
					{isLoggedIn ? (
						<AvatarImage src={userObject?.personaimage} className="" />
					) : (
						<User className="text-white" />
					)}
				</Avatar>
			</PopoverTrigger>

			<PopoverContent className={`p-0 font-audimat`} side="bottom" align="end">
				<NavBarLoginInterface />
			</PopoverContent>
		</Popover>
	);
};

export default NavbarLogin;
