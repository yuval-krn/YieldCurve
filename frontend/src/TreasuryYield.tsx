import { useState } from "react";
import { useTreasuryData } from "./useTreasuryData";

import TreasuryChart from "./TreasuryChart";
import OrderSubmissionForm from "./OrderSubmissionForm";
import OrderHistory from "./OrderHistory";
import LoadingState from "./LoadingState";
import ErrorState from "./ErrorState";
import type { ChartPoint, OrderData, OrderHistoryItem } from "./types/treasury";

export default function TreasuryYield() {
  const { data, loading, error, retry } = useTreasuryData();
  const [selectedPoint, setSelectedPoint] = useState<ChartPoint | null>(null);
  const [orderHistory, setOrderHistory] = useState<OrderHistoryItem[]>([]);

  // Helper function to calculate maturity date based on term
  const calculateMaturityDate = (issueDate: string, term: string): string => {
    const issue = new Date(issueDate);

    // Handle terms like "1m", "6m", "1Y", "2Y", etc.
    if (term.endsWith("m")) {
      // Month terms like "1m", "6m"
      const months = parseFloat(term.replace("m", ""));
      issue.setMonth(issue.getMonth() + months);
    } else if (term.endsWith("Y")) {
      // Year terms like "1Y", "2Y", "30Y"
      const years = parseInt(term.replace("Y", ""));
      issue.setFullYear(issue.getFullYear() + years);
    }

    return issue.toISOString().split("T")[0];
  };

  const handleOrderSubmit = (order: OrderData) => {
    console.log("Submitting order:", order);

    // Create order history item
    const purchaseTimestamp = new Date().toISOString();
    const issueDate = data?.date || new Date().toISOString().split("T")[0];
    const maturityDate = calculateMaturityDate(issueDate, order.term);

    const historyItem: OrderHistoryItem = {
      term: order.term,
      yield: order.yield,
      quantity: order.quantity,
      issueDate: issueDate,
      purchaseTimestamp: purchaseTimestamp,
      maturityDate: maturityDate,
    };

    // Add to history (newest first)
    setOrderHistory((prev) => [historyItem, ...prev]);
    setSelectedPoint(null);
  };

  const handleOrderCancel = () => {
    setSelectedPoint(null);
  };

  const handlePointClick = (point: ChartPoint) => {
    setSelectedPoint(point);
  };

  if (loading) return <LoadingState message="Loading Treasury data..." />;
  if (error) return <ErrorState error={error} onRetry={retry} />;
  if (!data) return <ErrorState error="No data found" onRetry={retry} />;

  return (
    <div>
      <TreasuryChart
        data={data.chartData}
        date={data.date}
        onPointClick={handlePointClick}
      />
      {selectedPoint && (
        <OrderSubmissionForm
          selectedPoint={selectedPoint}
          onSubmit={handleOrderSubmit}
          onCancel={handleOrderCancel}
        />
      )}
      <OrderHistory orders={orderHistory} />
    </div>
  );
}
