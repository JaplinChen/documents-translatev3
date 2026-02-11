import React, { useState, useRef, useEffect, useLayoutEffect } from 'react';
import { useTranslation } from "react-i18next";
import { getOptionLabel } from "../../utils/appHelpers";
import { createPortal } from 'react-dom';

/**
 * CustomSelect - 專業級自定義下拉選單 (Portal 版本)
 * 使用 ReactDOM.createPortal 將選單清單渲染至 body，徹底解決 overflow: hidden 的裁剪問題。
 */
export function CustomSelect({ options = [], value, onChange, className = "", placeholder = "", testId = "" }) {
    const { t } = useTranslation();
    const [isOpen, setIsOpen] = useState(false);
    const [coords, setCoords] = useState({ top: 0, left: 0, width: 0 });
    const containerRef = useRef(null);
    const dropdownRef = useRef(null);

    // 點擊外部自動收合
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target) &&
                dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // 動態計算選單位置
    const updateCoords = () => {
        if (containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            setCoords({
                top: rect.bottom + window.scrollY,
                left: rect.left + window.scrollX,
                width: rect.width
            });
        }
    };

    useLayoutEffect(() => {
        if (isOpen) {
            updateCoords();
            window.addEventListener('scroll', updateCoords, true);
            window.addEventListener('resize', updateCoords);
        }
        return () => {
            window.removeEventListener('scroll', updateCoords, true);
            window.removeEventListener('resize', updateCoords);
        };
    }, [isOpen]);

    useLayoutEffect(() => {
        if (!isOpen || !dropdownRef.current) return;
        const el = dropdownRef.current;
        el.style.top = `${coords.top}px`;
        el.style.left = `${coords.left}px`;
        el.style.minWidth = `${Math.max(160, coords.width)}px`;
        el.style.zIndex = '9999';
    }, [isOpen, coords.top, coords.left, coords.width]);

    const selectedOption = options.find(opt => opt.value === value) || options.find(opt => opt.code === value);

    const dropdownList = (
        <ul
            className="custom-select-options portal-dropdown"
            ref={dropdownRef}
            data-testid={testId ? `${testId}-options` : undefined}
        >
            {options.map((opt, index) => {
                const optValue = opt.value || opt.code;
                const isSelected = optValue === value;
                return (
                    <li
                        key={index}
                        className={`custom-option ${isSelected ? 'is-selected' : ''}`}
                        data-testid={testId ? `${testId}-option-${optValue}` : undefined}
                        onClick={() => {
                            onChange({ target: { value: optValue } });
                            setIsOpen(false);
                        }}
                    >
                        {getOptionLabel(t, opt)}
                    </li>
                );
            })}
        </ul>
    );

    return (
        <div className={`custom-select-container ${className}`} ref={containerRef} data-testid={testId || undefined}>
            <div
                className={`custom-select-trigger ${isOpen ? 'is-active' : ''}`}
                data-testid={testId ? `${testId}-trigger` : undefined}
                onClick={() => setIsOpen(!isOpen)}
            >
                <span className="selected-text">
                    {selectedOption ? getOptionLabel(t, selectedOption) : (placeholder || t("common.select_placeholder"))}
                </span>
                <span className={`custom-select-arrow ${isOpen ? 'is-rotated' : ''}`}>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                </span>
            </div>

            {isOpen && createPortal(dropdownList, document.body)}
        </div>
    );
}
