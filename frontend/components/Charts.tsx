"use client";

import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function FunnelChart({ data }: { data: Array<{ stage: string; count: number }> }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ded7c9" />
        <XAxis dataKey="stage" tick={{ fontSize: 11 }} />
        <YAxis />
        <Tooltip />
        <Bar dataKey="count" fill="#164b35" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function IntentChart({ data }: { data: Array<{ intent: string; count: number }> }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ded7c9" />
        <XAxis dataKey="intent" tick={{ fontSize: 11 }} />
        <YAxis />
        <Tooltip />
        <Bar dataKey="count" fill="#28536b" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ConversionLine({ data }: { data: Array<{ week: string; conversion: number }> }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ded7c9" />
        <XAxis dataKey="week" />
        <YAxis tickFormatter={(v) => `${Math.round(Number(v) * 100)}%`} />
        <Tooltip formatter={(v) => `${Math.round(Number(v) * 100)}%`} />
        <Line type="monotone" dataKey="conversion" stroke="#164b35" strokeWidth={3} dot />
      </LineChart>
    </ResponsiveContainer>
  );
}

