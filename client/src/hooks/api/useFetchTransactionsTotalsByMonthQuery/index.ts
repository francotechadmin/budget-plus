// src/hooks/api/useFetchTransactionsTotalsByMonthQuery/index.ts

import { api } from "@/lib/axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";
// import { Transaction } from "@/models/transactions";
interface FetchTransactionsByMonthQueryVariables {
  year: string;
  month: string;
}

interface FetchTransactionsByMonthResponse {
  income: number;
  expenses: number;
}

const fetchTotalsByMonth = async ({
  year,
  month,
}: FetchTransactionsByMonthQueryVariables): Promise<FetchTransactionsByMonthResponse> => {
  const response = await api.get<FetchTransactionsByMonthResponse>(
    `/transactions/totals/${year}/${month}`
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
    queryKey: ["totals", year, month],
    queryFn: () => fetchTotalsByMonth({ year, month }),
    placeholderData: (prev) => prev,
    enabled: !!year && !!month,
  });
};
