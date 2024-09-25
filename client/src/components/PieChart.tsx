import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import type { ChartOptions } from "chart.js";

// Register the required components from Chart.js
ChartJS.register(ArcElement, Tooltip, Legend);
// Optional chart configuration
const pieOptions: ChartOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: "top",
    },
  },
};
interface PieChartProps {
  transactions: { [key: string]: number };
}

export default function PieChart({ transactions }: PieChartProps) {
  const getRandomColor = (num_of_colors: number) => {
    // get int value of colors in increments
    const colors = [];
    // divide 255 by num_of_colors to get the increment
    const increment = Math.floor(255 / num_of_colors);
    for (let i = 0; i < num_of_colors; i++) {
      // push the color in rgb format
      colors.push(`hsla(${i * increment}, 100%, 50%, 0.8)`);
    }
    return colors;
  };

  const pieData = {
    labels: Object.keys(transactions),
    datasets: [
      {
        label: "Transaction Amount",
        data: Object.values(transactions),
        backgroundColor: getRandomColor(Object.keys(transactions).length),
      },
    ],
  };

  return (
    <div className="container mx-auto pl-4 mt-4">
      <Doughnut data={pieData} options={pieOptions} />
    </div>
  );
}
