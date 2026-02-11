import { useLayoutEffect, useRef, useState } from "react";

/**
 * Custom hook for draggable modal positioning
 * 支援從 localStorage 還原位置/尺寸
 */
export function useDraggableModal(open, storageKey) {
    const modalRef = useRef(null);
    const [position, setPosition] = useState({ top: 0, left: 0 });
    const dragState = useRef(null);

    const savePosition = (next) => {
        if (!storageKey) return;
        try {
            const saved = localStorage.getItem(storageKey);
            const parsed = saved ? JSON.parse(saved) : {};
            localStorage.setItem(
                storageKey,
                JSON.stringify({ ...parsed, top: next.top, left: next.left })
            );
        } catch {
            // 忽略儲存失敗
        }
    };

    useLayoutEffect(() => {
        if (!open) return;
        const modal = modalRef.current;
        if (!modal) return;

        // 先嘗試從 localStorage 還原已存的位置，避免覆蓋 ManageModal 的儲存狀態
        if (storageKey) {
            try {
                const saved = localStorage.getItem(storageKey);
                if (saved) {
                    const parsed = JSON.parse(saved);
                    if (typeof parsed?.top === 'number' && typeof parsed?.left === 'number') {
                        setPosition({ top: parsed.top, left: parsed.left });
                        return; // 已有儲存位置，不需要計算居中
                    }
                }
            } catch {
                // 讀取失敗，繼續使用居中計算
            }
        }

        // 沒有儲存位置時，計算居中位置
        const rect = modal.getBoundingClientRect();
        let nextTop = Math.max(24, (window.innerHeight - rect.height) / 2);
        let nextLeft = Math.max(24, (window.innerWidth - rect.width) / 2);
        setPosition({ top: nextTop, left: nextLeft });
    }, [open, storageKey]);

    const onMouseDown = (event) => {
        if (event.button !== 0) return;
        if (event.target.closest("button")) return;
        const modal = modalRef.current;
        if (!modal) return;
        const rect = modal.getBoundingClientRect();
        dragState.current = {
            offsetX: event.clientX - rect.left,
            offsetY: event.clientY - rect.top
        };

        const handleMove = (moveEvent) => {
            if (!dragState.current) return;
            const bounds = modal.getBoundingClientRect();
            const maxLeft = window.innerWidth - bounds.width - 12;
            const maxTop = window.innerHeight - bounds.height - 12;
            let nextLeft = moveEvent.clientX - dragState.current.offsetX;
            let nextTop = moveEvent.clientY - dragState.current.offsetY;
            nextLeft = Math.min(Math.max(12, nextLeft), Math.max(12, maxLeft));
            nextTop = Math.min(Math.max(12, nextTop), Math.max(12, maxTop));
            dragState.current.last = { top: nextTop, left: nextLeft };
            setPosition({ top: nextTop, left: nextLeft });
            savePosition({ top: nextTop, left: nextLeft });
        };

        const handleUp = () => {
            const last = dragState.current?.last;
            dragState.current = null;
            const payload = last || position;
            savePosition({ top: payload.top, left: payload.left });
            document.removeEventListener("mousemove", handleMove);
            document.removeEventListener("mouseup", handleUp);
        };

        document.addEventListener("mousemove", handleMove);
        document.addEventListener("mouseup", handleUp);
    };

    return { modalRef, position, setPosition, onMouseDown };
}
