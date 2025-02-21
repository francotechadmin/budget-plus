// BarChart.tsx
import React from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

// Register components to be used by Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartProps {
  income: number;
  expenses: number;
}

const BarChart: React.FC<BarChartProps> = ({ income, expenses }) => {
  // Data for the bar chart
  const data = {
    labels: ["Income vs Expenses"],
    datasets: [
      {
        label: "Income",
        data: [income],
        // green color for income
        backgroundColor: "#36A2EB",
      },
      {
        label: "Expenses",
        data: [-expenses], // Negative value for expenses to visually contrast it
        backgroundColor: "#FF6384",
      },
    ],
  };

  // Chart options
  const options = {
    indexAxis: "y" as const, // Display the bars horizontally
    scales: {
      x: {
        beginAtZero: true, // Start the x-axis at 0
      },
    },
    plugins: {
      legend: {
        display: false, // Show the legend
      },
    },
    responsive: true,
    barThickness: 20, // Set the thickness of the bars
    height: 400, // Set the height of the chart
  };

  return <Bar data={data} options={options} height={50} />;
};

export default BarChart;
