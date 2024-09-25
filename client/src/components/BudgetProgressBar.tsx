// BudgetProgressBar.tsx
import React from "react";

interface BudgetProgressBarProps {
  totalAmount: number; // Total budget amount
  spentAmount: number; // Amount already spent
}

const BudgetProgressBar: React.FC<BudgetProgressBarProps> = ({
  totalAmount,
  spentAmount,
}) => {
  // Calculate the percentage of the budget used
  const percentageUsed = (spentAmount / totalAmount) * 100;

  return (
    <div style={{ width: "50%", padding: "10px", marginInlineStart: "auto" }}>
      <div
        style={{
          height: "20px", // Height of the progress bar
          width: "100%",
          backgroundColor: "#e0e0df", // Light gray background
          borderRadius: "5px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${percentageUsed}%`, // Fill based on percentage used
            backgroundColor: percentageUsed > 75 ? "#ff6f61" : "#36A2EB", // Red if over 75%, blue otherwise
            transition: "width 0.5s ease-in-out", // Smooth transition when percentage changes
          }}
        />
      </div>
      {/* <p style={{ textAlign: "center", marginTop: "10px" }}>
        {spentAmount.toFixed(2)} / {totalAmount.toFixed(2)} spent
      </p> */}
    </div>
  );
};

export default BudgetProgressBar;
