import { useEffect, useState } from "react";
import type { TreasuryResponse, ChartPoint } from "./types/treasury";

export function useTreasuryData() {
  const [data, setData] = useState<{
    chartData: ChartPoint[];
    date: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("http://localhost:8000/");
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const json: TreasuryResponse = await res.json();
      setData({
        chartData: json.chart_data,
        date: json.date,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const retry = () => {
    fetchData();
  };

  return {
    data,
    loading,
    error,
    retry,
  };
}
