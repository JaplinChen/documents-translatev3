export const handleExport = (path) => window.open(path, '_blank');

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
    fetch(path, { method: 'POST', body: formData }).then(() => reload());
    event.target.value = '';
};
