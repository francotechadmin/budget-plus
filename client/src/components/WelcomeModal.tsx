// components/WelcomeModal.tsx
import React from "react";
import { Button } from "@/components/ui/button";
import { X, Download, SquarePlus, Notebook } from "lucide-react";

interface WelcomeModalProps {
  onClose: () => void;
}

const WelcomeModal: React.FC<WelcomeModalProps> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black opacity-50"
        onClick={onClose}
      ></div>

      {/* Modal Content */}
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-[90vw] xl:max-w-lg w-full p-6 z-10">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center flex-wrap">
            Welcome to <Notebook className="w-5 ml-2 mr-1" /> Budget+
          </h2>
          <Button
            variant="default"
            onClick={onClose}
            className="bg-transparent border-none shadow-none text-primary hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <p className="text-gray-700 dark:text-gray-300 mb-4">
          We're excited to have you on board! Here's a quick overview of what
          you can do:
        </p>

        <ul className="list-disc ml-6 text-gray-700 dark:text-gray-300 mb-6 space-y-2">
          <li>
            <span className="font-medium">Transactions:</span> View all your
            transactions, add new ones manually using the{" "}
            <SquarePlus className="inline h-4 w-4" /> button, or import them
            with the <Download className="inline h-4 w-4" /> button.
          </li>
          <li>
            <span className="font-medium">Expenses:</span> Get insightful
            visualizations of your expenses by category.
          </li>
          <li>
            <span className="font-medium">Budgets:</span> See running totals and
            expenses by category to manage your spending.
          </li>
          <li>
            <span className="font-medium">History:</span> Review a 6-month
            history of your income vs. expenses.
          </li>
        </ul>

        <div className="flex justify-end">
          <Button variant="default" onClick={onClose}>
            Get Started
          </Button>
        </div>
      </div>
    </div>
  );
};

export default WelcomeModal;
