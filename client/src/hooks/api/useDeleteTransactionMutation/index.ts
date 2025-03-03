// src/hooks/api/useDeleteTransactionMutation/index.ts
import { api } from "@/lib/axios";
import {
  useMutation,
  UseMutationResult,
  useQueryClient,
} from "@tanstack/react-query";
import { Transaction } from "@/models/transactions";

interface DeleteProjectResponse {
  message: string;
}

const deleteProjectFn = async (
  transactionId: string
): Promise<DeleteProjectResponse> => {
  const response = await api.delete<DeleteProjectResponse>(
    `/transactions/${transactionId}`
  );
  return response.data;
};

export const useDeleteTransactionMutation = (): UseMutationResult<
  DeleteProjectResponse,
  Error,
  string
> => {
  const queryClient = useQueryClient();
  return useMutation<DeleteProjectResponse, Error, string>({
    mutationFn: deleteProjectFn,
    onMutate: async (transactionId) => {
      const previousData = queryClient.getQueryData(["transactions"]);

      // Optimistically update the cache
      if (previousData) {
        queryClient.setQueryData(["transactions"], (oldData: Transaction[]) =>
          oldData.filter(
            (transaction: Transaction) => transaction.id !== transactionId
          )
        );
      }

      return { previousData };
    },
    onSuccess: (data) => {
      console.log("Project deleted successfully:", data);

      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ["groupedTransactions"] });
    },
    onError: (error) => {
      console.error("Error deleting project:", error);
    },
  });
};
