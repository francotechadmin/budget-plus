import { useState } from "react";

import PieChart from "../components/PieChart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useFetchTransactionsTotalsByMonthQuery } from "@/hooks/api/useFetchTransactionsTotalsByMonthQuery";
import { useFetchTransactionsDatesQuery } from "@/hooks/api/useFetchTransactionsDatesQuery";

export default function ExpensesPage() {
  // State to hold the selected year and month.
  const [yearMonth, setYearMonth] = useState({
    year: String(new Date().getFullYear()),
    month: String(new Date().getMonth() + 1),
  });

  // Utility to format a year/month object into a string like "YYYY-MM".
  const formatYearMonth = ({ year, month }: { year: string; month: string }) =>
    `${year}-${String(month).padStart(2, "0")}`;

  // Handler for when the month selection changes.
  const handleMonthSelect = (value: string) => {
    const [year, month] = value.split("-");
    setYearMonth({ year, month });
  };

  // Fetch available transaction dates.
  const {
    data: dates = { dates: [] },
    isLoading: datesLoading,
    error: datesError,
  } = useFetchTransactionsDatesQuery();

  // Fetch transaction totals for the selected month.
  const {
    data: totals = { totals: {} },
    isLoading: transactionsLoading,
    error: transactionsError,
  } = useFetchTransactionsTotalsByMonthQuery(yearMonth.year, yearMonth.month);

  // Combine all loading states.
  const isLoading = datesLoading || transactionsLoading;

  // Check for Error data.
  if (datesError || transactionsError) {
    return <div>Error fetching data.</div>;
  }

  // Text labels for the months.
  const monthLabels = [
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

  return (
    <div className="container mx-auto mt-4">
      <div className="flex justify-start items-center gap-4 pl-4">
        <h1 className="text-2xl font-bold text-left">Charts</h1>
        {/* Month selection dropdown */}
        <Select
          onValueChange={handleMonthSelect}
          defaultValue={formatYearMonth(yearMonth)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select a month" />
          </SelectTrigger>
          <SelectContent>
            {dates.dates.map((yearMonthString: string) => {
              const monthIndex = parseInt(yearMonthString.slice(5, 7), 10) - 1;
              const year = yearMonthString.slice(0, 4);
              return (
                <SelectItem key={yearMonthString} value={yearMonthString}>
                  {monthLabels[monthIndex]} {year}
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
        {/* Loading spinner */}
        {isLoading && <div className="text-gray-500">Loading...</div>}
      </div>
      {/* Render the pie chart with the fetched totals */}
      <PieChart totals={totals.totals} />
    </div>
  );
}
