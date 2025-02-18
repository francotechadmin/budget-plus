import axios from "axios";
import {
  keepPreviousData,
  useQuery,
  UseQueryResult,
} from "@tanstack/react-query";
import { Sections } from "@/models/sections";

const fetchCategories = async (): Promise<Sections> => {
  const response = await axios.get("/categories");
  return response.data;
};

export const useFetchCategories = (): UseQueryResult<Sections, Error> => {
  return useQuery<Sections, Error>({
    queryKey: ["categories"],
    queryFn: fetchCategories,
    placeholderData: keepPreviousData,
  });
};
