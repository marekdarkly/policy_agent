import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetFooter,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../table";
import { MdHome } from "react-icons/md";
import BankDashboardAccountCard from "./BankDashboardAccountCard";

const payments = [
    { month: "11/2023", amount: 4123, status: "cleared" },
    { month: "10/2023", amount: 4123, status: "cleared" },
    { month: "09/2023", amount: 4123, status: "cleared" },
    { month: "08/2023", amount: 4123, status: "cleared" },
    { month: "07/2023", amount: 4123, status: "cleared" },
    { month: "06/2023", amount: 4123, status: "cleared" },
    { month: "05/2023", amount: 4123, status: "cleared" },
    { month: "04/2023", amount: 4123, status: "cleared" },
    { month: "03/2023", amount: 4123, status: "cleared" },
    { month: "02/2023", amount: 4123, status: "cleared" },
    { month: "01/2023", amount: 4123, status: "cleared" },
    { month: "12/2022", amount: 4123, status: "cleared" },
];

export function MorgtgageAccount() {
    return (
        <Sheet>
            <SheetTrigger className="h-full w-full">
                <BankDashboardAccountCard
                    cardIcon={<MdHome className="text-blue-700 h-8 w-8" />}
                    cardTitle="Mortgage Account"
                    accountNumber="(***6503)"
                    cardSubtitle="APR 3.875%"
                    balanceLabel="Remaining Balance"
                    balanceNumber="$712,124"
                    bottomText="Next Due: March 15th, 2025"
                />
            </SheetTrigger>
            <SheetContent className="w-full lg:w-1/2 overflow-auto" side="right">
                <SheetHeader>
                    <SheetTitle className="font-sohne text-2xl">Mortgage Account</SheetTitle>
                    <SheetDescription className="font-sohne">
                        Your home loan balance statement
                    </SheetDescription>
                </SheetHeader>

                <Table className="">
                    <TableHeader>
                        <TableRow>
                            <TableHead>Month</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Method</TableHead>
                            <TableHead className="text-right">Amount</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {payments.map((invoice, i) => (
                            <TableRow key={i}>
                                <TableCell className="font-medium">{invoice.month}</TableCell>
                                <TableCell>{invoice.status}</TableCell>
                                <TableCell>Checking</TableCell>
                                <TableCell className="text-right">${invoice.amount}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>

                <SheetFooter>
                    {/* <SheetClose asChild>
            <Button type="submit">Save changes</Button>
          </SheetClose> */}
                </SheetFooter>
            </SheetContent>
        </Sheet>
    );
}
