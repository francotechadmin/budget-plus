// src/hooks/api/useFetchGroupedTransactionsQuery/index.ts

import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { GroupedTransaction } from "@/models/groupedTransactions";
import axios from "axios";

interface FetchGroupedTransactionsQueryVariables {
  year: string;
  month: string;
}

const fetchGroupedTransactions = async ({
  year,
  month,
}: FetchGroupedTransactionsQueryVariables): Promise<GroupedTransaction[]> => {
  const response = await axios.get<GroupedTransaction[]>(
    `/transactions/grouped/${year}/${month}`
  );
  return response.data;
};

export const useFetchGroupedTransactionsQuery = (
  year: string,
  month: string
): UseQueryResult<GroupedTransaction[]> => {
  return useQuery<GroupedTransaction[], Error, GroupedTransaction[]>({
    queryKey: ["groupedTransactions", year, month],
    queryFn: () => fetchGroupedTransactions({ year, month }),
    placeholderData: (prev) => prev,
    staleTime: 1000 * 60 * 60,
  });
};
