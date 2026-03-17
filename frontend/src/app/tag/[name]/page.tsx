import { api } from "@/lib/api";
import type { ArticleListOut } from "@/types";
import ArticleCard from "@/components/article/ArticleCard";
import Header from "@/components/layout/Header";

interface Props {
  params: { name: string };
  searchParams: { page?: string };
}

export default async function TagPage({ params, searchParams }: Props) {
  const tag = decodeURIComponent(params.name);
  const page = Number(searchParams.page ?? 1);

  let data: ArticleListOut = { total: 0, page: 1, page_size: 20, items: [] };
  try {
    data = await api.get<ArticleListOut>(`/articles?tag=${encodeURIComponent(tag)}&page=${page}`);
  } catch {}

  return (
    <>
      <Header />
      <main className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-lg font-semibold text-gray-800 mb-4">标签：{tag}</h1>
        <div className="space-y-3">
          {data.items.map((a) => <ArticleCard key={a.id} article={a} />)}
        </div>
      </main>
    </>
  );
}
