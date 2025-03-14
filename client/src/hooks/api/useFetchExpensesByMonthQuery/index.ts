// src/hooks/api/useFetchExpensesByMonthQuery/index.ts

import { api } from "@/lib/axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { Transaction } from "@/models/transactions";
interface FetchTransactionsByMonthQueryVariables {
  year: string;
  month: string;
}

const fetchExpensesByMonth = async ({
  year,
  month,
}: FetchTransactionsByMonthQueryVariables): Promise<Transaction[]> => {
  const response = await api.get<Transaction[]>(
    `/transactions/expenses/${year}/${month}`
  );
  return response.data;
};

export const useFetchExpensesByMonthQuery = (
  year: string,
  month: string
): UseQueryResult<Transaction[]> => {
  return useQuery<Transaction[], Error, Transaction[]>({
    queryKey: ["expenses", year, month],
    queryFn: () => fetchExpensesByMonth({ year, month }),
    placeholderData: (prev) => prev,
    enabled: !!year && !!month,
  });
};
