import { redirect } from "next/navigation";

type PageProps = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ next?: string }>;
};

export default async function LoginPage({ params, searchParams }: PageProps) {
  const { locale } = await params;
  const query = await searchParams;
  const next = query.next ? `&next=${encodeURIComponent(query.next)}` : "";
  redirect(`/${locale}?auth=login${next}`);
}
