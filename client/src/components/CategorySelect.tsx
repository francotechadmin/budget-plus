// src/components/CategorySelect.tsx
import React from "react";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface CategorySelectProps {
  value: string;
  onChange: (value: string) => void;
  sections: Record<string, string[]>;
}

export const CategorySelect: React.FC<CategorySelectProps> = ({
  value,
  onChange,
  sections,
}) => {
  return (
    <Select onValueChange={onChange} defaultValue={value}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a category" />
      </SelectTrigger>
      <SelectContent>
        {sections &&
          Object.entries(sections).map(([section, categoryItems]) => (
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
