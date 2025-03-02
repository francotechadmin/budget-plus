// src/pages/TransactionsPage.tsx

import { createColumns } from "../components/columns";
import { DataTable } from "../components/data-table";
// import { Button } from "../components/ui/button";

// Models
import { Transaction } from "@/models/transactions";

// Hooks
import { useFetchTransactions } from "@/hooks/api/usefetchTransactionsQuery";
import { useFetchCategories } from "@/hooks/api/useFetchCategoriesQuery";
import { useDeleteTransactionMutation } from "@/hooks/api/useDeleteTransactionMutation";

// New modal components
import { AddTransactionModal } from "../components/AddTransactionModal";
import { ImportTransactionsModal } from "../components/ImportTransactionsModal";
import { Spinner } from "@/components/ui/loader";
import { Skeleton } from "@/components/ui/skeleton";

export default function TransactionsPage() {
  const {
    data: transactions = [],
    isLoading: transactionsLoading,
    isFetching: transactionsFetching,
    isError: transError,
  } = useFetchTransactions();

  const {
    data: sections = {},
    isLoading: categoriesLoading,
    isError: catError,
  } = useFetchCategories();

  const deleteTransactionMutation = useDeleteTransactionMutation();

  const deleteTransactionHandler = (id: string) => {
    deleteTransactionMutation.mutate(id);
  };

  const columns = createColumns(sections, deleteTransactionHandler);

  if (transError || catError) {
    return <div>Error fetching data.</div>;
  }

  if (transactionsLoading || categoriesLoading) {
    return (
      <div className="container mx-auto pl-4 mt-4">
        <h1 className="text-2xl font-bold">Transactions</h1>
        <Skeleton className="h-8 w-1/2 mt-4" />
        <div className="mt-4">
          <Skeleton className="h-8 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto pl-4 mt-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold flex items-center">
          Transactions
          {transactionsFetching && <Spinner size="small" className="ml-2" />}
        </h1>
        <div className="flex space-x-2">
          <AddTransactionModal sections={sections} />
          <ImportTransactionsModal />
        </div>
      </div>
      <DataTable<Transaction, (typeof columns)[number]>
        columns={columns}
        data={transactions}
        sections={sections}
      />
    </div>
  );
}
