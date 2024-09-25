import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { createColumns } from "../components/columns";
import { DataTable } from "../components/data-table";
import BarChart from "../components/BarChart"; // Import the BarChart component
// import BudgetProgressBar from "../components/BudgetProgressBar";

// Define the shape of the transaction data.
export type Transaction = {
  id: string;
  description: string;
  date: string;
  amount: number;
  category: string;
};

// Fetch transactions and categories from the backend
const fetchTransactions = async (year: string, month: string) => {
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/transactions/${year}/${month}`
  );
  return response.data as Record<string, Record<string, Transaction[]>>;
};

const fetchDates = async () => {
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/transactions/range`
  );
  return response.data;
};

const fetchCategories = async () => {
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/categories`
  );
  return response.data;
};

const fetchTotals = async (year: string, month: string) => {
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/transactions/totals/${year}/${month}`
  );
  return response.data;
};

// delete transaction from backend
const deleteTransaction = async (id: string) => {
  const response = await axios.delete(
    `${import.meta.env.VITE_API_URL}/transactions/${id}`
  );
  return response.data;
};

const BudgetPage = () => {
  const queryClient = useQueryClient();

  // default to current month
  const [yearMonth, setYearMonth] = useState({
    year: `${new Date().getFullYear()}`,
    month: `${new Date().getMonth() + 1}`,
  });

  const setSelectedMonth = (value: string) => {
    const [year, month] = value.split("-");
    setYearMonth({ year: year, month: month });
  };

  const { data: dates, isLoading: datesLoading } = useQuery({
    queryKey: ["dates"],
    queryFn: fetchDates,
  });

  const { data: transactions, isLoading: transactionsLoading } = useQuery({
    queryKey: ["transactions", yearMonth],
    queryFn: () => fetchTransactions(yearMonth.year, yearMonth.month),
  });

  const { data: totals, isLoading: totalsLoading } = useQuery({
    queryKey: ["totals", yearMonth],
    queryFn: () => fetchTotals(yearMonth.year, yearMonth.month),
  });

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });

  const deleteTransactionMutation = useMutation({
    mutationFn: deleteTransaction,
    onSuccess: (data) => {
      console.log("Transaction deleted successfully:", data);
      queryClient.setQueryData(["transactions"], data);
    },
  });

  const deleteTransactionHandler = (id: string) => {
    deleteTransactionMutation.mutate(id);
  };

  const months_text = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const getYearMonth = ({ year, month }: { year: string; month: string }) => {
    return `${year}-${String(month).padStart(2, "0")}`;
  };

  if (
    transactionsLoading ||
    datesLoading ||
    categoriesLoading ||
    totalsLoading
  ) {
    return <div>Loading...</div>;
  }

  if (!transactions || !dates || !categories || !totals) {
    return <div>Error fetching data.</div>;
  }

  return (
    <div className="container mx-auto pl-4 mt-4">
      <div className="flex justify-left items-center gap-4">
        <h1 className="text-2xl font-bold text-left">Budget</h1>
        {/* Month selection dropdown */}
        <div>
          <Select
            onValueChange={setSelectedMonth}
            defaultValue={getYearMonth(yearMonth)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select a month" />
            </SelectTrigger>
            <SelectContent>
              {dates.map((yearMonth: string) => (
                <SelectItem key={yearMonth} value={yearMonth}>
                  {months_text[parseInt(yearMonth.slice(5, 7)) - 1]}{" "}
                  {yearMonth.slice(0, 4)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {/* money in  vs out */}
        <div className="flex gap-4">
          <div>
            <h2 className="text-lg font-semibold">Total Income</h2>
            <p>$ {totals.income.toFixed(2)}</p>
          </div>
          <div>
            <h2 className="text-lg font-semibold">Total Expenses</h2>
            <p>$ {totals.expenses.toFixed(2)}</p>
          </div>
        </div>
      </div>
      {/* Render the BarChart */}
      <BarChart income={totals.income} expenses={totals.expenses} />{" "}
      {/* Loading and Error states */}
      {transactionsLoading && <div>Loading expenses...</div>}
      {/* Render the grouped expenses */}
      {transactions && (
        <div className="mt-4">
          {Object.entries(transactions).map(([section, categories_data]) => (
            <div key={section}>
              <h2 className="text-xl pt-2 font-semibold">
                {section} $
                {Object.values(categories_data)
                  .reduce(
                    (acc, items) =>
                      acc + items.reduce((acc, item) => acc + item.amount, 0),
                    0
                  )
                  .toFixed(2)}
              </h2>
              {Object.entries(categories_data).map(([category, items]) => (
                <div key={category}>
                  <Accordion
                    type="single"
                    collapsible
                    className="pl-4 overflow-hidden"
                  >
                    <AccordionItem value={category}>
                      <AccordionTrigger>
                        <p>
                          {category} ({items.length}) $
                          {items
                            .reduce((acc, item) => acc + item.amount, 0)
                            .toFixed(2)}
                        </p>
                        {/* <BudgetProgressBar totalAmount={100} spentAmount={50} /> */}
                      </AccordionTrigger>
                      <AccordionContent>
                        <DataTable
                          data={items}
                          columns={createColumns(
                            categories,
                            deleteTransactionHandler
                          )}
                          categories={categories}
                        />
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BudgetPage;
