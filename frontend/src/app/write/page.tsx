"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import { CLIENT_API } from "@/lib/api";

const CATEGORIES = ["面经分享", "技术文章", "学习路径", "面试技巧", "行业资讯", "题库解析"];

export default function WritePage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [tags, setTags] = useState<string[]>([]);

  function addTag(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      const v = tagInput.trim();
      if (v && !tags.includes(v) && tags.length < 8) {
        setTags([...tags, v]);
      }
      setTagInput("");
    }
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    const form = e.currentTarget;
    const token = localStorage.getItem("token");
    if (!token) {
      setError("请先登录");
      setSubmitting(false);
      return;
    }

    const body = {
      title: (form.elements.namedItem("title") as HTMLInputElement).value.trim(),
      content: (form.elements.namedItem("content") as HTMLTextAreaElement).value.trim(),
      summary: (form.elements.namedItem("summary") as HTMLInputElement).value.trim() || undefined,
      category: (form.elements.namedItem("category") as HTMLSelectElement).value || undefined,
      tag_names: tags,
    };

    if (!body.title || !body.content) {
      setError("标题和正文不能为空");
      setSubmitting(false);
      return;
    }

    try {
      const res = await fetch(`${CLIENT_API}/articles`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (json.code !== 0) throw new Error(json.msg ?? "提交失败");
      router.push(`/articles/${json.data.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "提交失败，请重试");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Header />
      <main className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-xl font-bold text-gray-900 mb-6">发布文章</h1>
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* 标题 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">标题 *</label>
            <input
              name="title"
              maxLength={200}
              placeholder="请输入文章标题"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* 分类 */}
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
              <select
                name="category"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:border-blue-500 bg-white"
              >
                <option value="">请选择分类</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">摘要（可选）</label>
              <input
                name="summary"
                maxLength={300}
                placeholder="一句话描述文章内容"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* 标签 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              标签（回车或逗号添加，最多 8 个）
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {tags.map((t) => (
                <span key={t} className="flex items-center gap-1 text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded">
                  {t}
                  <button type="button" onClick={() => setTags(tags.filter((x) => x !== t))} className="hover:text-red-500">×</button>
                </span>
              ))}
            </div>
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={addTag}
              placeholder="输入标签后按回车"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* 正文 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">正文（支持 Markdown）*</label>
            <textarea
              name="content"
              rows={16}
              placeholder="## 面试经历&#10;&#10;### 一面&#10;..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono focus:outline-none focus:border-blue-500 resize-y"
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? "提交中..." : "发布"}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 border border-gray-300 text-gray-600 text-sm rounded-md hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        </form>
      </main>
    </>
  );
}
