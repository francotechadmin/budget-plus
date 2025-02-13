export interface Transaction {
  id: string;
  amount: number;
  date: Date;
  description: string;
  category: string;
  section: string;
}

export class TransactionModel implements Transaction {
  id: string;
  amount: number;
  date: Date;
  description: string;
  category: string;
  section: string;

  constructor(
    id: string,
    amount: number,
    date: Date,
    description: string,
    category: string,
    section: string
  ) {
    this.id = id;
    this.amount = amount;
    this.date = date;
    this.description = description;
    this.category = category;
    this.section = section;
  }
}
