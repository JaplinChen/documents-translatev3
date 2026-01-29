import React from 'react';

/**
 * Unified Category Pill Component
 * Features:
 * 1. Automatic dynamic coloring based on name hashing (handles growing category lists).
 * 2. Predefined high-contrast semantic colors for common categories.
 */
export function CategoryPill({ name, className = "" }) {
    if (!name) return <span className="text-slate-300">-</span>;

    // Harmonious color palettes (bg-100, text-700)
    const palettes = [
        { bg: "bg-blue-100", text: "text-blue-700" },
        { bg: "bg-indigo-100", text: "text-indigo-700" },
        { bg: "bg-purple-100", text: "text-purple-700" },
        { bg: "bg-emerald-100", text: "text-emerald-700" },
        { bg: "bg-orange-100", text: "text-orange-700" },
        { bg: "bg-cyan-100", text: "text-cyan-700" },
        { bg: "bg-rose-100", text: "text-rose-700" },
        { bg: "bg-amber-100", text: "text-amber-700" },
        { bg: "bg-teal-100", text: "text-teal-700" },
        { bg: "bg-violet-100", text: "text-violet-700" },
        { bg: "bg-lime-100", text: "text-lime-700" },
        { bg: "bg-pink-100", text: "text-pink-700" }
    ];

    // Priority mapping for fixed semantic categories
    const getFixedColor = (catName) => {
        const mapping = {
            "產品名稱": { bg: "bg-blue-100", text: "text-blue-700" },
            "技術縮寫": { bg: "bg-indigo-100", text: "text-indigo-700" },
            "專業術語": { bg: "bg-purple-100", text: "text-purple-700" },
            "翻譯術語": { bg: "bg-emerald-100", text: "text-emerald-700" },
            "公司名稱": { bg: "bg-orange-100", text: "text-orange-700" },
            "網絡術語": { bg: "bg-cyan-100", text: "text-cyan-700" }
        };
        return mapping[catName];
    };

    // Dynamic Hash Logic
    const getHashColor = (catName) => {
        let hash = 0;
        for (let i = 0; i < catName.length; i++) {
            hash = catName.charCodeAt(i) + ((hash << 5) - hash);
        }
        const index = Math.abs(hash) % palettes.length;
        return palettes[index];
    };

    const color = getFixedColor(name) || getHashColor(name);

    return (
        <span className={`text-[10px] font-black px-2.5 py-1 rounded-full uppercase tracking-wider inline-block shrink-0 ${color.bg} ${color.text} ${className}`}>
            {name}
        </span>
    );
}
