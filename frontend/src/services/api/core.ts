export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || '';
const NETWORK_RETRY_COUNT = 2;
const NETWORK_RETRY_DELAY_MS = 250;

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
            // 無法解析 JSON
        }

        let message = `API Error: ${response.status}`;
        if (response.status === 502) {
            message = '伺服器網關錯誤 (502)，請檢查後端服務是否正常啟動。';
        } else if (response.status === 504) {
            message = '服務回應逾時 (504)，請稍後再試。';
        }

        throw new ApiClientError(message, response.status, detail);
    }
    return response.json();
}

function buildJsonHeaders(extra?: HeadersInit): HeadersInit {
    return {
        'Content-Type': 'application/json',
        ...(extra ?? {}),
    };
}

function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetriableNetworkError(error: unknown): boolean {
    if (!(error instanceof Error)) return false;
    const message = (error.message || '').toLowerCase();
    return (
        error.name === 'TypeError' ||
        message.includes('failed to fetch') ||
        message.includes('networkerror') ||
        message.includes('err_connection_refused')
    );
}

async function fetchWithRetry(
    url: string,
    init: RequestInit,
    retries = NETWORK_RETRY_COUNT
): Promise<Response> {
    let attempt = 0;
    while (true) {
        try {
            return await fetch(url, init);
        } catch (error) {
            if (!isRetriableNetworkError(error) || attempt >= retries) {
                throw error;
            }
            attempt += 1;
            await sleep(NETWORK_RETRY_DELAY_MS * attempt);
        }
    }
}

async function requestJson<T>(
    path: string,
    init: RequestInit
): Promise<T> {
    const response = await fetchWithRetry(`${API_BASE_URL}${path}`, init);
    return handleResponse<T>(response);
}

export async function getJson<T>(path: string): Promise<T> {
    return requestJson<T>(path, { method: 'GET' });
}

export async function postJson<T>(path: string, body?: unknown): Promise<T> {
    const init: RequestInit = { method: 'POST' };
    if (body !== undefined) {
        init.headers = buildJsonHeaders();
        init.body = JSON.stringify(body);
    }
    return requestJson<T>(path, init);
}

export async function putJson<T>(path: string, body?: unknown): Promise<T> {
    const init: RequestInit = { method: 'PUT' };
    if (body !== undefined) {
        init.headers = buildJsonHeaders();
        init.body = JSON.stringify(body);
    }
    return requestJson<T>(path, init);
}

export async function patchJson<T>(path: string, body?: unknown): Promise<T> {
    const init: RequestInit = { method: 'PATCH' };
    if (body !== undefined) {
        init.headers = buildJsonHeaders();
        init.body = JSON.stringify(body);
    }
    return requestJson<T>(path, init);
}

export async function deleteJson<T>(path: string, body?: unknown): Promise<T> {
    const init: RequestInit = { method: 'DELETE' };
    if (body !== undefined) {
        init.headers = buildJsonHeaders();
        init.body = JSON.stringify(body);
    }
    return requestJson<T>(path, init);
}

export async function postText<T>(
    path: string,
    text: string,
    contentType = 'text/plain'
): Promise<T> {
    return requestJson<T>(path, {
        method: 'POST',
        headers: { 'Content-Type': contentType },
        body: text,
    });
}

export async function getText(path: string): Promise<string> {
    const response = await fetchWithRetry(`${API_BASE_URL}${path}`, { method: 'GET' });
    if (!response.ok) {
        throw new ApiClientError('Request failed', response.status);
    }
    return response.text();
}

export async function postJsonBlob(
    path: string,
    body: unknown
): Promise<Blob> {
    const response = await fetchWithRetry(`${API_BASE_URL}${path}`, {
        method: 'POST',
        headers: buildJsonHeaders(),
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        throw new ApiClientError('Request failed', response.status);
    }
    return response.blob();
}

export function buildApiUrl(path: string): string {
    if (!path) return API_BASE_URL;
    if (path.startsWith('http://') || path.startsWith('https://')) return path;
    if (path.startsWith('/')) return `${API_BASE_URL}${path}`;
    return `${API_BASE_URL}/${path}`;
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

export async function postForm<T>(
    path: string,
    params: Record<string, unknown>
): Promise<T> {
    const formData = createFormData(params);
    const response = await fetchWithRetry(`${API_BASE_URL}${path}`, {
        method: 'POST',
        body: formData,
    });
    return handleResponse<T>(response);
}

export async function postFile<T>(
    path: string,
    file: File,
    fieldName = 'file'
): Promise<T> {
    const formData = new FormData();
    formData.append(fieldName, file);
    const response = await fetchWithRetry(`${API_BASE_URL}${path}`, {
        method: 'POST',
        body: formData,
    });
    return handleResponse<T>(response);
}

export async function getBlob(path: string): Promise<Blob> {
    const response = await fetchWithRetry(`${API_BASE_URL}${path}`, { method: 'GET' });
    if (!response.ok) {
        throw new ApiClientError('Download failed', response.status);
    }
    return response.blob();
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
}
