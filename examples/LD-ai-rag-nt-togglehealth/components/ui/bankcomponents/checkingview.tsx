import { Button } from "@/components/ui/button";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
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
import { useFlags } from "@/utils/industryHook";
import { CiMoneyCheck1 } from "react-icons/ci";
import BankDashboardAccountCard from "./BankDashboardAccountCard";

type Transaction = {
    id: number;
    date: string;
    merchant: string;
    status: string;
    amount: number;
    accounttype: string;
    user: string;
};

export function CheckingAccount() {
    const [transactions, setTransactions] = useState<Transaction[]>([]);

    const { financialDBMigration, togglebankDBGuardedRelease } = useFlags();

    async function getTransactions() {
        const response = await fetch("/api/checkingdata");
        let transactionsJson: Transaction[];
        if (response.status == 200) {
            const data = await response.json();
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
            <SheetTrigger className=" h-full w-full" >
                <BankDashboardAccountCard
                    cardIcon={<CiMoneyCheck1 className="text-blue-700 h-8 w-8" />}
                    cardTitle="Platinum Checking"
                    accountNumber="(***2982)"
                    cardSubtitle="No Fee Checking"
                    balanceLabel="Total Checking Balance"
                    balanceNumber="$83,758.52"
                />
            </SheetTrigger>
            <SheetContent className="w-full lg:w-1/2 overflow-auto" side="right">
                <SheetHeader>
                    <SheetTitle className="font-sohne text-2xl">
                        <div className="flex-col">
                            <div className="flex">Checking Account</div>
                            {financialDBMigration === "complete" || togglebankDBGuardedRelease ? (
                                <div className="flex text-center items-center justify-center my-6 bg-green-200 text-zinc-500 font-sohnebuch font-extralight text-base py-2">
                                    Retrieving data from DynamoDB
                                </div>
                            ) : (
                                <div className="flex text-center items-center justify-center my-6 bg-amber-200 font-sohnebuch font-extralight text-base py-2">
                                    Retrieving Data from RDS
                                </div>
                            )}
                        </div>
                    </SheetTitle>
                    <SheetDescription className="font-sohne">
                        Understand the Balance of Your Checking Accounts
                    </SheetDescription>
                </SheetHeader>

                <Table className="">
                    <TableCaption>
                        <Button
                            className="flex rounded-none bg-blue-700 text-lg font-sohnelight"
                            onClick={getTransactions}
                        >
                            Refresh Data
                        </Button>
                    </TableCaption>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Date</TableHead>
                            <TableHead>Merchant</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Amount</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {transactions.map((item, i) => (
                            <TableRow key={i}>
                                <TableCell className="font-medium">{item.date}</TableCell>
                                <TableCell>{item.merchant}</TableCell>
                                <TableCell>{item.status}</TableCell>
                                <TableCell className="text-right">
                                    {item.amount.toLocaleString("en-US", {
                                        style: "currency",
                                        currency: "USD",
                                    })}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </SheetContent>
        </Sheet>
    );
}
