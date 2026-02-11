import { buildApiUrl } from '../../services/api/core';
import { tmApi } from '../../services/api/tm';

export const handleExport = (path) => window.open(buildApiUrl(path), '_blank');

export const handleImportFile = ({
    event,
    path,
    reload,
    isGlossary,
    setLastGlossaryAt,
    setLastMemoryAt,
}) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (isGlossary) setLastGlossaryAt(Date.now());
    else setLastMemoryAt(Date.now());
    const formData = new FormData();
    formData.append('file', file);
    const relativePath = path.startsWith('/api/') ? path : path.replace(/^https?:\/\/[^/]+/, '');
    const endpoint = relativePath.includes('/glossary/') ? 'glossary' : 'memory';
    const upload = endpoint === 'glossary' ? tmApi.importGlossary : tmApi.importMemory;
    upload(file).then(() => reload());
    event.target.value = '';
};
