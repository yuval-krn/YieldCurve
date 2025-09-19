import type { OrderHistoryItem } from "./types/treasury";

type OrderHistoryProps = {
  orders: OrderHistoryItem[];
};

export default function OrderHistory({ orders }: OrderHistoryProps) {
  if (orders.length === 0) {
    return (
      <div className="order-history">
        <h2>Order History</h2>
        <p>
          No orders yet. Click on a point in the chart above to place your first
          order.
        </p>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatTerm = (term: string) => {
    if (term.endsWith("m")) {
      const months = term.replace("m", "");
      return `${months} Month${months !== "1" ? "s" : ""}`;
    } else if (term.endsWith("Y")) {
      const years = term.replace("Y", "");
      return `${years} Year${years !== "1" ? "s" : ""}`;
    }
    return term;
  };

  return (
    <div className="order-history">
      <h2>Order History</h2>
      <div className="order-history-list">
        {orders.map((order, index) => (
          <div key={index} className="order-card">
            <div className="order-card-header">
              <h3 className="order-card-title">
                Treasury - {formatTerm(order.term)}
              </h3>
            </div>

            <div className="order-card-prominent">
              <div className="prominent-stat">
                <div className="prominent-stat-label">Yield</div>
                <div className="prominent-stat-value yield-value">
                  {order.yield.toFixed(2)}%
                </div>
              </div>
              <div className="prominent-stat">
                <div className="prominent-stat-label">Investment</div>
                <div className="prominent-stat-value amount-value">
                  {formatCurrency(order.quantity)}
                </div>
              </div>
            </div>

            <div className="order-card-details">
              <p className="detail-item">
                <strong>Issue Date:</strong> {formatDate(order.issueDate)}
              </p>
              <p className="detail-item">
                <strong>Purchase Time:</strong>{" "}
                {formatTimestamp(order.purchaseTimestamp)}
              </p>
              <p className="detail-item">
                <strong>Maturity Date:</strong> {formatDate(order.maturityDate)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
