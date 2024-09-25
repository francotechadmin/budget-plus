import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import BarChartVertical from "../components/BarChartVertical"; // Import the BarChartVertical component

// Fetch transactions and categories from the backend
const fetchExpensesHistory = async () => {
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/transactions/history`
  );
  return response.data;
};

const HistoryPage = () => {
  const { data: transactions, isLoading: transactionsLoading } = useQuery({
    queryKey: ["transaction_history"],
    queryFn: () => fetchExpensesHistory(),
  });

  if (transactionsLoading) {
    return <div>Loading...</div>;
  }

  if (!transactions) {
    return <div>Error fetching data.</div>;
  }

  return (
    <div className="container mx-auto pl-4 mt-4">
      <div className="flex justify-left items-center gap-4">
        <h1 className="text-2xl font-bold text-left">History</h1>
      </div>
      {/* Render the BarChart */}
      <BarChartVertical monthlyData={transactions} />
    </div>
  );
};

export default HistoryPage;
