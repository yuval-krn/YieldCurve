import { useState } from "react";
import { useTreasuryData } from "./useTreasuryData";
import { useOrders } from "./useOrders";

import TreasuryChart from "./TreasuryChart";
import OrderSubmissionForm from "./OrderSubmissionForm";
import OrderHistory from "./OrderHistory";
import LoadingState from "./LoadingState";
import ErrorState from "./ErrorState";
import type { ChartPoint, OrderData } from "./types/treasury";

export default function TreasuryYield() {
  const {
    data,
    loading: treasuryLoading,
    error: treasuryError,
    retry: treasuryRetry,
  } = useTreasuryData();
  const {
    orders,
    loading: ordersLoading,
    error: ordersError,
    submitOrder,
    refreshOrders,
  } = useOrders();
  const [selectedPoint, setSelectedPoint] = useState<ChartPoint | null>(null);
  const [orderSubmitting, setOrderSubmitting] = useState<boolean>(false);
  const [orderSubmissionError, setOrderSubmissionError] = useState<
    string | null
  >(null);

  const handleOrderSubmit = async (order: OrderData) => {
    console.log("Submitting order:", order);

    setOrderSubmitting(true);
    setOrderSubmissionError(null); // Clear any previous submission errors

    try {
      const result = await submitOrder(order);

      if (result.success) {
        setSelectedPoint(null);
      } else {
        // Use the specific error message returned from submitOrder
        setOrderSubmissionError(
          result.error || "Failed to submit order. Please try again.",
        );
      }
    } catch (err) {
      console.error("Order submission error:", err);
      setOrderSubmissionError(
        err instanceof Error ? err.message : "An unexpected error occurred",
      );
    } finally {
      setOrderSubmitting(false);
    }
  };

  const handleOrderCancel = () => {
    setSelectedPoint(null);
    setOrderSubmissionError(null);
  };

  const handlePointClick = (point: ChartPoint) => {
    setSelectedPoint(point);
    setOrderSubmissionError(null);
  };

  const handleRetryOrders = () => {
    refreshOrders();
  };

  // Show loading state if treasury data is still loading
  if (treasuryLoading)
    return <LoadingState message="Loading Treasury data..." />;

  // Show error if treasury data failed to load
  if (treasuryError)
    return <ErrorState error={treasuryError} onRetry={treasuryRetry} />;

  // Show error if no treasury data
  if (!data)
    return <ErrorState error="No data found" onRetry={treasuryRetry} />;

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
          isSubmitting={orderSubmitting}
          error={orderSubmissionError}
        />
      )}

      {ordersLoading ? (
        <LoadingState message="Loading order history..." />
      ) : ordersError ? (
        <div className="order-history-error">
          <h2>Order History</h2>
          <ErrorState error={ordersError} onRetry={handleRetryOrders} />
        </div>
      ) : (
        <OrderHistory orders={orders} />
      )}
    </div>
  );
}
