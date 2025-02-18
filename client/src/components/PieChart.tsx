import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import type { ChartOptions } from "chart.js";

// Register the required components from Chart.js
ChartJS.register(ArcElement, Tooltip, Legend);
// Optional chart configuration
const pieOptions: ChartOptions<"doughnut"> = {
  responsive: true,
  plugins: {
    legend: {
      position: "top",
    },
  },
};
interface PieChartProps {
  totals: Record<string, number>;
}

export default function PieChart({ totals }: PieChartProps) {
  // if totals is empty, return chart with no data

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

  let pieData = {
    labels: Object.keys(totals),
    datasets: [
      {
        label: "Transaction Amount",
        data: Object.values(totals),
        backgroundColor: getRandomColor(Object.keys(totals).length),
      },
    ],
  };

  // if totals is empty, return chart with no data
  if (Object.keys(totals).length === 0) {
    pieData = {
      labels: ["No Data"],
      datasets: [
        {
          label: "Transaction Amount",
          data: [1],
          backgroundColor: ["#e5e5e5"],
        },
      ],
    };
  }

  return (
    <div className="flex flex-col justify-center items-center mt-4 w-full max-h-[700px]">
      <Doughnut data={pieData} options={pieOptions} />
    </div>
  );
}
