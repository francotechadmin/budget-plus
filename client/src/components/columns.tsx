"use client";

import { ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { CategoryDropdown } from "./CategoryDropdown";
import { DataTableColumnHeader } from "./DataTableColumnHeader";
import { Transaction } from "@/models/transactions";
import { Sections } from "@/models/sections";

// Define the columns for the transaction table, passing sections from props
export const createColumns = (
  sections: Sections,
  deleteMutationHandler: (id: string) => void
): ColumnDef<Transaction>[] => [
  {
    accessorKey: "description",
    header: "Description",
  },
  {
    accessorKey: "date",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Date" />
    ),
  },
  {
    accessorKey: "amount",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Amount" />
    ),

    cell: ({ row }) => {
      const amount = parseFloat(row.getValue("amount"));
      const formatted = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(amount);
      return <div className="text-left font-medium">{formatted}</div>;
    },
  },
  {
    accessorKey: "category",
    header: "Category",
    cell: ({ row }) => {
      const transaction = row.original;
      return (
        <CategoryDropdown
          transactionId={transaction.id}
          initialCategory={transaction.category}
          sections={sections}
        />
      );
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const transaction = row.original;

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem
              onClick={() => navigator.clipboard.writeText(transaction.id)}
            >
              Copy Transaction ID
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Edit Transaction</DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => deleteMutationHandler(transaction.id)}
            >
              Delete Transaction
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
