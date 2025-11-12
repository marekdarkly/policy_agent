import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import { Landmark } from "lucide-react";
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

export function FederatedCheckingAccount() {
    const [transactions, setTransactions] = useState<TransactionInterface[]>([]);

    async function getTransactions() {
        const response = await fetch("/api/checkingdata");
        let transactionsJson: TransactionInterface[];
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
    }, []);

    return (
        <Sheet>
            <SheetTrigger className="h-full w-full">
                <BankDashboardAccountCard
                    cardIcon={<Landmark className="text-gray-700 h-8 w-8" />}
                    cardTitle="External Federated Checking"
                    balanceLabel="Total Checking Balance"
                    balanceNumber="$83,758.50"
                    cardIconColor="bg-gray-300/30"
                />
            </SheetTrigger>

            <SheetContent className="w-full lg:w-1/2 overflow-auto" side="right">
                <SheetHeader>
                    <SheetTitle className="font-sohne text-2xl">
                        Federated Checking Account
                    </SheetTitle>
                    <SheetDescription className="font-sohne">
                        Understand the Balance of Your Checking Accounts
                    </SheetDescription>
                </SheetHeader>

                <Table className="">
                    <TableCaption>Your Checking Account Transactions</TableCaption>
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
                                <TableCell className="text-right">{item.amount}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </SheetContent>
        </Sheet>
    );
}
