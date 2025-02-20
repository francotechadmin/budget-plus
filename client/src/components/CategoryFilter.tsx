"use client";

import { ListFilter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Column } from "@tanstack/react-table";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

interface CategoryFilterDropdownProps<TData, TValue>
  extends React.HTMLAttributes<HTMLDivElement> {
  column: Column<TData, TValue>;
  sections: { [key: string]: string[] };
}

export function CategoryFilter<TData, TValue>({
  column,
  sections,
  className,
}: CategoryFilterDropdownProps<TData, TValue>) {
  const options = [{ label: "All", value: "all" }];
  Object.entries(sections).forEach(([sectionName, cats]) => {
    cats.forEach((category) => {
      options.push({ label: `${sectionName} - ${category}`, value: category });
    });
  });

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="-ml-3 h-8 data-[state=open]:bg-accent"
          >
            <span>Category</span>
            <ListFilter className="ml-2 h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="max-h-60 overflow-auto">
          <DropdownMenuLabel>Filter by Category</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {options.map((option) => (
            <DropdownMenuItem
              key={option.value}
              onSelect={() =>
                column.setFilterValue(
                  option.value === "all" ? undefined : option.value
                )
              }
            >
              {option.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
