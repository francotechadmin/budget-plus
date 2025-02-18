import React, { useState } from "react";
import { useUpdateTransactionMutation } from "@/hooks/api/useUpdateTransactionMutation";
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
  sections: Record<string, string[]>;
}

export const CategoryDropdown: React.FC<CategoryDropdownProps> = ({
  transactionId,
  initialCategory,
  sections,
}) => {
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);

  const { mutate: updateTransaction } = useUpdateTransactionMutation();

  const handleCategoryChange = async (value: string) => {
    const newCategory = value;
    setSelectedCategory(newCategory);

    // Optimistically update the category in the table
    updateTransaction({
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
        {Object.entries(sections).map(([section, categoryItems]) => (
          <SelectGroup key={section}>
            <SelectLabel>{section}</SelectLabel>
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
