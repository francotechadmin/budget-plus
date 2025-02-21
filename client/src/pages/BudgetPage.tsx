import { useState } from "react";
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

const BudgetPage = () => {
  // Initialize with the current month in "YYYY-MM" format.
  const initialYear = new Date().getFullYear().toString();
  const initialMonth = String(new Date().getMonth() + 1).padStart(2, "0");
  const [selectedMonth, setSelectedMonth] = useState(
    `${initialYear}-${initialMonth}`
  );

  // Handler for month changes.
  const handleMonthSelect = (value: string) => {
    setSelectedMonth(value);
  };

  // API hooks.
  const { data: dates = [], isLoading: datesLoading } =
    useFetchTransactionsDatesQuery();
  const { data: categories, isLoading: categoriesLoading } =
    useFetchCategories();
  const {
    data: totals = { income: 0, expenses: 0 },
    isLoading: totalsLoading,
  } = useFetchTransactionsTotalsByMonthQuery(
    selectedMonth.split("-")[0],
    selectedMonth.split("-")[1]
  );
  const { data: groupedData, isLoading: groupedLoading } =
    useFetchGroupedTransactionsQuery(
      selectedMonth.split("-")[0],
      selectedMonth.split("-")[1]
    );

  const deleteTransactionMutation = useDeleteTransactionMutation();
  const handleDeleteTransaction = (id: string) => {
    deleteTransactionMutation.mutate(id);
  };

  // Combine loading states.
  const isLoading =
    datesLoading || categoriesLoading || totalsLoading || groupedLoading;
  if (isLoading) {
    return <div className="text-center p-4">Loading...</div>;
  }

  // Check for missing data.
  if (!dates || !categories || !totals || !groupedData) {
    return <div>Error fetching data.</div>;
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
        {/* Display loading state */}
        {isLoading && <div className="text-gray-500">Loading...</div>}
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
