import { api } from "@/lib/api";
import type { ArticleDetail } from "@/types";
import Header from "@/components/layout/Header";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

interface Props {
  params: { id: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const article = await api.get<ArticleDetail>(`/articles/${params.id}`);
    return {
      title: `${article.title} | OfferHub`,
      description: article.summary ?? undefined,
      openGraph: { title: article.title, description: article.summary ?? undefined, type: "article" },
    };
  } catch {
    return { title: "OfferHub" };
  }
}

export default async function ArticleDetailPage({ params }: Props) {
  let article: ArticleDetail;
  try {
    article = await api.get<ArticleDetail>(`/articles/${params.id}`);
  } catch {
    notFound();
  }

  return (
    <>
      <Header />
      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          {article.category && (
            <span className="text-xs text-blue-500 font-medium">{article.category}</span>
          )}
          <h1 className="text-2xl font-bold text-gray-900 mt-2 mb-4">{article.title}</h1>

          <div className="flex items-center gap-3 text-sm text-gray-400 mb-6 pb-4 border-b">
            <span>{article.author.username}</span>
            <span>·</span>
            <span>{article.published_at ? new Date(article.published_at).toLocaleDateString("zh-CN") : ""}</span>
            <span>·</span>
            <span>👁 {article.view_count}</span>
            <span>👍 {article.like_count}</span>
            {article.source_url && (
              <>
                <span>·</span>
                <a href={article.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                  原文链接
                </a>
              </>
            )}
          </div>

          <div className="prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
              {article.content ?? article.summary ?? ""}
            </ReactMarkdown>
          </div>

          {article.tags.length > 0 && (
            <div className="flex gap-2 flex-wrap mt-6 pt-4 border-t">
              {article.tags.map((tag) => (
                <a key={tag.id} href={`/tag/${encodeURIComponent(tag.name)}`}
                  className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded hover:bg-blue-50 hover:text-blue-600">
                  {tag.name}
                </a>
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
