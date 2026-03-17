import { api } from "@/lib/api";
import type { ArticleListOut } from "@/types";
import ArticleCard from "@/components/article/ArticleCard";
import Header from "@/components/layout/Header";
import type { Metadata } from "next";

interface Props {
  searchParams: { q?: string; page?: string };
}

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const q = searchParams.q ?? "";
  return q
    ? { title: `"${q}" 搜索结果`, description: `OfferHub 搜索「${q}」的面试题和面经` }
    : { title: "搜索面试题" };
}

export default async function SearchPage({ searchParams }: Props) {
  const q = searchParams.q ?? "";
  const page = Number(searchParams.page ?? 1);

  let data: ArticleListOut & { items: any[] } = { total: 0, page: 1, page_size: 20, items: [] };
  if (q) {
    try {
      data = await api.get(`/search?q=${encodeURIComponent(q)}&page=${page}`);
    } catch {}
  }

  return (
    <>
      <Header />
      <main className="max-w-3xl mx-auto px-4 py-8">
        <form className="flex mb-6">
          <input
            name="q"
            defaultValue={q}
            placeholder="搜索面试题、面经..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:border-blue-500"
          />
          <button type="submit" className="px-5 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700">
            搜索
          </button>
        </form>

        {q && (
          <p className="text-sm text-gray-500 mb-4">
            "{q}" 共找到 {data.total} 条结果
          </p>
        )}

        {!q && (
          <div className="text-center py-20 text-gray-400">请输入关键词开始搜索</div>
        )}

        <div className="space-y-3">
          {data.items.map((item) => (
            <ArticleCard key={item.id} article={item} />
          ))}
        </div>
      </main>
    </>
  );
}
