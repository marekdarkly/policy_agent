import {
	Sheet,
	SheetContent,
	SheetHeader,
	SheetTitle,
	SheetTrigger,
} from "@/components/ui/sheet";
import { Menu } from "lucide-react";
import { useRouter } from "next/router";
import { CSCard } from "./ldcscard";
import { motion } from "framer-motion";
import { CSNAV_ITEMS } from "@/utils/constants";
import { Settings } from "lucide-react";
import { useQuickCommandDialog } from "../generators/experimentation-automation/quickcommand";
import { Button } from "./button";

export function CSNav() {
	const router = useRouter();
	const { open, setOpen } = useQuickCommandDialog();//this doesn't work for some reason

	function goHome() {
		router.push("/");
	}

	return (
		<Sheet>
			<SheetTrigger asChild>
				<Menu size={24} className="text-navlink cursor-pointer" />
			</SheetTrigger>
			<SheetContent className="overflow-y-scroll w-full" side="left">
				<SheetHeader className="">
					<SheetTitle className="font-sohne text-2xl">
						<img
							src="ldLogo/ldLogo_black.svg"
							onClick={goHome}
							className="w-56 cursor-pointer"
							title="Go Home"
						/>
					</SheetTitle>
				</SheetHeader>
				<div className="grid gap-4 py-4">
					<div className="grid items-center gap-4">
						<div className="my-2 flex gap-x-2 items-center justify-between text-ldlightgray ">
							<h3 className="font-sohnelight tracking-widest text-sm">
								EXPLORE MORE
							</h3>
							{/* <Button
								className="cursor-pointer bg-transparent rounded-none  text-ldlightgray hover:bg-transparent"
								title="Go to Generator"
								onClick={() => setOpen((open) => !open)}
                
							>
								<Settings />
							</Button> */}
						</div>

						{CSNAV_ITEMS.map((item, index: number) => {
							return (
								<motion.div
									key={index}
									initial={{ x: -100, opacity: 0 }}
									whileHover={{ scale: 1.05 }}
									animate={{ x: 0, opacity: 1 }}
									transition={{ delay: 0.05, duration: 0.2 }}
									className="cursor-pointer"
									title={`Go to ${item.title}`}
								>
									<div
										onClick={() => router.push(item.link)}
										className={`bg-gradient-to-r from-${index}-start to-${index}-end rounded-3xl shadow-lg`}
									>
										<CSCard
											cardTitle={item.title}
											icon={item.icon}
											iconHover={item.icon}
											hoverBackground={item.hoverBackground}
											noHoverBackground={item.noHoverBackground}
										/>
									</div>
								</motion.div>
							);
						})}
					</div>
				</div>
			</SheetContent>
		</Sheet>
	);
}
