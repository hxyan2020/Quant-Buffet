import { redirect } from "next/navigation";

export default function LegacyAdminList() {
  redirect("/admin/strategies");
}
