import { Suspense } from "react";

import AdminStrategyList from "@/components/admin/AdminStrategyList";

export default function AdminStrategiesPage() {
  return (
    <Suspense fallback={<p className="qb-admin-muted">Loading admin…</p>}>
      <AdminStrategyList />
    </Suspense>
  );
}
