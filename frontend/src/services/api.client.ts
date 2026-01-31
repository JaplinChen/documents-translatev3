/**
 * API Client - 統一的 API 呼叫函數
 *
 * 此檔案由 /ui-ship 流水線自動生成
 * 根據 backend/api/ 目錄的 API 端點定義
 *
 * 特性：
 * - 統一錯誤處理
 * - TypeScript 型別安全
 * - SSE 串流支援
 * - FormData 自動處理
 */

import type {
    ApiError,
    DocxApplyParams,
    DocxApplyResponse,
    DocxExtractResponse,
    ExportFormatsResponse,
    ExportRequest,
    GlossaryEntry,
    GlossaryResponse,
    LlmModelsParams,
    LlmModelsResponse,
    MemoryEntry,
    MemoryResponse,
    OcrSettings,
    PdfApplyParams,
    PdfApplyResponse,
    PdfExtractResponse,
    PptxApplyParams,
    PptxApplyResponse,
    PptxExtractGlossaryResponse,
    PptxExtractResponse,
    PptxHistoryResponse,
    PptxLanguagesResponse,
    PptxTranslateParams,
    PreserveTerm,
    PreserveTermBatchRequest,
    PreserveTermBatchResponse,
    PreserveTermsResponse,
    PromptContent,
    StyleSuggestRequest,
    StyleSuggestResponse,
    SuggestTermsResponse,
    TermBatchPayload,
    TermCategory,
    TermCategoryResponse,
    TermImportPreviewResponse,
    TermImportResponse,
    TermItem,
    TermListParams,
    TermListResponse,
    TermPayload,
    TextBlock,
    TmCategory,
    TmCategoryResponse,
    TokenEstimateResponse,
    TokenRecordRequest,
    TokenStatsResponse,
    TranslateProgressEvent,
    XlsxApplyParams,
    XlsxApplyResponse,
    XlsxExtractResponse,
    ConvertToGlossaryRequest,
    BatchDeleteRequest,
} from './api.types';

// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// =============================================================================
// Error Handling
// =============================================================================

export class ApiClientError extends Error {
    constructor(
        message: string,
        public statusCode: number,
        public detail?: string
    ) {
        super(message);
        this.name = 'ApiClientError';
    }
}

/**
 * 統一錯誤處理函數
 */
async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let detail = response.statusText;
        try {
            const errorData: ApiError = await response.json();
            detail = errorData.detail || detail;
        } catch {
            // 無法解析 JSON，使用預設錯誤訊息
        }
        throw new ApiClientError(
            `API Error: ${response.status}`,
            response.status,
            detail
        );
    }
    return response.json();
}

/**
 * 建立 FormData
 */
function createFormData(params: Record<string, unknown>): FormData {
    const formData = new FormData();
    Object.entries(params).forEach(([key, value]) => {
        if (value === undefined || value === null) return;
        if (value instanceof File) {
            formData.append(key, value);
        } else if (typeof value === 'boolean') {
            formData.append(key, value.toString());
        } else if (typeof value === 'object') {
            formData.append(key, JSON.stringify(value));
        } else {
            formData.append(key, String(value));
        }
    });
    return formData;
}

// =============================================================================
// PPTX API
// =============================================================================

export const pptxApi = {
    /**
     * 提取 PPTX 內容
     */
    async extract(file: File): Promise<PptxExtractResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/pptx/extract`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PptxExtractResponse>(response);
    },

    /**
     * 偵測語言
     */
    async languages(file: File): Promise<PptxLanguagesResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/pptx/languages`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PptxLanguagesResponse>(response);
    },

    /**
     * 套用翻譯
     */
    async apply(params: PptxApplyParams): Promise<PptxApplyResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/pptx/apply`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PptxApplyResponse>(response);
    },

    /**
     * 下載檔案（返回 Blob）
     */
    async download(filename: string): Promise<Blob> {
        const response = await fetch(
            `${API_BASE_URL}/api/pptx/download/${encodeURIComponent(filename)}`
        );
        if (!response.ok) {
            throw new ApiClientError('Download failed', response.status);
        }
        return response.blob();
    },

    /**
     * 取得歷史紀錄
     */
    async history(): Promise<PptxHistoryResponse> {
        const response = await fetch(`${API_BASE_URL}/api/pptx/history`);
        return handleResponse<PptxHistoryResponse>(response);
    },

    /**
     * 刪除歷史紀錄
     */
    async deleteHistory(filename: string): Promise<{ status: string }> {
        const response = await fetch(
            `${API_BASE_URL}/api/pptx/history/${encodeURIComponent(filename)}`,
            { method: 'DELETE' }
        );
        return handleResponse<{ status: string }>(response);
    },

    /**
     * 翻譯（非串流）
     */
    async translate(
        params: PptxTranslateParams
    ): Promise<{ results: TextBlock[] }> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/pptx/translate`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<{ results: TextBlock[] }>(response);
    },

    /**
     * 翻譯（SSE 串流）
     * @returns EventSource 物件，需手動關閉
     */
    translateStream(
        params: PptxTranslateParams,
        onEvent: (event: TranslateProgressEvent) => void,
        onError?: (error: Error) => void
    ): { abort: () => void } {
        const formData = createFormData(params);

        const controller = new AbortController();

        fetch(`${API_BASE_URL}/api/pptx/translate-stream`, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
        })
            .then(async (response) => {
                if (!response.ok) {
                    throw new ApiClientError('Stream failed', response.status);
                }
                const reader = response.body?.getReader();
                if (!reader) throw new Error('No response body');

                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                onEvent(data);
                            } catch {
                                // 忽略解析錯誤
                            }
                        }
                    }
                }
            })
            .catch((error) => {
                if (error.name !== 'AbortError') {
                    onError?.(error);
                }
            });

        return { abort: () => controller.abort() };
    },

    /**
     * 提取詞彙
     */
    async extractGlossary(
        blocks: string,
        targetLanguage: string = 'zh-TW',
        options?: {
            provider?: string;
            model?: string;
            api_key?: string;
            base_url?: string;
        }
    ): Promise<PptxExtractGlossaryResponse> {
        const formData = createFormData({
            blocks,
            target_language: targetLanguage,
            ...options,
        });
        const response = await fetch(`${API_BASE_URL}/api/pptx/extract-glossary`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PptxExtractGlossaryResponse>(response);
    },
};

// =============================================================================
// DOCX API
// =============================================================================

export const docxApi = {
    /**
     * 提取 DOCX 內容
     */
    async extract(file: File): Promise<DocxExtractResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/docx/extract`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<DocxExtractResponse>(response);
    },

    /**
     * 套用翻譯
     */
    async apply(params: DocxApplyParams): Promise<DocxApplyResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/docx/apply`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<DocxApplyResponse>(response);
    },

    /**
     * 下載檔案
     */
    async download(filename: string): Promise<Blob> {
        const response = await fetch(
            `${API_BASE_URL}/api/docx/download/${encodeURIComponent(filename)}`
        );
        if (!response.ok) {
            throw new ApiClientError('Download failed', response.status);
        }
        return response.blob();
    },

    /**
     * 取得歷史紀錄
     */
    async history(): Promise<{ items: unknown[] }> {
        const response = await fetch(`${API_BASE_URL}/api/docx/history`);
        return handleResponse<{ items: unknown[] }>(response);
    },

    /**
     * 刪除歷史紀錄
     */
    async deleteHistory(filename: string): Promise<{ status: string }> {
        const response = await fetch(
            `${API_BASE_URL}/api/docx/history/${encodeURIComponent(filename)}`,
            { method: 'DELETE' }
        );
        return handleResponse<{ status: string }>(response);
    },

    /**
     * 翻譯（SSE 串流）
     */
    translateStream(
        params: PptxTranslateParams,
        onEvent: (event: TranslateProgressEvent) => void,
        onError?: (error: Error) => void
    ): { abort: () => void } {
        const formData = createFormData(params);
        const controller = new AbortController();

        fetch(`${API_BASE_URL}/api/docx/translate-stream`, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
        })
            .then(async (response) => {
                if (!response.ok) {
                    throw new ApiClientError('Stream failed', response.status);
                }
                const reader = response.body?.getReader();
                if (!reader) throw new Error('No response body');

                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                onEvent(data);
                            } catch {
                                // 忽略解析錯誤
                            }
                        }
                    }
                }
            })
            .catch((error) => {
                if (error.name !== 'AbortError') {
                    onError?.(error);
                }
            });

        return { abort: () => controller.abort() };
    },
};

// =============================================================================
// PDF API
// =============================================================================

export const pdfApi = {
    /**
     * 提取 PDF 內容
     */
    async extract(file: File): Promise<PdfExtractResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/pdf/extract`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PdfExtractResponse>(response);
    },

    /**
     * 套用翻譯
     */
    async apply(params: PdfApplyParams): Promise<PdfApplyResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/pdf/apply`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PdfApplyResponse>(response);
    },

    /**
     * 下載檔案
     */
    async download(filename: string): Promise<Blob> {
        const response = await fetch(
            `${API_BASE_URL}/api/pdf/download/${encodeURIComponent(filename)}`
        );
        if (!response.ok) {
            throw new ApiClientError('Download failed', response.status);
        }
        return response.blob();
    },

    /**
     * 翻譯（SSE 串流）
     */
    translateStream(
        params: PptxTranslateParams,
        onEvent: (event: TranslateProgressEvent) => void,
        onError?: (error: Error) => void
    ): { abort: () => void } {
        const formData = createFormData(params);
        const controller = new AbortController();

        fetch(`${API_BASE_URL}/api/pdf/translate-stream`, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
        })
            .then(async (response) => {
                if (!response.ok) {
                    throw new ApiClientError('Stream failed', response.status);
                }
                const reader = response.body?.getReader();
                if (!reader) throw new Error('No response body');

                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                onEvent(data);
                            } catch {
                                // 忽略解析錯誤
                            }
                        }
                    }
                }
            })
            .catch((error) => {
                if (error.name !== 'AbortError') {
                    onError?.(error);
                }
            });

        return { abort: () => controller.abort() };
    },
};

// =============================================================================
// XLSX API
// =============================================================================

export const xlsxApi = {
    /**
     * 提取 XLSX 內容
     */
    async extract(file: File): Promise<XlsxExtractResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/xlsx/extract`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<XlsxExtractResponse>(response);
    },

    /**
     * 套用翻譯
     */
    async apply(params: XlsxApplyParams): Promise<XlsxApplyResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/xlsx/apply`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<XlsxApplyResponse>(response);
    },

    /**
     * 下載檔案
     */
    async download(filename: string): Promise<Blob> {
        const response = await fetch(
            `${API_BASE_URL}/api/xlsx/download/${encodeURIComponent(filename)}`
        );
        if (!response.ok) {
            throw new ApiClientError('Download failed', response.status);
        }
        return response.blob();
    },

    /**
     * 翻譯（SSE 串流）
     */
    translateStream(
        params: PptxTranslateParams,
        onEvent: (event: TranslateProgressEvent) => void,
        onError?: (error: Error) => void
    ): { abort: () => void } {
        const formData = createFormData(params);
        const controller = new AbortController();

        fetch(`${API_BASE_URL}/api/xlsx/translate-stream`, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
        })
            .then(async (response) => {
                if (!response.ok) {
                    throw new ApiClientError('Stream failed', response.status);
                }
                const reader = response.body?.getReader();
                if (!reader) throw new Error('No response body');

                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                onEvent(data);
                            } catch {
                                // 忽略解析錯誤
                            }
                        }
                    }
                }
            })
            .catch((error) => {
                if (error.name !== 'AbortError') {
                    onError?.(error);
                }
            });

        return { abort: () => controller.abort() };
    },
};

// =============================================================================
// LLM API
// =============================================================================

export const llmApi = {
    /**
     * 取得模型列表
     */
    async models(params: LlmModelsParams): Promise<LlmModelsResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/llm/models`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<LlmModelsResponse>(response);
    },
};

// =============================================================================
// Export API
// =============================================================================

export const exportApi = {
    /**
     * 取得匯出格式列表
     */
    async formats(): Promise<ExportFormatsResponse> {
        const response = await fetch(`${API_BASE_URL}/api/export-formats`);
        return handleResponse<ExportFormatsResponse>(response);
    },

    /**
     * 匯出為 DOCX
     */
    async toDocx(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/docx`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    /**
     * 匯出為 XLSX
     */
    async toXlsx(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/xlsx`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    /**
     * 匯出為 TXT
     */
    async toTxt(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/txt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    /**
     * 匯出為 Markdown
     */
    async toMd(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/md`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    /**
     * 匯出為 PDF
     */
    async toPdf(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    /**
     * 術語建議
     */
    async suggestTerms(blocks: TextBlock[]): Promise<SuggestTermsResponse> {
        const response = await fetch(`${API_BASE_URL}/api/suggest-terms`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ blocks }),
        });
        return handleResponse<SuggestTermsResponse>(response);
    },
};

// =============================================================================
// Translation Memory API
// =============================================================================

export const tmApi = {
    /**
     * 初始化資料
     */
    async seed(): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/seed`, {
            method: 'POST',
        });
        return handleResponse<{ status: string }>(response);
    },

    // --- Glossary ---

    /**
     * 取得詞彙表
     */
    async getGlossary(limit: number = 200): Promise<GlossaryResponse> {
        const response = await fetch(
            `${API_BASE_URL}/api/tm/glossary?limit=${limit}`
        );
        return handleResponse<GlossaryResponse>(response);
    },

    /**
     * 新增/更新詞彙
     */
    async upsertGlossary(entry: GlossaryEntry): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry),
        });
        return handleResponse<{ status: string }>(response);
    },

    /**
     * 批次新增詞彙
     */
    async batchUpsertGlossary(
        entries: GlossaryEntry[]
    ): Promise<{ status: string; count: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entries),
        });
        return handleResponse<{ status: string; count: number }>(response);
    },

    /**
     * 刪除詞彙
     */
    async deleteGlossary(id: number): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id }),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    /**
     * 批次刪除詞彙
     */
    async batchDeleteGlossary(ids: number[]): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/batch`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids }),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    /**
     * 清空詞彙表
     */
    async clearGlossary(): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/clear`, {
            method: 'DELETE',
        });
        return handleResponse<{ deleted: number }>(response);
    },

    /**
     * 匯入詞彙
     */
    async importGlossary(
        file: File
    ): Promise<{ status: string; count: number }> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/import`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<{ status: string; count: number }>(response);
    },

    /**
     * 匯出詞彙（返回 CSV 文字）
     */
    async exportGlossary(): Promise<string> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/export`);
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.text();
    },

    // --- Memory ---

    /**
     * 取得翻譯記憶
     */
    async getMemory(limit: number = 200): Promise<MemoryResponse> {
        const response = await fetch(
            `${API_BASE_URL}/api/tm/memory?limit=${limit}`
        );
        return handleResponse<MemoryResponse>(response);
    },

    /**
     * 新增/更新記憶
     */
    async upsertMemory(entry: MemoryEntry): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry),
        });
        return handleResponse<{ status: string }>(response);
    },

    /**
     * 刪除記憶
     */
    async deleteMemory(id: number): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id }),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    /**
     * 批次刪除記憶
     */
    async batchDeleteMemory(ids: number[]): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory/batch`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids }),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    /**
     * 清空記憶
     */
    async clearMemory(): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory/clear`, {
            method: 'DELETE',
        });
        return handleResponse<{ deleted: number }>(response);
    },

    /**
     * 匯入記憶
     */
    async importMemory(file: File): Promise<{ status: string; count: number }> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/tm/memory/import`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<{ status: string; count: number }>(response);
    },

    /**
     * 匯出記憶（返回 CSV 文字）
     */
    async exportMemory(): Promise<string> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory/export`);
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.text();
    },

    // --- Categories ---

    /**
     * 取得分類列表
     */
    async getCategories(): Promise<TmCategoryResponse> {
        const response = await fetch(`${API_BASE_URL}/api/tm/categories`);
        return handleResponse<TmCategoryResponse>(response);
    },

    /**
     * 新增分類
     */
    async createCategory(
        name: string,
        sortOrder?: number
    ): Promise<{ item: TmCategory }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/categories`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, sort_order: sortOrder ?? 0 }),
        });
        return handleResponse<{ item: TmCategory }>(response);
    },

    /**
     * 更新分類
     */
    async updateCategory(
        id: number,
        name: string,
        sortOrder?: number
    ): Promise<{ item: TmCategory }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/categories/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, sort_order: sortOrder ?? 0 }),
        });
        return handleResponse<{ item: TmCategory }>(response);
    },

    /**
     * 刪除分類
     */
    async deleteCategory(id: number): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/categories/${id}`, {
            method: 'DELETE',
        });
        return handleResponse<{ status: string }>(response);
    },
};

// =============================================================================
// Terms API
// =============================================================================

export const termsApi = {
    /**
     * 取得術語列表
     */
    async list(params?: TermListParams): Promise<TermListResponse> {
        const searchParams = new URLSearchParams();
        if (params) {
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                    searchParams.append(key, String(value));
                }
            });
        }
        const query = searchParams.toString();
        const response = await fetch(
            `${API_BASE_URL}/api/terms${query ? `?${query}` : ''}`
        );
        return handleResponse<TermListResponse>(response);
    },

    /**
     * 新增術語
     */
    async create(payload: TermPayload): Promise<{ item: TermItem }> {
        const response = await fetch(`${API_BASE_URL}/api/terms`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return handleResponse<{ item: TermItem }>(response);
    },

    /**
     * 更新術語
     */
    async update(id: number, payload: TermPayload): Promise<{ item: TermItem }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return handleResponse<{ item: TermItem }>(response);
    },

    /**
     * 刪除術語
     */
    async delete(id: number): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/${id}`, {
            method: 'DELETE',
        });
        return handleResponse<{ status: string }>(response);
    },

    /**
     * 取得版本歷史
     */
    async versions(id: number): Promise<{ versions: unknown[] }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/${id}/versions`);
        return handleResponse<{ versions: unknown[] }>(response);
    },

    /**
     * 批次更新
     */
    async batchUpdate(payload: TermBatchPayload): Promise<{ updated: number }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return handleResponse<{ updated: number }>(response);
    },

    /**
     * 批次刪除
     */
    async batchDelete(payload: BatchDeleteRequest): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/batch`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    /**
     * 同步所有資料
     */
    async syncAll(): Promise<{ synced: number }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/sync-all`, {
            method: 'POST',
        });
        return handleResponse<{ synced: number }>(response);
    },

    // --- Categories ---

    /**
     * 取得分類列表
     */
    async getCategories(): Promise<TermCategoryResponse> {
        const response = await fetch(`${API_BASE_URL}/api/terms/categories`);
        return handleResponse<TermCategoryResponse>(response);
    },

    /**
     * 新增分類
     */
    async createCategory(
        name: string,
        sortOrder?: number
    ): Promise<{ item: TermCategory }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/categories`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, sort_order: sortOrder }),
        });
        return handleResponse<{ item: TermCategory }>(response);
    },

    /**
     * 更新分類
     */
    async updateCategory(
        id: number,
        name: string,
        sortOrder?: number
    ): Promise<{ item: TermCategory }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/categories/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, sort_order: sortOrder }),
        });
        return handleResponse<{ item: TermCategory }>(response);
    },

    /**
     * 刪除分類
     */
    async deleteCategory(id: number): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/categories/${id}`, {
            method: 'DELETE',
        });
        return handleResponse<{ status: string }>(response);
    },

    // --- Import/Export ---

    /**
     * 匯入預覽
     */
    async importPreview(
        file: File,
        mapping?: Record<string, string>
    ): Promise<TermImportPreviewResponse> {
        const formData = new FormData();
        formData.append('file', file);
        if (mapping) {
            formData.append('mapping', JSON.stringify(mapping));
        }
        const response = await fetch(`${API_BASE_URL}/api/terms/import/preview`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<TermImportPreviewResponse>(response);
    },

    /**
     * 匯入術語
     */
    async import(
        file: File,
        mapping?: Record<string, string>
    ): Promise<TermImportResponse> {
        const formData = new FormData();
        formData.append('file', file);
        if (mapping) {
            formData.append('mapping', JSON.stringify(mapping));
        }
        const response = await fetch(`${API_BASE_URL}/api/terms/import`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<TermImportResponse>(response);
    },

    /**
     * 取得匯入錯誤
     */
    async importErrors(): Promise<{ errors: unknown[] }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/import/errors`);
        return handleResponse<{ errors: unknown[] }>(response);
    },

    /**
     * 匯出術語（返回 CSV 文字）
     */
    async export(): Promise<string> {
        const response = await fetch(`${API_BASE_URL}/api/terms/export`);
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.text();
    },
};

// =============================================================================
// Preserve Terms API
// =============================================================================

export const preserveTermsApi = {
    /**
     * 取得保留術語列表
     */
    async list(): Promise<PreserveTermsResponse> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms`);
        return handleResponse<PreserveTermsResponse>(response);
    },

    /**
     * 新增保留術語
     */
    async create(term: PreserveTerm): Promise<{ term: PreserveTerm }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(term),
        });
        return handleResponse<{ term: PreserveTerm }>(response);
    },

    /**
     * 批次新增
     */
    async batch(
        request: PreserveTermBatchRequest
    ): Promise<PreserveTermBatchResponse> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        return handleResponse<PreserveTermBatchResponse>(response);
    },

    /**
     * 更新保留術語
     */
    async update(
        id: string,
        term: PreserveTerm
    ): Promise<{ term: PreserveTerm }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(term),
        });
        return handleResponse<{ term: PreserveTerm }>(response);
    },

    /**
     * 刪除保留術語
     */
    async delete(id: string): Promise<{ deleted: boolean }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/${id}`, {
            method: 'DELETE',
        });
        return handleResponse<{ deleted: boolean }>(response);
    },

    /**
     * 清空所有
     */
    async deleteAll(): Promise<{ message: string }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms`, {
            method: 'DELETE',
        });
        return handleResponse<{ message: string }>(response);
    },

    /**
     * 匯出（返回 CSV 文字）
     */
    async export(): Promise<string> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/export`);
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.text();
    },

    /**
     * 匯入
     */
    async import(
        csvData: string
    ): Promise<{ imported: number; skipped: number; total: number }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'text/plain' },
            body: csvData,
        });
        return handleResponse<{
            imported: number;
            skipped: number;
            total: number;
        }>(response);
    },

    /**
     * 從詞彙表轉換
     */
    async convertFromGlossary(
        sourceText: string,
        category?: string,
        caseSensitive?: boolean
    ): Promise<{ term: PreserveTerm; message: string }> {
        const params = new URLSearchParams({ source_text: sourceText });
        if (category) params.append('category', category);
        if (caseSensitive !== undefined)
            params.append('case_sensitive', String(caseSensitive));

        const response = await fetch(
            `${API_BASE_URL}/api/preserve-terms/convert-from-glossary?${params}`,
            { method: 'POST' }
        );
        return handleResponse<{ term: PreserveTerm; message: string }>(response);
    },

    /**
     * 轉換至詞彙表
     */
    async convertToGlossary(
        request: ConvertToGlossaryRequest
    ): Promise<{ status: string; source_lang: string; target_lang: string }> {
        const response = await fetch(
            `${API_BASE_URL}/api/preserve-terms/convert-to-glossary`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
            }
        );
        return handleResponse<{
            status: string;
            source_lang: string;
            target_lang: string;
        }>(response);
    },
};

// =============================================================================
// Prompts API
// =============================================================================

export const promptsApi = {
    /**
     * 取得提示列表
     */
    async list(): Promise<string[]> {
        const response = await fetch(`${API_BASE_URL}/api/prompts`);
        return handleResponse<string[]>(response);
    },

    /**
     * 取得提示內容
     */
    async get(name: string): Promise<PromptContent> {
        const response = await fetch(
            `${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}`
        );
        return handleResponse<PromptContent>(response);
    },

    /**
     * 儲存提示
     */
    async save(name: string, content: string): Promise<{ status: string }> {
        const response = await fetch(
            `${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }),
            }
        );
        return handleResponse<{ status: string }>(response);
    },
};

// =============================================================================
// Style API
// =============================================================================

export const styleApi = {
    /**
     * 樣式建議
     */
    async suggest(request: StyleSuggestRequest): Promise<StyleSuggestResponse> {
        const response = await fetch(`${API_BASE_URL}/api/style/suggest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        return handleResponse<StyleSuggestResponse>(response);
    },
};

// =============================================================================
// OCR Settings API
// =============================================================================

export const ocrApi = {
    /**
     * 取得 OCR 設定
     */
    async getSettings(): Promise<OcrSettings> {
        const response = await fetch(`${API_BASE_URL}/api/ocr/settings`);
        return handleResponse<OcrSettings>(response);
    },

    /**
     * 更新 OCR 設定
     */
    async updateSettings(settings: OcrSettings): Promise<OcrSettings> {
        const response = await fetch(`${API_BASE_URL}/api/ocr/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings),
        });
        return handleResponse<OcrSettings>(response);
    },
};

// =============================================================================
// Token Stats API
// =============================================================================

export const tokenStatsApi = {
    /**
     * 取得統計
     */
    async get(): Promise<TokenStatsResponse> {
        const response = await fetch(`${API_BASE_URL}/api/token-stats`);
        return handleResponse<TokenStatsResponse>(response);
    },

    /**
     * 記錄使用量
     */
    async record(
        request: TokenRecordRequest
    ): Promise<{ recorded: boolean; usage: { total_tokens: number; estimated_cost_usd: number } }> {
        const params = new URLSearchParams({
            provider: request.provider,
            model: request.model,
            prompt_tokens: String(request.prompt_tokens),
            completion_tokens: String(request.completion_tokens),
        });
        if (request.operation) {
            params.append('operation', request.operation);
        }
        const response = await fetch(
            `${API_BASE_URL}/api/token-stats/record?${params}`,
            { method: 'POST' }
        );
        return handleResponse<{
            recorded: boolean;
            usage: { total_tokens: number; estimated_cost_usd: number };
        }>(response);
    },

    /**
     * 估算 Token
     */
    async estimate(
        text: string,
        provider: string = 'openai'
    ): Promise<TokenEstimateResponse> {
        const params = new URLSearchParams({ text, provider });
        const response = await fetch(
            `${API_BASE_URL}/api/token-stats/estimate?${params}`,
            { method: 'POST' }
        );
        return handleResponse<TokenEstimateResponse>(response);
    },
};

// =============================================================================
// Default Export
// =============================================================================

export default {
    pptx: pptxApi,
    docx: docxApi,
    pdf: pdfApi,
    xlsx: xlsxApi,
    llm: llmApi,
    export: exportApi,
    tm: tmApi,
    terms: termsApi,
    preserveTerms: preserveTermsApi,
    prompts: promptsApi,
    style: styleApi,
    ocr: ocrApi,
    tokenStats: tokenStatsApi,
};
