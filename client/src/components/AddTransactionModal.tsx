// src/components/AddTransactionModal.tsx
import { useState, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SquarePlus } from "lucide-react";
import { Sections } from "@/models/sections";
import { CategorySelect } from "./CategorySelect";
import { useAddTransactionMutation } from "@/hooks/api/useAddTransactionMutation";
import { Spinner } from "./ui/loader";
import { DatePicker } from "./DatePicker";

interface AddTransactionModalProps {
  sections: Sections; // Add categories as a prop
}

export function AddTransactionModal({ sections }: AddTransactionModalProps) {
  const [open, setOpen] = useState(false);
  const [transactionType, setTransactionType] = useState<"expense" | "income">(
    "expense"
  );

  const [formData, setFormData] = useState({
    date: new Date().toISOString().split("T")[0],
    description: "",
    amount: 0,
    category: "",
  });

  const {
    mutate: addTransaction,
    isPending,
    error,
  } = useAddTransactionMutation();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Ensure that expenses are negative and incomes are positive.
    const numericAmount = Math.abs(Number(formData.amount));
    const finalAmount =
      transactionType === "expense" ? -numericAmount : numericAmount;

    addTransaction(
      { ...formData, amount: finalAmount },
      {
        onSuccess: () => {
          resetForm();
          setOpen(false);
        },
      }
    );
  };

  const handleOpenChange = (open: boolean) => {
    setOpen(open);
    if (!open) {
      resetForm();
      setTransactionType("expense");
    }
  };

  const resetForm = useCallback(() => {
    // Reset form and close modal
    setFormData({
      date: new Date().toISOString().split("T")[0],
      description: "",
      amount: 0,
      category: "",
    });
  }, []);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="default">
          <span className="hidden lg:block">Add Transaction</span>{" "}
          <SquarePlus className="lg:ml-1 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-[90vw] lg:max-w-lg rounded">
        <DialogHeader>
          <DialogTitle>Add Transaction</DialogTitle>
          <DialogDescription>
            Fill in the details for the new transaction.
          </DialogDescription>
          {error && (
            <div className="text-red-500 text-sm">
              There was an error adding your transaction.
            </div>
          )}
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              className="block text-sm font-medium text-gray-700"
              aria-label="Date"
            >
              Date
            </label>
            <DatePicker
              onDateChange={() =>
                setFormData({
                  ...formData,
                  date: new Date().toISOString().split("T")[0],
                })
              }
            />
          </div>
          <div>
            <label
              className="block text-sm font-medium text-gray-700"
              aria-label="Description"
            >
              Description
            </label>
            <Input
              type="text"
              name="description"
              value={formData.description}
              onChange={handleChange}
              required
            />
          </div>
          {/* Transaction type toggle */}
          <div>
            <label
              className="block text-sm font-medium text-gray-700"
              aria-label="Transaction Type"
            >
              Transaction Type
            </label>
            <div className="flex space-x-2 mt-1">
              <Button
                type="button"
                variant={
                  transactionType === "expense" ? "destructive" : "outline"
                }
                onClick={() => setTransactionType("expense")}
              >
                Expense
              </Button>
              <Button
                type="button"
                variant={transactionType === "income" ? "default" : "outline"}
                onClick={() => setTransactionType("income")}
              >
                Income
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Expenses will be recorded as negative values.
            </p>
          </div>
          <div>
            <label
              className="block text-sm font-medium text-gray-700"
              aria-label="Amount"
            >
              Amount
            </label>
            <Input
              type="number"
              step="0.01"
              name="amount"
              // Conditionally style amount: red for expense, green for income
              className={
                transactionType === "expense"
                  ? "text-red-500"
                  : "text-green-500"
              }
              value={formData.amount === 0 ? "" : formData.amount}
              onChange={handleChange}
              required
            />
          </div>
          <div>
            <label
              className="block text-sm font-medium text-gray-700"
              aria-label="Category"
            >
              Category
            </label>
            <CategorySelect
              value={formData.category}
              onChange={(value) =>
                setFormData({ ...formData, category: value })
              }
              sections={sections}
            />
          </div>
          <div className="flex justify-end space-x-2">
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" disabled={isPending}>
              {isPending ? <Spinner size="small" /> : "Add Transaction"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
