// src/hooks/api/useDeleteTransactionMutation/index.ts
import axios from "axios";
import { useMutation, UseMutationResult } from "@tanstack/react-query";

interface DeleteProjectResponse {
  message: string;
}

const deleteProjectFn = async (
  transactionId: string
): Promise<DeleteProjectResponse> => {
  const response = await axios.delete<DeleteProjectResponse>(
    `/transactions/${transactionId}`
  );
  return response.data;
};

export const useDeleteTransactionMutation = (): UseMutationResult<
  DeleteProjectResponse,
  Error,
  string
> => {
  return useMutation<DeleteProjectResponse, Error, string>({
    mutationFn: deleteProjectFn,
    onSuccess: (data) => {
      console.log("Project deleted successfully:", data);
    },
    onError: (error) => {
      console.error("Error deleting project:", error);
    },
  });
};
