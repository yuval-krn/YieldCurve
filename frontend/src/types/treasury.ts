export type TreasuryResponse = {
  date: string;
  chart_data: ChartPoint[];
};

export type ChartPoint = {
  term: string;
  Yield: number;
};

export type OrderData = {
  term: string;
  quantity: number;
};

export type OrderHistoryItem = {
  term: string;
  yield: number;
  quantity: number;
  issueDate: string;
  purchaseTimestamp: string;
  maturityDate: string;
};
