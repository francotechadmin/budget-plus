// src/hooks/api/useFetchTransactionsTotalsByMonthQuery/index.ts

import axios from "axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";
// import { Transaction } from "@/models/transactions";

interface FetchTransactionsByMonthResponse {
  totals: Record<string, number>;
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
    `/transactions/expenses/${year}/${month}`
  );
  return response.data;
};

export const useFetchTransactionsTotalsByMonthQuery = (
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
