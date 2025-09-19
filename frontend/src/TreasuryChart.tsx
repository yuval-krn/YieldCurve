import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  type DotProps,
} from "recharts";

import type { ChartPoint } from "./types/treasury";

type TreasuryChartProps = {
  data: ChartPoint[];
  date: string;
  onPointClick: (point: ChartPoint) => void;
};

export default function TreasuryChart({
  data,
  date,
  onPointClick,
}: TreasuryChartProps) {
  const handleClick: Required<DotProps>["onClick"] = (
    _data: unknown,
    index,
  ) => {
    // @ts-expect-error: typing is known to be bad here in recharts
    const payload = index.payload as ChartPoint;
    onPointClick(payload);
  };

  return (
    <div style={{ width: "100%", height: 400 }}>
      <h2>Treasury Yield Curve ({new Date(date).toLocaleDateString()})</h2>
      <ResponsiveContainer>
        <LineChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="term" />
          <YAxis domain={["auto", "auto"]} tickFormatter={(val) => `${val}%`} />
          <Tooltip formatter={(val) => `${val}%`} />
          <Line
            type="monotone"
            dataKey="Yield"
            stroke="#8884d8"
            activeDot={{ onClick: handleClick, r: 10 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
