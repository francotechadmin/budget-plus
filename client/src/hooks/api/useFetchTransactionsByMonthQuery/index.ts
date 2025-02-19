// src/hooks/api/usefetchTransactionsQuery/index.ts

import axios from "axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { Transaction } from "@/models/transactions";
interface FetchTransactionsByMonthQueryVariables {
  year: string;
  month: string;
}

const fetchTransactionsByMonth = async ({
  year,
  month,
}: FetchTransactionsByMonthQueryVariables): Promise<Transaction[]> => {
  const response = await axios.get<Transaction[]>(
    `/transactions/${year}/${month}`
  );
  return response.data;
};

export const useFetchTransactionsByMonthQuery = (
  year: string,
  month: string
): UseQueryResult<Transaction[]> => {
  return useQuery<Transaction[], Error, Transaction[]>({
    queryKey: ["transactions", year, month],
    queryFn: () => fetchTransactionsByMonth({ year, month }),
  });
};
