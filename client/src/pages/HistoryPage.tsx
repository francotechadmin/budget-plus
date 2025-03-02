import BarChartVertical from "../components/BarChartVertical"; // Import the BarChartVertical component
import { useGetTransactionHistoryQuery } from "@/hooks/api/useGetTransactionHistoryQuery";
import { Skeleton } from "@/components/ui/skeleton";
const HistoryPage = () => {
  const {
    data: transactions = {},
    isLoading: transactionsLoading,
    error,
  } = useGetTransactionHistoryQuery();

  if (error) {
    return <div>Error fetching data.</div>;
  }

  if (transactionsLoading) {
    return (
      <div className="container mx-auto px-4 mt-4">
        <h1 className="text-2xl font-bold">History</h1>
        <Skeleton className="h-[350px] w-full mt-4" />
      </div>
    );
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
