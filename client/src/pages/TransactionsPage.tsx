// src/pages/TransactionsPage.tsx

//Components
import { createColumns } from "../components/columns";
import { DataTable } from "../components/data-table";
import { Button } from "../components/ui/button";

// Models
import { Transaction } from "@/models/transactions";

// Hooks
import { useFetchTransactions } from "@/hooks/api/usefetchTransactionsQuery";
import { useFetchCategories } from "@/hooks/api/useFetchCategoriesQuery";
import { useDeleteTransactionMutation } from "@/hooks/api/useDeleteTransactionMutation";
import { useImportTransactionsMutation } from "@/hooks/api/useImportTransactionsMutation";

export default function TransactionsPage() {
  const {
    data: transactions = [],
    isLoading: transactionsLoading,
    isError: transError,
  } = useFetchTransactions();

  const {
    data: sections = {},
    isLoading: categoriesLoading,
    isError: catError,
  } = useFetchCategories();

  const { mutate: importTransactionsMutation, isPending: isImporting } =
    useImportTransactionsMutation();

  const deleteTransactionMutation = useDeleteTransactionMutation();

  if (transactionsLoading || categoriesLoading) {
    return <div>Loading...</div>;
  }

  if (transError || catError) {
    return <div>Error fetching data.</div>;
  } // Show error message if there is an error fetching data

  const addTransactionsHandler = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".csv, .xlsx"; // accept csv, xlsx files
    input.multiple = false;
    input.onchange = (e) => {
      const event = e.target as HTMLInputElement;
      if (!event.files) {
        return;
      }
      const file = event.files[0];
      if (!file) {
        return;
      }
      // Call the importTransactionsMutation with the selected file
      importTransactionsMutation(file);
      event.value = ""; // Clear the input value after file selection
    };
    input.click();
  };

  const deleteTransactionHandler = (id: string) => {
    deleteTransactionMutation.mutate(id);
  };

  const columns = createColumns(sections, deleteTransactionHandler); // Create columns dynamically based on the fetched categories

  return (
    <div className="container mx-auto pl-4 mt-4">
      <div className="flex justify-between items-center">
        <div className="flex items-center">
          <h1 className="text-2xl font-bold text-left">Transactions</h1>
          {/* loading text */}
          {transactionsLoading && (
            <span className="text-sm text-gray-500 ml-2">Loading...</span>
          )}
          {isImporting && (
            <span className="text-sm text-gray-500 ml-2">Importing...</span>
          )}
        </div>
        <Button
          variant="outline"
          className="h-8"
          // open file picker to upload xlsx file
          onClick={addTransactionsHandler}
        >
          Add Transactions
        </Button>
      </div>
      <DataTable<Transaction, (typeof columns)[number]>
        columns={columns}
        data={transactions}
        sections={sections}
      />
    </div>
  );
}
