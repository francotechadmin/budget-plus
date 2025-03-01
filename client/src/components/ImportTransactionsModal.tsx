// src/components/ImportTransactionsModal.tsx
import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Import, Building } from "lucide-react";
import { useImportTransactionsMutation } from "@/hooks/api/useImportTransactionsMutation";
import { Label } from "./ui/label";
import { cn } from "@/lib/utils";
import { Spinner } from "./ui/loader";

export function ImportTransactionsModal() {
  const [open, setOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const {
    mutate: importTransactionsMutation,
    isPending: isImporting,
    error,
  } = useImportTransactionsMutation();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleImport = () => {
    if (selectedFile) {
      importTransactionsMutation(selectedFile, {
        onSuccess: () => {
          setSelectedFile(null); // Reset the file input after successful import
          setOpen(false); // Close the dialog
        },
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default">
          Import Transactions <Import className="ml-1 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="w-full max-w-4xl">
        <DialogHeader>
          <DialogTitle>Import or Link Transactions</DialogTitle>
          <DialogDescription>
            Choose how you would like to add transactions.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col md:flex-row gap-4">
          {/* Left Panel: Link Bank Transactions */}
          <div className="flex-1 border p-4 rounded">
            <div className="flex items-center gap-2">
              <Building className="w-5 h-5" />
              <h2 className="text-lg font-bold">Link Bank Transactions</h2>
            </div>
            <p className="text-sm text-gray-500 mt-1">Coming soon</p>
          </div>
          {/* Right Panel: Import CSV/Excel */}
          <div className="flex-1 border p-4 rounded">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Import className="w-5 h-5" />
                  <h2 className="text-lg font-bold">Import CSV/Excel</h2>
                </div>
              </div>
              {error && (
                <div className="text-red-500 text-sm mt-2">
                  There was an error adding your transaction.
                </div>
              )}
              <p className="text-sm text-gray-500 mt-2">
                The file must include the following headers:{" "}
                <strong>date</strong>, <strong>description</strong>,{" "}
                <strong>amount</strong>, and optionally{" "}
                <strong>category</strong>.
              </p>
              <div className="grid w-full max-w-sm items-center gap-1.5 mt-2">
                <Label htmlFor="transaction_file" className="text-sm">
                  Select a file
                </Label>
                <Input
                  id="transaction_file"
                  type="file"
                  accept=".csv, .xlsx"
                  className={cn(
                    // change text color to white
                    "file:text-primary"
                  )}
                  onChange={handleFileChange}
                />
              </div>
              <div className="flex justify-center">
                <Button
                  onClick={handleImport}
                  disabled={!selectedFile || isImporting}
                  className="mt-2"
                >
                  {isImporting == true ? (
                    <Spinner size={"small"} />
                  ) : (
                    <div className="flex items-center">
                      Import <Import className="ml-2 w-4" />{" "}
                    </div>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
