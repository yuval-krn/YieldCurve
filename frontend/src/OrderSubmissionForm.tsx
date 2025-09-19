import { useState } from "react";
import type { ChartPoint, OrderData } from "./types/treasury";

type OrderSubmissionFormProps = {
  selectedPoint: ChartPoint;
  onSubmit: (order: OrderData) => void;
  onCancel: () => void;
};

export default function OrderSubmissionForm({
  selectedPoint,
  onSubmit,
  onCancel,
}: OrderSubmissionFormProps) {
  const [amount, setAmount] = useState<string>("1,000");
  const [amountError, setAmountError] = useState<string>("");

  // Function to format number with commas
  const formatWithCommas = (value: string): string => {
    // Remove all non-digit characters
    const numericValue = value.replace(/[^\d]/g, "");

    // Add commas
    return numericValue.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };

  // Function to parse formatted number back to plain number for validation
  const parseFormattedNumber = (value: string): number => {
    return parseFloat(value.replace(/,/g, ""));
  };

  const handleSubmit = () => {
    const numAmount = parseFormattedNumber(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      setAmountError("Please enter a valid dollar amount");
      return;
    }

    onSubmit({
      term: selectedPoint.term,
      yield: selectedPoint.Yield,
      quantity: numAmount,
    });
    setAmount("1,000"); // Reset amount after submission
    setAmountError("");
  };

  const handleCancel = () => {
    onCancel();
    setAmount("1,000"); // Reset amount on cancel
    setAmountError("");
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const formattedValue = formatWithCommas(value);
    setAmount(formattedValue);

    // Clear error when user starts typing
    if (amountError) {
      setAmountError("");
    }
  };

  return (
    <div className="order-form-overlay">
      <div className="order-form">
        <h2>Submit Order</h2>
        <div className="order-form-details">
          <p>
            <strong>Term:</strong> {selectedPoint.term} <br />
            <strong>Yield:</strong> {selectedPoint.Yield}%
          </p>
        </div>
        <div className="quantity-field">
          <label>Investment Amount</label>
          <div className="input-with-dollar">
            <span className="dollar-sign">$</span>
            <input
              type="text"
              value={amount}
              onChange={handleAmountChange}
              placeholder="1,000"
              className="dollar-input"
            />
          </div>
          {amountError && <div className="error-message">{amountError}</div>}
        </div>
        <div className="form-buttons">
          <button className="form-button cancel-button" onClick={handleCancel}>
            Cancel
          </button>
          <button className="form-button submit-button" onClick={handleSubmit}>
            Submit Order
          </button>
        </div>
      </div>
    </div>
  );
}
