export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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

export async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let detail = response.statusText;
        try {
            const errorData = await response.json();
            detail = errorData?.detail || detail;
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

export function createFormData(params: Record<string, unknown>): FormData {
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

export function startJsonLineStream<T>(
    url: string,
    formData: FormData,
    onEvent: (event: T) => void,
    onError?: (error: Error) => void
): { abort: () => void } {
    const controller = new AbortController();

    fetch(url, {
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
                const lines = buffer.split('
');
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
}
