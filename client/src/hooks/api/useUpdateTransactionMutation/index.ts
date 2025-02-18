// src/hooks/api/useUpdateTransactionMutation/index.ts
import axios from "axios";
import { useMutation, UseMutationResult } from "@tanstack/react-query";
import { Transaction } from "@/models/transactions";

interface UpdateTransactionResponse {
  message: string;
  transaction: Transaction;
}

interface UpdateTransactionMutationVariables {
  id: string;
  category: string;
}

const updateTransactionFn = async ({
  id,
  category,
}: UpdateTransactionMutationVariables): Promise<UpdateTransactionResponse> => {
  const response = await axios.post<UpdateTransactionResponse>(
    `transactions/update`,
    {
      transaction_id: id,
      category: category,
    }
  );
  return response.data;
};

export const useUpdateTransactionMutation = (): UseMutationResult<
  UpdateTransactionResponse,
  Error,
  UpdateTransactionMutationVariables
> => {
  return useMutation<
    UpdateTransactionResponse,
    Error,
    UpdateTransactionMutationVariables
  >({
    mutationFn: updateTransactionFn,
    onSuccess: (data) => {
      console.log("Transaction updated successfully:", data);
    },
    onError: (error) => {
      console.error("Error updating transaction:", error);
    },
  });
};
