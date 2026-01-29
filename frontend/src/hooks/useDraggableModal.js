import { useLayoutEffect, useRef, useState } from "react";

/**
 * Custom hook for draggable modal positioning
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
