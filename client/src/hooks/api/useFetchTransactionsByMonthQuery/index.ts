// src/hooks/api/usefetchTransactionsQuery/index.ts

import axios from "axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { Transaction } from "@/models/transactions";

interface FetchTransactionsByMonthResponse {
  transactions: Transaction[];
}

interface FetchTransactionsByMonthQueryVariables {
  year: string;
  month: string;
}

const fetchTransactionsByMonth = async ({
  year,
  month,
}: FetchTransactionsByMonthQueryVariables): Promise<FetchTransactionsByMonthResponse> => {
  const response = await axios.get<FetchTransactionsByMonthResponse>(
    `/transactions/${year}/${month}`
  );
  return response.data;
};

export const useFetchTransactionsByMonthQuery = (
  year: string,
  month: string
): UseQueryResult<FetchTransactionsByMonthResponse> => {
  return useQuery<
    FetchTransactionsByMonthResponse,
    Error,
    FetchTransactionsByMonthResponse
  >({
    queryKey: ["transactions", year, month],
    queryFn: () => fetchTransactionsByMonth({ year, month }),
  });
};
