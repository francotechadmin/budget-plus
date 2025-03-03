// src/hooks/api/useUpdateTransactionMutation/index.ts
import { api } from "@/lib/axios";
import {
  useMutation,
  UseMutationResult,
  useQueryClient,
} from "@tanstack/react-query";
import { Transaction } from "@/models/transactions";
interface UpdateTransactionMutationVariables {
  id: string;
  category: string;
}

const updateTransactionFn = async ({
  id,
  category,
}: UpdateTransactionMutationVariables): Promise<Transaction> => {
  const response = await api.post<Transaction>(`transactions/update`, {
    transaction_id: id,
    category: category,
  });
  return response.data;
};

export const useUpdateTransactionMutation = (): UseMutationResult<
  Transaction,
  Error,
  UpdateTransactionMutationVariables
> => {
  const queryClient = useQueryClient();
  return useMutation<Transaction, Error, UpdateTransactionMutationVariables>({
    mutationFn: updateTransactionFn,
    onSuccess: (data: Transaction) => {
      console.log("Transaction updated successfully:", data);
      // Optionally invalidate queries or update local state here
      const dateString = String(data.date);
      const year = dateString.split("-")[0];
      const month = dateString.split("-")[1];
      // Invalidate queries related to transactions
      queryClient.invalidateQueries({
        queryKey: ["groupedTransactions", year, month],
      });
    },
    onError: (error) => {
      console.error("Error updating transaction:", error);
    },
  });
};
