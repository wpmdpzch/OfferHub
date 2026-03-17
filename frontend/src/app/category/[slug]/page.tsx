import { api } from "@/lib/api";
import type { ArticleListOut } from "@/types";
import ArticleCard from "@/components/article/ArticleCard";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import type { Metadata } from "next";

interface Props {
  params: { slug: string };
  searchParams: { page?: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const category = decodeURIComponent(params.slug);
  return { title: category, description: `OfferHub ${category}分类下的面试题和面经` };
}

export default async function CategoryPage({ params, searchParams }: Props) {
  const category = decodeURIComponent(params.slug);
  const page = Number(searchParams.page ?? 1);

  let data: ArticleListOut = { total: 0, page: 1, page_size: 20, items: [] };
  try {
    data = await api.get<ArticleListOut>(`/articles?category=${encodeURIComponent(category)}&page=${page}`);
  } catch {}

  return (
    <>
      <Header />
      <main className="max-w-6xl mx-auto px-4 py-6 flex gap-6">
        <Sidebar activeCategory={category} />
        <div className="flex-1 min-w-0">
          <h1 className="text-lg font-semibold text-gray-800 mb-4">{category}</h1>
          <div className="space-y-3">
            {data.items.length === 0 ? (
              <div className="text-center py-20 text-gray-400">暂无内容</div>
            ) : (
              data.items.map((a) => <ArticleCard key={a.id} article={a} />)
            )}
          </div>
        </div>
      </main>
    </>
  );
}
