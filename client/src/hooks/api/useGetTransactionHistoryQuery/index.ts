// src/hooks/api/useGetTransactionHistoryQuery/index.ts

import axios from "axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";

interface FetchTransactionHistoryResponse {
  [key: string]: {
    income: number;
    expenses: number;
  };
}

export const fetchTransactionHistory =
  async (): Promise<FetchTransactionHistoryResponse> => {
    const response = await axios.get("/transactions/history");
    return response.data;
  };

export const useGetTransactionHistoryQuery =
  (): UseQueryResult<FetchTransactionHistoryResponse> => {
    return useQuery<FetchTransactionHistoryResponse>({
      queryKey: ["transaction_history"],
      queryFn: fetchTransactionHistory,
    });
  };
