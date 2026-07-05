import ManageStrategyPanel from "@/components/ManageStrategyPanel";

export default function AdminNewStrategyPage() {
  return (
    <div className="qb-admin-page">
      <ManageStrategyPanel basePath="/admin" mode="create" />
    </div>
  );
}
