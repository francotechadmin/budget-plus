// src/hooks/api/useImportTransactionsMutation/index.ts
import axios from "axios";
import {
  useMutation,
  UseMutationResult,
  useQueryClient,
} from "@tanstack/react-query";

interface ImportTransactionsResponse {
  message: string;
}

const importTransactionsFn = async (
  file: File
): Promise<ImportTransactionsResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post<ImportTransactionsResponse>(
    "/transactions/import",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
};

export const useImportTransactionsMutation = (): UseMutationResult<
  ImportTransactionsResponse,
  Error,
  File
> => {
  const queryClient = useQueryClient();

  return useMutation<ImportTransactionsResponse, Error, File>({
    mutationFn: importTransactionsFn,
    onSuccess: (data) => {
      console.log("Transactions imported successfully:", data);
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
    onError: (error) => {
      console.error("Error importing transactions:", error);
    },
  });
};
