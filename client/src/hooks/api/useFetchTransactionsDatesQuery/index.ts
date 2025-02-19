// src/hooks/api/useFetchTransactionsDatesQuery/index.ts

import axios from "axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";

export const useFetchTransactionsDatesQuery = (): UseQueryResult<string[]> => {
  const fetchDates = async (): Promise<string[]> => {
    const response = await axios.get<string[]>(
      `${import.meta.env.VITE_API_URL}/transactions/range`
    );
    return response.data;
  };

  return useQuery<string[], Error>({
    queryKey: ["dates"],
    queryFn: fetchDates,
    placeholderData: (prev) => prev,
    staleTime: 1000 * 60 * 60,
  });
};
