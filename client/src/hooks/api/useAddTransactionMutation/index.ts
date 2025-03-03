// src/hooks/api/useAddTransactionMutation/index.ts

import { api } from "@/lib/axios";
import {
  useMutation,
  UseMutationResult,
  useQueryClient,
} from "@tanstack/react-query";

import { Transaction } from "@/models/transactions";

interface AddTransactionResponse {
  transaction: Transaction;
}

interface AddTransactionMutationVariables {
  date: string;
  description: string;
  amount: number;
  category: string;
}

const addTransactionFn = async ({
  date,
  description,
  amount,
  category,
}: AddTransactionMutationVariables): Promise<AddTransactionResponse> => {
  const response = await api.post<AddTransactionResponse>(`/transactions/`, {
    date: date,
    description: description,
    amount: amount,
    category: category,
  });
  return response.data;
};

export const useAddTransactionMutation = (): UseMutationResult<
  AddTransactionResponse,
  Error,
  AddTransactionMutationVariables
> => {
  const queryClient = useQueryClient();
  return useMutation<
    AddTransactionResponse,
    Error,
    AddTransactionMutationVariables
  >({
    mutationFn: addTransactionFn,
    onSuccess: (data: AddTransactionResponse) => {
      console.log("Transaction added successfully:", data);

      // Invalidate and refetch the transactions query to update the UI
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
    onError: (error) => {
      console.error("Error adding transaction:", error);
    },
  });
};
