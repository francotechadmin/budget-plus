// src/hooks/api/useGetTransactionHistoryQuery/index.ts

import { api } from "@/lib/axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";

interface FetchTransactionHistoryResponse {
  [key: string]: {
    income: number;
    expenses: number;
  };
}

export const fetchTransactionHistory =
  async (): Promise<FetchTransactionHistoryResponse> => {
    const response = await api.get("/transactions/history");
    return response.data;
  };

export const useGetTransactionHistoryQuery =
  (): UseQueryResult<FetchTransactionHistoryResponse> => {
    return useQuery<FetchTransactionHistoryResponse>({
      queryKey: ["transaction_history"],
      queryFn: fetchTransactionHistory,
    });
  };
