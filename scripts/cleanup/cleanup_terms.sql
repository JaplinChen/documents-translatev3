-- ============================================
-- 術語資料清理腳本
-- 清理 terms.db 和 translation_memory.db 中的問題資料
-- ============================================

-- === 1. 清理 terms.db ===

-- 刪除組合詞 (含有 +)
DELETE FROM terms WHERE term LIKE '%+%';

-- 刪除純版本號 (沒有品牌名的版本)
DELETE FROM terms WHERE term REGEXP '^[0-9]+ Pro$';
DELETE FROM terms WHERE term IN ('7 Pro', '10 Pro', '7 pro', '10 pro');

-- 刪除通用詞
DELETE FROM terms WHERE LOWER(term) IN (
    'no.', 'no', 'date of purchase', 'date', 'ram', 'ram (gb)', 
    'none', 'total', 'sum', 'status', 'summary', 'table', 'page',
    'index', 'note', 'name', 'type', 'size', 'price', 'quantity',
    'amount', 'description', 'item', 'unit', 'value', 'count',
    'number', 'month', 'year', 'day', 'week', 'time', 'file',
    'folder', 'document', 'report', 'list', 'data', 'info', 'detail'
);

-- 刪除規格描述 (含 GB, TB, GHz 等)
DELETE FROM terms WHERE term LIKE '%GB%' AND term LIKE '%SSD%';
DELETE FROM terms WHERE term LIKE '%TB%' AND term LIKE '%HDD%';
DELETE FROM terms WHERE term LIKE '%GHz%';

-- === 2. 顯示清理結果 ===
SELECT 'Terms remaining:' as info, COUNT(*) as count FROM terms;
