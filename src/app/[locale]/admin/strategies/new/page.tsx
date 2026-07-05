import { redirect } from "next/navigation";

export default function LegacyAdminNew() {
  redirect("/admin/strategies/new");
}
