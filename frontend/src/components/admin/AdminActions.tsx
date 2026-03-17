"use client";

import { useState } from "react";
import { CLIENT_API } from "@/lib/api";

interface Props {
  articleId: string;
  token: string;
}

export default function AdminActions({ articleId, token }: Props) {
  const [status, setStatus] = useState<"idle" | "approved" | "rejected" | "loading">("idle");

  async function act(action: "approve" | "reject") {
    setStatus("loading");
    try {
      const res = await fetch(`${CLIENT_API}/admin/articles/${articleId}/${action}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.code !== 0) throw new Error(json.msg);
      setStatus(action === "approve" ? "approved" : "rejected");
    } catch {
      setStatus("idle");
      alert("操作失败，请重试");
    }
  }

  if (status === "approved") return <span className="text-xs text-green-600 font-medium shrink-0">✓ 已通过</span>;
  if (status === "rejected") return <span className="text-xs text-red-500 font-medium shrink-0">✗ 已拒绝</span>;

  return (
    <div className="flex gap-2 shrink-0">
      <button
        onClick={() => act("approve")}
        disabled={status === "loading"}
        className="px-3 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
      >
        通过
      </button>
      <button
        onClick={() => act("reject")}
        disabled={status === "loading"}
        className="px-3 py-1.5 text-xs bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
      >
        拒绝
      </button>
    </div>
  );
}
