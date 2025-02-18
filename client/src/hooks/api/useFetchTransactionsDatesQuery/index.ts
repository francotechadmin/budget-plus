// src/hooks/api/useFetchTransactionsDatesQuery/index.ts

import axios from "axios";
import { useQuery, UseQueryResult } from "@tanstack/react-query";

interface FetchDatesResponse {
  dates: string[];
}

export const useFetchTransactionsDatesQuery =
  (): UseQueryResult<FetchDatesResponse> => {
    const fetchDates = async (): Promise<FetchDatesResponse> => {
      const response = await axios.get<FetchDatesResponse>(
        `${import.meta.env.VITE_API_URL}/transactions/range`
      );
      return response.data;
    };

    return useQuery<FetchDatesResponse, Error>({
      queryKey: ["dates"],
      queryFn: fetchDates,
    });
  };
