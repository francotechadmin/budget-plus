import { createColumns } from "../components/columns";
import { DataTable } from "../components/data-table";
import {
  useQuery,
  // keepPreviousData,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import axios from "axios";
import { Button } from "../components/ui/button";
import { useFetchTransactions } from "@/hooks/api/usefetchTransactions";

const fetchCategories = async () => {
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/categories`
  );
  return response.data;
};

// send xslx file to backend
const addTransations = async (data: FormData) => {
  const response = await axios.post(
    `${import.meta.env.VITE_API_URL}/transactions/`,
    data
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

export default function TransactionsPage() {
  const queryClient = useQueryClient();
  const {
    data: transactions,
    isLoading: transactionsLoading,
    isError: transError,
  } = useFetchTransactions();

  // const {
  //   data: transactions,
  //   isLoading: transactionsLoading,
  //   isError: transError,
  // } = useQuery({
  //   queryKey: ["transactions"],
  //   queryFn: fetchTransactions,
  //   placeholderData: keepPreviousData,
  // });

  const {
    data: categories,
    isLoading: categoriesLoading,
    isError: catError,
  } = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });

  const addTransactionsMutation = useMutation({
    mutationFn: addTransations,
    onSuccess: (data) => {
      console.log("Transactions added successfully:", data);
      queryClient.setQueryData(["transactions"], data);
    },
  });

  const deleteTransactionMutation = useMutation({
    mutationFn: deleteTransaction,
    onSuccess: (data) => {
      console.log("Transaction deleted successfully:", data);
      queryClient.setQueryData(["transactions"], data);
    },
  });

  if (transactionsLoading || categoriesLoading) {
    return <div>Loading...</div>;
  }

  if (transError || catError) {
    console.log(transactions, categories, transError, catError);
    return <div>Error fetching data.</div>;
  } // Show error message if there is an error fetching data

  const deleteTransactionHandler = (id: string) => {
    deleteTransactionMutation.mutate(id);
  };

  const addTransactionsHandler = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".csv";
    input.multiple = true;
    input.onchange = (e) => {
      const event = e.target as HTMLInputElement;
      if (!event.files) {
        return;
      }
      const files = event.files;
      const form = new FormData();
      for (let i = 0; i < files.length; i++) {
        form.append("files", files[i]);
      }
      if (form) {
        addTransactionsMutation.mutate(form);
      }
    };
    input.click();
  };

  const columns = createColumns(categories, deleteTransactionHandler); // Create columns dynamically based on the fetched categories

  return (
    <div className="container mx-auto pl-4 mt-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-left">Transactions</h1>
        <Button
          variant="outline"
          className="h-8"
          // open file picker to upload xlsx file
          onClick={addTransactionsHandler}
        >
          Add Transactions
        </Button>
      </div>
      <DataTable
        columns={columns}
        data={transactions ?? []}
        categories={categories}
      />
    </div>
  );
}
