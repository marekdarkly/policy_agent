import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetFooter,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import { useFlags } from "@/utils/industryHook";

import { CreditCard } from "lucide-react";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "../table";
import { useEffect, useState } from "react";
import { TransactionInterface } from "@/utils/typescriptTypesInterfaceIndustry";
import BankDashboardAccountCard from "./BankDashboardAccountCard";

export function CreditAccount() {
    const { financialDBMigration, togglebankDBGuardedRelease } = useFlags();
    const [transactions, setTransactions] = useState<TransactionInterface[]>([]);

    async function getTransactions() {
        const response = await fetch("/api/creditdata");
        let transactionsJson: TransactionInterface[];
        if (response.status == 200) {
            const data = await response?.json();

            transactionsJson = data;
        } else {
            transactionsJson = [
                {
                    id: 0,
                    date: "",
                    merchant: "",
                    status: "Server Error",
                    amount: 0,
                    accounttype: "",
                    user: "",
                },
            ];
        }
        setTransactions(transactionsJson);
        return transactionsJson;
    }

    useEffect(() => {
        getTransactions();
    }, [financialDBMigration]);

    useEffect(() => {
        getTransactions();
    }, [togglebankDBGuardedRelease]);

    return (
        <Sheet>
            <SheetTrigger className=" h-full  w-full">
                <BankDashboardAccountCard
                    cardIcon={<CreditCard className="text-blue-700 h-8 w-8" />}
                    cardTitle="GSF Platinum Credit"
                    accountNumber="(***4222)"
                    cardSubtitle="APR 13.875%"
                    balanceLabel="Total Credit Balance"
                    balanceNumber="$1,203.00"
                    bottomText="Next Due: March 15th, 2025"
                />
            </SheetTrigger>
            <SheetContent className="w-full lg:w-1/2 overflow-auto" side="right">
                <SheetHeader>
                    <SheetTitle className="font-sohne text-2xl">
                        <div className="flex-col">
                            <div className="flex">GSF Platinum Credit Account</div>
                            {financialDBMigration === "complete" || togglebankDBGuardedRelease ? (
                                <div className="flex text-center items-center justify-center my-6 bg-green-200 text-zinc-500 font-sohnebuch font-extralight text-base py-2">
                                    Retrieving data from DynamoDB
                                </div>
                            ) : (
                                <div className="flex text-center items-center justify-center my-6 bg-amber-200 font-sohnebuch font-extralight text-base py-2">
                                    Retrieving data from RDS
                                </div>
                            )}
                        </div>
                    </SheetTitle>
                    <SheetDescription className="font-sohne">
                        Transaction history for your GSF Platinum Credit Account
                    </SheetDescription>
                </SheetHeader>

                <Table className="">
                    <TableCaption>A list of your recent credit transactions.</TableCaption>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Invoice</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Method</TableHead>
                            <TableHead className="text-right">Amount</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {transactions.map((invoice, i) => (
                            <TableRow key={i}>
                                <TableCell className="font-medium">{invoice.date}</TableCell>
                                <TableCell>{invoice.merchant}</TableCell>
                                <TableCell>{invoice.status}</TableCell>
                                <TableCell className="text-right">{invoice.amount}</TableCell>
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
