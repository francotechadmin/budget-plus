import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Define a prop type for the component
interface CategoryDropdownProps {
  transactionId: string;
  initialCategory: string;
  categories: Record<string, string[]>;
}

// Update the category of a transaction in the backend
const updateCategory = async ({
  id,
  category,
}: {
  id: string;
  category: string;
}) => {
  const response = await axios.post(
    `http://localhost:8000/update-transaction`,
    {
      transaction_id: id,
      category: category,
    }
  );
  return response.data;
};

export const CategoryDropdown: React.FC<CategoryDropdownProps> = ({
  transactionId,
  initialCategory,
  categories,
}) => {
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const queryClient = useQueryClient();

  const updateCategoryMutation = useMutation({
    mutationFn: updateCategory,
    onSuccess: (data) => {
      console.log("Category updated successfully");
      queryClient.setQueryData(["transactions"], data);
    },
  });

  const handleCategoryChange = async (value: string) => {
    const newCategory = value;
    setSelectedCategory(newCategory);

    // Optimistically update the category in the table
    updateCategoryMutation.mutate({
      id: transactionId,
      category: newCategory,
    });
  };

  return (
    <Select
      onValueChange={handleCategoryChange}
      defaultValue={selectedCategory}
    >
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a category" />
      </SelectTrigger>
      <SelectContent>
        {/* Select grouped by section (Income, Housing, etc.) */}
        {Object.entries(categories).map(([categoryGroup, categoryItems]) => (
          <SelectGroup key={categoryGroup}>
            <SelectLabel>{categoryGroup}</SelectLabel>
            {categoryItems.map((category) => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectGroup>
        ))}
      </SelectContent>
    </Select>
  );
};
