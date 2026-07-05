import Link from "next/link";

import { auth } from "@/auth";
import RemoveCollectionButton from "@/components/RemoveCollectionButton";
import { listCollectedStrategies } from "@/lib/collections";
import { strategyHref } from "@/lib/slug";
import { getTranslations } from "next-intl/server";

type PageProps = { params: Promise<{ locale: string }> };

export default async function CollectedStrategiesPage({ params }: PageProps) {
  const { locale } = await params;
  const dictionary = await getTranslations({ locale, namespace: "profile" });
  const session = await auth();
  const userId = session?.user?.id;

  const strategies = userId ? await listCollectedStrategies(userId) : [];

  return (
    <div className="qb-card">
      <h2 className="qb-card-title">{dictionary("collected")}</h2>
      {strategies.length === 0 ?
        <p className="qb-muted" style={{ lineHeight: 1.7, margin: 0 }}>
          {dictionary("collectedEmpty")}
        </p>
      : <ul className="qb-collected-list">
          {strategies.map((s) => (
            <li key={s.id} className="qb-collected-item">
              <div className="qb-collected-item-main">
                <Link className="qb-accent-link" href={strategyHref(s.locale, s.slug)}>
                  {s.title}
                </Link>
                <span className="qb-collected-locale">{s.locale === "zh" ? "中文" : "EN"}</span>
                <span className="qb-collected-meta">
                  {[s.market, s.region, s.annualisedReturn, s.sharpeRatio]
                    .filter(Boolean)
                    .join(" · ")}
                </span>
              </div>
              <RemoveCollectionButton strategyId={s.id} />
            </li>
          ))}
        </ul>
      }
    </div>
  );
}
