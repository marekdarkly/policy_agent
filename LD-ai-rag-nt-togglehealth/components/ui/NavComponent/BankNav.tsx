import React, { useContext } from "react";
import { useLDClient } from "@/utils/industryHook";
import NavWrapper from "@/components/ui/NavComponent/NavWrapper";
import CSNavWrapper from "@/components/ui/NavComponent/CSNavWrapper";
import NavLogo from "@/components/ui/NavComponent/NavLogo";
import NavbarLeftSideWrapper from "@/components/ui/NavComponent/NavbarLeftSideWrapper";
import NavLinkButton from "@/components/ui/NavComponent/NavLinkButton";
import NavbarRightSideWrapper from "@/components/ui/NavComponent/NavbarRightSideWrapper";
import NavbarLogin from "@/components/ui/NavComponent/NavbarLogin";
import NavbarDropdownMenu from "@/components/ui/NavComponent/NavbarDropdownMenu";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { CSNav } from "@/components/ui/csnav";
import { NavbarSignUpButton } from "@/components/ui/NavComponent/NavbarSignUpInButton";
import { NAV_ELEMENTS_VARIANT, BANK } from "@/utils/constants";
import { useRouter } from "next/router";
import LoginContext from "@/utils/contexts/login";
import Link from "next/link";
import LiveLogsContext from "@/utils/contexts/LiveLogsContext";

const BankNav = ({ industry = 'banking' }: { industry?: string }) => {
	const { isLoggedIn } = useContext(LoginContext);
	const router = useRouter();
	const { logLDMetricSent } = useContext(LiveLogsContext);
	const ldClient = useLDClient();

	return (
		<NavWrapper>
			<>
				<CSNavWrapper>
					<CSNav />
				</CSNavWrapper>

				<NavLogo
					altText={industry}
				/>

				{/* left side navbar template */}

				<NavbarLeftSideWrapper>
					<>
						{NAV_ELEMENTS_VARIANT[BANK]?.navLinks.map((navLink, index) => {
							return (
								<NavLinkButton
									text={navLink?.text}
									href={navLink?.href}
									navLinkColor={NAV_ELEMENTS_VARIANT[BANK]?.navLinkColor}
									index={index}
									key={index}
								/>
							);
						})}
					</>
				</NavbarLeftSideWrapper>

				<NavbarDropdownMenu>
					<>
						{NAV_ELEMENTS_VARIANT[BANK]?.navLinks.map((navLink, index) => {
							return (
                                <DropdownMenuItem key={index}>
                                <Link href={navLink?.href}>
                                    {navLink?.text}
                                </Link>
                            </DropdownMenuItem>
							);
						})}
					</>
				</NavbarDropdownMenu>

				{/* right side navbar template */}
				<NavbarRightSideWrapper>
					<>
						{!isLoggedIn && (
							<>
								<NavbarSignUpButton
									backgroundColor="bg-gradient-bank hidden sm:block"
									onClick={() => {
										ldClient?.track("sign_up_started");
										logLDMetricSent({ metricKey: "sign_up_started" });
										router.push("/signup");
									}}
								/>
							</>
						)}

						<NavbarLogin />
					</>
				</NavbarRightSideWrapper>
			</>
		</NavWrapper>
	);
};

export default BankNav;
