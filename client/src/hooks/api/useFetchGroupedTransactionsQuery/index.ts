// src/hooks/api/useFetchGroupedTransactionsQuery/index.ts

import { useQuery, UseQueryResult } from "@tanstack/react-query";
import axios from "axios";

interface FetchGroupedTransactionsQueryVariables {
  year: string;
  month: string;
}

interface FetchGroupedTransactionsQueryResponse {
  [key: string]: number;
}

const fetchGroupedTransactions = async ({
  year,
  month,
}: FetchGroupedTransactionsQueryVariables): Promise<FetchGroupedTransactionsQueryResponse> => {
  const response = await axios.get<FetchGroupedTransactionsQueryResponse>(
    `/transactions/grouped/${year}/${month}`
  );
  return response.data;
};

export const useFetchGroupedTransactionsQuery = (
  year: string,
  month: string
): UseQueryResult<FetchGroupedTransactionsQueryResponse> => {
  return useQuery<
    FetchGroupedTransactionsQueryResponse,
    Error,
    FetchGroupedTransactionsQueryResponse
  >({
    queryKey: ["groupedTransactions", year, month],
    queryFn: () => fetchGroupedTransactions({ year, month }),
  });
};
