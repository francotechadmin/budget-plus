import { useState, useEffect } from "react";
import PieChart from "../components/PieChart";
import { MonthSelect } from "../components/MonthSelect";
import { useFetchExpensesByMonthQuery } from "@/hooks/api/useFetchExpensesByMonthQuery";
import { useFetchTransactionsDatesQuery } from "@/hooks/api/useFetchTransactionsDatesQuery";

export default function ExpensesPage() {
  // Use a single string "YYYY-MM" for the selected month.
  const [selectedMonth, setSelectedMonth] = useState<string>("");

  // Handler for when the month selection changes.
  const handleMonthSelect = (value: string) => setSelectedMonth(value);

  // Fetch available transaction dates.
  const {
    data: dates = [],
    isLoading: datesLoading,
    error: datesError,
  } = useFetchTransactionsDatesQuery();

  // When dates are available and no month is selected, set selectedMonth to the latest date.
  useEffect(() => {
    if (!selectedMonth && dates.length > 0) {
      const latest = dates.reduce(
        (prev, curr) => (curr > prev ? curr : prev),
        dates[0]
      );
      setSelectedMonth(latest);
    }
  }, [selectedMonth, dates]);

  // Derive year and month from selectedMonth (if available).
  let year = "";
  let month = "";
  if (selectedMonth) {
    [year, month] = selectedMonth.split("-");
  }

  // Fetch expenses for the selected month.
  const {
    data: expenses = {},
    isLoading: expensesLoading,
    isFetching: expensesFetching,
    error: expensesError,
  } = useFetchExpensesByMonthQuery(year, month);

  const isLoading = datesLoading || expensesLoading || expensesFetching;

  if (datesError || expensesError) {
    return <div>Error fetching data.</div>;
  }

  return (
    <div className="container mx-auto mt-4">
      <div className="flex items-center gap-4 pl-4">
        <h1 className="text-2xl font-bold">Charts</h1>
        <MonthSelect
          selectedMonth={selectedMonth}
          onMonthSelect={handleMonthSelect}
          dates={dates}
        />
        {isLoading && <div className="text-gray-500">Loading...</div>}
      </div>
      <PieChart expenses={expenses} />
    </div>
  );
}
