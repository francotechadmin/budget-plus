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
import { months_text } from "@/lib/constants";

export default function ExpensesPage() {
  // Use a single string "YYYY-MM" for the selected month.
  const [selectedMonth, setSelectedMonth] = useState(
    `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, "0")}`
  );

  // Handler for when the month selection changes.
  const handleMonthSelect = (value: string) => setSelectedMonth(value);

  // Extract year and month for the query hook.
  const [year, month] = selectedMonth.split("-");

  // Fetch available transaction dates.
  const {
    data: dates = [],
    isLoading: datesLoading,
    error: datesError,
  } = useFetchTransactionsDatesQuery();

  // Fetch totals for the selected month.
  const {
    data: totals = {},
    isLoading: totalsLoading,
    isFetching: totalsFetching,
    error: totalsError,
  } = useFetchTransactionsTotalsByMonthQuery(year, month);

  const isLoading = datesLoading || totalsLoading || totalsFetching;

  if (datesError || totalsError) {
    return <div>Error fetching data.</div>;
  }

  return (
    <div className="container mx-auto mt-4">
      <div className="flex items-center gap-4 pl-4">
        <h1 className="text-2xl font-bold">Charts</h1>
        <Select onValueChange={handleMonthSelect} defaultValue={selectedMonth}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select a month" />
          </SelectTrigger>
          <SelectContent>
            {dates.map((dateString: string) => {
              const [yr, mon] = dateString.split("-");
              const monthIndex = parseInt(mon, 10) - 1;
              return (
                <SelectItem key={dateString} value={dateString}>
                  {months_text[monthIndex]} {yr}
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
        {isLoading && <div className="text-gray-500">Loading...</div>}
      </div>
      <PieChart totals={totals} />
    </div>
  );
}
