import React from "react";

const LoadingSkeleton = ({ className = "", type = "text" }) => {
    const baseClass = "animate-pulse bg-slate-200 rounded";

    if (type === "card") {
        return (
            <div className={`p-4 border border-slate-100 rounded-xl flex flex-col gap-3 ${className}`}>
                <div className={`${baseClass} h-4 w-1/4 mb-2`}></div>
                <div className="flex gap-2">
                    <div className={`${baseClass} h-20 flex-1`}></div>
                    <div className={`${baseClass} h-20 flex-1`}></div>
                </div>
                <div className="flex gap-2">
                    <div className={`${baseClass} h-8 w-16`}></div>
                    <div className={`${baseClass} h-8 w-16`}></div>
                </div>
            </div>
        );
    }

    if (type === "list") {
        return (
            <div className={`flex flex-col gap-2 ${className}`}>
                {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className={`${baseClass} h-12 w-full`}></div>
                ))}
            </div>
        );
    }

    return <div className={`${baseClass} ${className}`}></div>;
};

export default LoadingSkeleton;
