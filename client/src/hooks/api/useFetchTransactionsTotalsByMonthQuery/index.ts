// src/hooks/api/useFetchTransactionsTotalsByMonthQuery/index.ts

import axios from "axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";
// import { Transaction } from "@/models/transactions";
interface FetchTransactionsByMonthQueryVariables {
  year: string;
  month: string;
}

const fetchTransactionsByMonth = async ({
  year,
  month,
}: FetchTransactionsByMonthQueryVariables): Promise<Record<string, number>> => {
  const response = await axios.get<Record<string, number>>(
    `/transactions/expenses/${year}/${month}`
  );
  return response.data;
};

export const useFetchTransactionsTotalsByMonthQuery = (
  year: string,
  month: string
): UseQueryResult<Record<string, number>> => {
  return useQuery<Record<string, number>, Error, Record<string, number>>({
    queryKey: ["transactions", year, month],
    queryFn: () => fetchTransactionsByMonth({ year, month }),
  });
};
