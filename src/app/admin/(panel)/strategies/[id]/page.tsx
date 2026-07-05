import { notFound } from "next/navigation";

import ManageStrategyPanel from "@/components/ManageStrategyPanel";
import prisma from "@/lib/prisma";

type PageProps = { params: Promise<{ id: string }> };

export default async function AdminEditStrategyPage({ params }: PageProps) {
  const { id } = await params;
  const exists = await prisma.strategy.findUnique({
    where: { id },
    select: { id: true, title: true },
  });

  if (!exists) {
    notFound();
  }

  return (
    <div className="qb-admin-page">
      <ManageStrategyPanel
        basePath="/admin"
        mode="edit"
        strategyId={exists.id}
        strategyTitle={exists.title}
      />
    </div>
  );
}
