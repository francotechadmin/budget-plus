import {
  ChevronLeftIcon,
  ChevronRightIcon,
  DoubleArrowLeftIcon,
  DoubleArrowRightIcon,
} from "@radix-ui/react-icons";
import { Table } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface DataTablePaginationProps<TData> {
  table: Table<TData>;
}

export function DataTablePagination<TData>({
  table,
}: DataTablePaginationProps<TData>) {
  const totalPages = table.getPageCount();
  const currentPage = table.getState().pagination.pageIndex;

  // Function to generate pagination buttons with "..." when necessary
  const getVisiblePageNumbers = () => {
    const pageButtons = [];

    // Always show the first page
    pageButtons.push(0);

    if (currentPage > 3) {
      pageButtons.push(-1); // Ellipsis
    }

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages - 2, currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
      pageButtons.push(i);
    }

    if (currentPage < totalPages - 3) {
      pageButtons.push(-1); // Ellipsis
    }

    // Always show the last page
    if (totalPages > 1) {
      pageButtons.push(totalPages - 1);
    }

    return pageButtons;
  };

  const pages = getVisiblePageNumbers();

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between px-2">
      {/* Total rows & amount */}
      <div className="mb-2 sm:mb-0">
        <p className="text-sm text-muted-foreground">
          {table.getRowModel().rows.length} rows - Total amount: $
          {table
            .getRowModel()
            .rows.reduce(
              (acc, row) => acc + (row.getValue("amount") as number),
              0
            )
            .toFixed(2)}
        </p>
      </div>

      {/* Desktop Pagination Controls */}
      <div className="hidden lg:flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <p className="text-sm font-medium">Rows per page</p>
          <Select
            value={`${table.getState().pagination.pageSize}`}
            onValueChange={(value) => {
              table.setPageSize(Number(value));
            }}
          >
            <SelectTrigger className="h-8 w-[70px]">
              <SelectValue placeholder={table.getState().pagination.pageSize} />
            </SelectTrigger>
            <SelectContent side="top">
              {[10, 20, 30, 40, 50].map((pageSize) => (
                <SelectItem key={pageSize} value={`${pageSize}`}>
                  {pageSize}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex w-[100px] items-center justify-center text-sm font-medium">
          Page {currentPage + 1} of {totalPages}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            className="hidden h-8 w-8 p-0 lg:flex"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">Go to first page</span>
            <DoubleArrowLeftIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">Go to previous page</span>
            <ChevronLeftIcon className="h-4 w-4" />
          </Button>

          {/* Page numbers */}
          {pages.map((page) =>
            page === -1 ? (
              <span
                key={page + Math.random()} // Use a unique key for the ellipsis
                className="h-8 w-8 flex justify-center items-center"
              >
                ...
              </span>
            ) : (
              <Button
                key={page}
                variant={currentPage === page ? "secondary" : "outline"}
                className="h-8 w-8 p-0"
                onClick={() => table.setPageIndex(page)}
              >
                {page + 1}
              </Button>
            )
          )}

          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <span className="sr-only">Go to next page</span>
            <ChevronRightIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            className="hidden h-8 w-8 p-0 lg:flex"
            onClick={() => table.setPageIndex(totalPages - 1)}
            disabled={!table.getCanNextPage()}
          >
            <span className="sr-only">Go to last page</span>
            <DoubleArrowRightIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Mobile Pagination Controls */}
      <div className="flex lg:hidden items-center space-x-2">
        <Button
          variant="outline"
          className="h-8 w-8 p-0"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          <span className="sr-only">Go to previous page</span>
          <ChevronLeftIcon className="h-4 w-4" />
        </Button>
        <div className="text-sm font-medium">
          Page {currentPage + 1} of {totalPages}
        </div>
        <Button
          variant="outline"
          className="h-8 w-8 p-0"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          <span className="sr-only">Go to next page</span>
          <ChevronRightIcon className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
