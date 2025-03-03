import { api } from "@/lib/axios";
import { useMutation, UseMutationResult } from "@tanstack/react-query";

interface UpsertUserResponse {
  id: string;
  email: string;
  name: string;
  // Additional user info
}

const upsertUserFn = async (): Promise<UpsertUserResponse> => {
  // Extract user information from the token

  const response = await api.post<UpsertUserResponse>("/users/");
  return response.data;
};

export const useUpsertUserMutation = (): UseMutationResult<
  UpsertUserResponse,
  Error,
  void
> => {
  return useMutation<UpsertUserResponse, Error, void>({
    mutationFn: upsertUserFn,
    onSuccess: (data) => {
      console.log("User upserted successfully:", data);
    },
    onError: (error) => {
      console.error("Error upserting user:", error);
    },
  });
};
