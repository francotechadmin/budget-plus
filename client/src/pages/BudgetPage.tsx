import { useState, useEffect } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { createColumns } from "../components/columns";
import { DataTable } from "../components/data-table";
import { MonthSelect } from "../components/MonthSelect";
import BarChart from "../components/BarChart";
import { useFetchTransactionsDatesQuery } from "@/hooks/api/useFetchTransactionsDatesQuery";
import { useFetchTransactionsTotalsByMonthQuery } from "@/hooks/api/useFetchTransactionsTotalsByMonthQuery";
import { useFetchCategories } from "@/hooks/api/useFetchCategoriesQuery";
import { useDeleteTransactionMutation } from "@/hooks/api/useDeleteTransactionMutation";
import { useFetchGroupedTransactionsQuery } from "@/hooks/api/useFetchGroupedTransactionsQuery";
import { Skeleton } from "@/components/ui/skeleton";

const BudgetPage = () => {
  // Use a single string "YYYY-MM" for the selected month.
  const [selectedMonth, setSelectedMonth] = useState<string>("");

  // Handler for month changes.
  const handleMonthSelect = (value: string) => {
    setSelectedMonth(value);
  };

  // Fetch available transaction dates.
  const { data: dates = [], isLoading: datesLoading } =
    useFetchTransactionsDatesQuery();

  // Auto-select the latest available date once dates are loaded.
  useEffect(() => {
    if (!selectedMonth && dates.length > 0) {
      const latest = dates.reduce(
        (prev, curr) => (curr > prev ? curr : prev),
        dates[0]
      );
      setSelectedMonth(latest);
    }
  }, [selectedMonth, dates]);

  // Derive year and month from selectedMonth if available.
  const year = selectedMonth ? selectedMonth.split("-")[0] : "";
  const month = selectedMonth ? selectedMonth.split("-")[1] : "";

  // API hooks.
  const { data: categories = {}, isLoading: categoriesLoading } =
    useFetchCategories();
  const {
    data: totals = { income: 0, expenses: 0 },
    isLoading: totalsLoading,
  } = useFetchTransactionsTotalsByMonthQuery(year, month);
  const { data: groupedData = [], isLoading: groupedLoading } =
    useFetchGroupedTransactionsQuery(year, month);

  const deleteTransactionMutation = useDeleteTransactionMutation();
  const handleDeleteTransaction = (id: string) => {
    deleteTransactionMutation.mutate(id);
  };

  // Combine loading states.
  const isLoading =
    datesLoading || categoriesLoading || totalsLoading || groupedLoading;

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 mt-4">
        <h1 className="text-2xl font-bold py-2">Budget</h1>
        <Skeleton className="h-28 w-full mt-4" />
        <div className="mt-8">
          <Skeleton className="h-12 w-full mb-2" />
          <Skeleton className="h-6 w-full mb-2" />
          <Skeleton className="h-6 w-full mb-2" />
          <Skeleton className="h-6 w-full mb-2" />
        </div>
        <div className="mt-4">
          <Skeleton className="h-12 w-full mb-2" />
          <Skeleton className="h-6 w-full mb-2" />
          <Skeleton className="h-6 w-full mb-2" />
          <Skeleton className="h-6 w-full mb-2" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto pl-4 mt-4">
      <div className="flex items-center gap-4 flex-col md:flex-row">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Budget</h1>
          {/* Month selection dropdown */}
          <MonthSelect
            selectedMonth={selectedMonth}
            onMonthSelect={handleMonthSelect}
            dates={dates}
          />
        </div>
        {/* Display total income vs. expenses */}
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
      <BarChart income={totals.income} expenses={totals.expenses} />
      {/* Render grouped transactions */}
      {groupedData.map((section) => (
        <div key={section.section} className="mt-4">
          <h2 className="text-xl pt-2 font-semibold">
            {section.section} ${section.total.toFixed(2)}
          </h2>
          {section.categories.map((category) => (
            <Accordion
              key={category.name}
              type="single"
              collapsible
              className="pl-4 overflow-hidden"
            >
              <AccordionItem value={category.name}>
                <AccordionTrigger>
                  <p>
                    {category.name} ({category.transactions.length}) $
                    {category.total.toFixed(2)}
                  </p>
                </AccordionTrigger>
                <AccordionContent>
                  <DataTable
                    columns={createColumns(categories, handleDeleteTransaction)}
                    data={category.transactions}
                    sections={categories}
                  />
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          ))}
        </div>
      ))}
    </div>
  );
};

export default BudgetPage;
