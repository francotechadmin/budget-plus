import { api } from "@/lib/axios";
import {
  keepPreviousData,
  useQuery,
  UseQueryResult,
} from "@tanstack/react-query";

const pingAPI = async () => {
  const response = await api.get("/ping/");
  return response.data;
};

export const usePingQuery = (): UseQueryResult<Error> => {
  return useQuery<Error>({
    queryKey: ["ping"],
    queryFn: pingAPI,
    placeholderData: keepPreviousData,
  });
};
