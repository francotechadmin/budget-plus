import PieChart from "../components/PieChart";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useState } from "react";

import axios from "axios";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Fetch transactions and categories from the backend
const fetchTransactions = async (year: string, month: string) => {
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/transactions/expenses/${year}/${month}`
  );
  return response.data;
};

const fetchCategories = async () => {
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/categories`
  );
  return response.data;
};

const fetchDates = async () => {
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/transactions/range`
  );
  return response.data;
};

export default function ExpensesPage() {
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

  const getYearMonth = ({ year, month }: { year: string; month: string }) => {
    return `${year}-${String(month).padStart(2, "0")}`;
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
  const { data: transactions, isLoading: transactionsLoading } = useQuery({
    queryKey: ["transaction_totals", yearMonth],
    queryFn: () => fetchTransactions(yearMonth.year, yearMonth.month),
    placeholderData: keepPreviousData,
  });

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });

  if (transactionsLoading || categoriesLoading) {
    return <div>Loading...</div>;
  }

  if (!transactions || !categories) {
    return <div>Error fetching data.</div>;
  }

  if (datesLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto pl-4 mt-4">
      <div className="flex justify-left items-center gap-4">
        <h1 className="text-2xl font-bold text-left">Charts</h1>
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
      </div>
      <PieChart transactions={transactions} />
    </div>
  );
}
