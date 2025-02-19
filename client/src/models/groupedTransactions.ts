// Grouped Transactions Model
import { Transaction } from "./transactions";

export interface GroupedTransaction {
  section: string;
  total: number;
  categories: Category[];
}

export interface Category {
  name: string;
  total: number;
  transactions: Transaction[];
}
