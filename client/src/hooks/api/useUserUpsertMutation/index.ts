import { api } from "@/lib/axios";
import { useMutation, UseMutationResult } from "@tanstack/react-query";

interface UpsertUserResponse {
  id: string;
  email: string;
  name: string;
  // Additional user info
}

const upsertUserFn = async ({
  setShowWelcome,
}: {
  setShowWelcome: (show: boolean) => void;
}): Promise<UpsertUserResponse> => {
  // Extract user information from the token

  const response = await api.post<UpsertUserResponse>("/users/");

  if (response.status !== 200 && response.status !== 201) {
    throw new Error("Failed to upsert user");
  }

  if (response.status === 201) {
    setShowWelcome(true);
  }
  return response.data;
};

export const useUpsertUserMutation = ({
  setShowWelcome,
}: {
  setShowWelcome: (show: boolean) => void;
}): UseMutationResult<UpsertUserResponse, Error, void> => {
  return useMutation<UpsertUserResponse, Error, void>({
    mutationFn: () => upsertUserFn({ setShowWelcome }),
    onSuccess: (data) => {
      console.log("User upserted successfully:", data);
    },
    onError: (error) => {
      console.error("Error upserting user:", error);
    },
  });
};
