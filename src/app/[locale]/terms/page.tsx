import { redirect } from "next/navigation";

type PageProps = { params: Promise<{ locale: string }> };

export default async function TermsPage({ params }: PageProps) {
  const { locale } = await params;
  redirect(`/${locale}?legal=terms`);
}
