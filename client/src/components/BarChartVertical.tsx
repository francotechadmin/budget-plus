import React, { useState, useEffect } from "react";
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
  const [isMobile, setIsMobile] = useState<boolean>(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768); // adjust breakpoint if needed
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Prepare the data for the bar chart
  const data = {
    labels: Object.keys(monthlyData),
    datasets: [
      {
        label: "Income",
        data: Object.values(monthlyData).map((data) => data.income),
        backgroundColor: "#36A2EB",
      },
      {
        label: "Expenses",
        data: Object.values(monthlyData).map((data) => data.expenses),
        backgroundColor: "#FF6384",
      },
    ],
  };

  // Adjust options based on mobile view
  const options = {
    indexAxis: isMobile ? ("y" as const) : ("x" as const),
    maintainAspectRatio: isMobile ? false : true,
    aspectRatio: isMobile ? 1 : 2,
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        stacked: true,
      },
      x: {
        stacked: true,
      },
    },
    plugins: {
      legend: {
        display: true,
      },
    },
    barThickness: 20, // Adjust bar thickness for mobile
  };

  // Increase container height on mobile for a larger chart
  const containerStyle = isMobile
    ? { height: "500px", width: "100%" }
    : { height: "600px", width: "100%" };

  return (
    <div style={containerStyle}>
      <Bar data={data} options={options} />
    </div>
  );
};

export default BarChartVertical;
