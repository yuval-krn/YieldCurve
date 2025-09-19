import { useState, useEffect } from "react";
import type { OrderData, OrderHistoryItem } from "./types/treasury";

// Type definitions for Pydantic validation errors
interface ValidationErrorDetail {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

interface ApiOrder {
  id: number;
  term: string;
  yield_value: number;
  quantity: number;
  issue_date: string;
  purchase_timestamp: string;
  maturity_date: string;
}

interface UseOrdersResult {
  orders: OrderHistoryItem[];
  loading: boolean;
  error: string | null;
  submitOrder: (
    order: OrderData,
  ) => Promise<{ success: boolean; error?: string }>;
  refreshOrders: () => Promise<void>;
  clearError: () => void;
}

const API_BASE_URL = "http://localhost:8000";

export function useOrders(): UseOrdersResult {
  const [orders, setOrders] = useState<OrderHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Convert API order format to frontend format
  const convertApiOrderToHistoryItem = (
    apiOrder: ApiOrder,
  ): OrderHistoryItem => {
    return {
      term: apiOrder.term,
      yield: apiOrder.yield_value,
      quantity: apiOrder.quantity,
      issueDate: apiOrder.issue_date,
      purchaseTimestamp: apiOrder.purchase_timestamp,
      maturityDate: apiOrder.maturity_date,
    };
  };

  // Fetch orders from API
  const fetchOrders = async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/orders/`);

      if (!response.ok) {
        throw new Error(
          `Failed to fetch orders: ${response.status} ${response.statusText}`,
        );
      }

      const apiOrders: ApiOrder[] = await response.json();
      const convertedOrders = apiOrders.map(convertApiOrderToHistoryItem);

      setOrders(convertedOrders);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMessage);
      console.error("Error fetching orders:", err);
    } finally {
      setLoading(false);
    }
  };

  // Submit new order
  const submitOrder = async (
    order: OrderData,
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      setError(null);

      const response = await fetch(`${API_BASE_URL}/orders/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(order),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);

        let errorMessage: string;

        // Handle Pydantic validation errors
        if (errorData?.detail && Array.isArray(errorData.detail)) {
          // Extract validation error messages
          const validationErrors = errorData.detail as ValidationErrorDetail[];
          const errorMessages = validationErrors
            .map((error: ValidationErrorDetail) => {
              let msg = error.msg || "Validation error";
              // Clean up Pydantic "Value error, " prefix
              if (msg.startsWith("Value error, ")) {
                msg = msg.replace("Value error, ", "");
              }
              return msg;
            })
            .join(", ");
          errorMessage = errorMessages;
        } else if (errorData?.detail && typeof errorData.detail === "string") {
          // Handle string detail messages
          errorMessage = errorData.detail;
        } else {
          // Fallback error message
          errorMessage = `Failed to submit order: ${response.status} ${response.statusText}`;
        }

        return { success: false, error: errorMessage };
      }

      // Refresh orders list after successful submission
      await fetchOrders();
      return { success: true };
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred";
      console.error("Error submitting order:", err);
      return { success: false, error: errorMessage };
    }
  };

  // Refresh orders (exposed for manual refresh)
  const refreshOrders = async (): Promise<void> => {
    await fetchOrders();
  };

  // Clear error state
  const clearError = (): void => {
    setError(null);
  };

  // Fetch orders on mount
  useEffect(() => {
    fetchOrders();
  }, []);

  return {
    orders,
    loading,
    error,
    submitOrder,
    refreshOrders,
    clearError,
  };
}
