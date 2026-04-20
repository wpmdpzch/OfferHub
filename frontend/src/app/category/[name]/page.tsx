import { api } from "@/lib/api";
import type { ArticleListOut } from "@/types";
import ArticleCard from "@/components/article/ArticleCard";
import Header from "@/components/layout/Header";
import type { Metadata } from "next";
import Link from "next/link";

interface Props {
  params: { name: string };
  searchParams: { page?: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const name = decodeURIComponent(params.name);
  return {
    title: `${name} - OfferHub`,
    description: `OfferHub 中分类为「${name}」的面试题和面经汇总`,
  };
}

export default async function CategoryPage({ params, searchParams }: Props) {
  const name = decodeURIComponent(params.name);
  const page = Number(searchParams.page ?? 1);

  let data: ArticleListOut = { total: 0, page: 1, page_size: 20, items: [] };
  try {
    data = await api.get<ArticleListOut>(`/articles?category=${encodeURIComponent(name)}&page=${page}`);
  } catch {}

  const totalPages = Math.ceil(data.total / data.page_size);

  return (
    <>
      <Header />
      <main className="max-w-6xl mx-auto px-4 py-6 flex gap-6">
        <aside className="hidden md:block w-48 shrink-0">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h2 className="text-sm font-semibold text-gray-500 mb-3">📂 分类</h2>
            <ul className="space-y-1">
              <li>
                <Link href="/" className="block px-2 py-1.5 rounded text-sm text-gray-700 hover:bg-gray-50">
                  全部
                </Link>
              </li>
              {["面经分享", "技术文章", "学习路径", "面试技巧", "行业资讯", "题库解析"].map((cat) => (
                <li key={cat}>
                  <Link href={`/category/${encodeURIComponent(cat)}`}
                    className={`block px-2 py-1.5 rounded text-sm hover:bg-gray-50 ${cat === name ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-700'}`}>
                    {cat}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-lg font-semibold text-gray-800">
              <span className="text-blue-600">{name}</span>
            </h1>
            <span className="text-sm text-gray-500">{data.total} 篇</span>
          </div>
          <div className="space-y-3">
            {data.items.length === 0 ? (
              <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
                <div className="text-4xl mb-3">📂</div>
                <p className="text-gray-400">暂无相关分类内容</p>
              </div>
            ) : (
              data.items.map((a) => <ArticleCard key={a.id} article={a} />)
            )}
          </div>
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              {page > 1 && (
                <Link href={`/category/${encodeURIComponent(name)}?page=${page - 1}`}
                  className="px-4 py-2 border border-gray-200 rounded text-sm hover:bg-gray-50">
                  ← 上一页
                </Link>
              )}
              <span className="px-4 py-2 text-sm text-gray-500">第 {page} / {totalPages} 页</span>
              {page < totalPages && (
                <Link href={`/category/${encodeURIComponent(name)}?page=${page + 1}`}
                  className="px-4 py-2 border border-gray-200 rounded text-sm hover:bg-gray-50">
                  下一页 →
                </Link>
              )}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
