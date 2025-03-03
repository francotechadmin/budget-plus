import { api } from "@/lib/axios";
import {
  keepPreviousData,
  useQuery,
  UseQueryResult,
} from "@tanstack/react-query";
import { Transaction } from "@/models/transactions";

const fetchTransactions = async (): Promise<Transaction[]> => {
  const response = await api.get("/transactions/");
  return response.data;
};

export const useFetchTransactions = (): UseQueryResult<
  Transaction[],
  Error
> => {
  return useQuery<Transaction[], Error>({
    queryKey: ["transactions"],
    queryFn: fetchTransactions,
    placeholderData: keepPreviousData,
  });
};
