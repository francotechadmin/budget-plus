// BarChartVertical.tsx
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

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartVerticalProps {
  monthlyData: {
    [key: string]: {
      income: number;
      expenses: number;
    };
  };
}

const BarChartVertical: React.FC<BarChartVerticalProps> = ({ monthlyData }) => {
  // Prepare the data for the bar chart
  const data = {
    labels: Object.keys(monthlyData), // Months as labels
    datasets: [
      {
        label: "Income",
        data: Object.values(monthlyData).map((data) => data.income), // Income data
        backgroundColor: "#36A2EB", // Blue color for income
      },
      {
        label: "Expenses",
        data: Object.values(monthlyData).map((data) => data.expenses), // Expenses data
        backgroundColor: "#FF6384", // Red color for expenses
      },
    ],
  };

  // Chart options to enable stacked bars
  const options = {
    scales: {
      y: {
        beginAtZero: true, // Ensure the y-axis starts at 0
        stacked: true, // Enable stacking on the y-axis
      },
      x: {
        stacked: true, // Enable stacking on the x-axis
      },
    },
    plugins: {
      legend: {
        display: true, // Show the legend
      },
    },
    responsive: true, // Make the chart responsive
    // maintainAspectRatio: false, // Allow for a responsive chart without fixed aspect ratio
    barThickness: 50, // Adjust the bar thickness
  };

  return <Bar data={data} options={options} />;
};

export default BarChartVertical;
