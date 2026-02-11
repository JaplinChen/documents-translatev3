import { buildApiUrl, getJson } from './core';

export async function fetchHistoryItems(): Promise<{ items: unknown[] }> {
    return getJson<{ items: unknown[] }>('/api/pptx/history');
}

export async function fetchHistoryFile(
    filename: string,
    fileType: 'docx' | 'pptx'
): Promise<File> {
    const encoded = encodeURIComponent(filename);
    const response = await fetch(buildApiUrl(`/api/${fileType}/download/${encoded}`));
    if (!response.ok) {
        throw new Error('Download failed');
    }
    const blob = await response.blob();
    const mimeType =
        fileType === 'docx'
            ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            : 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
    return new File([blob], filename, { type: mimeType });
}
