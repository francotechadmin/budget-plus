// src/components/CategoryDropdown.tsx
import React, { useState } from "react";
import { useUpdateTransactionMutation } from "@/hooks/api/useUpdateTransactionMutation";
import { CategorySelect } from "./CategorySelect";

interface CategoryDropdownProps {
  transactionId: string;
  initialCategory: string;
  sections: Record<string, string[]>;
}

export const CategoryDropdown: React.FC<CategoryDropdownProps> = ({
  transactionId,
  initialCategory,
  sections,
}) => {
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const { mutate: updateTransaction } = useUpdateTransactionMutation();

  const handleCategoryChange = (value: string) => {
    setSelectedCategory(value);
    // Optimistically update the category for the transaction
    updateTransaction({
      id: transactionId,
      category: value,
    });
  };

  return (
    <CategorySelect
      value={selectedCategory}
      onChange={handleCategoryChange}
      sections={sections}
    />
  );
};
