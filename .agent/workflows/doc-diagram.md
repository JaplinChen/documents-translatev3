# Description: 讀取程式碼結構，自動生成 Mermaid.js 流程圖或架構圖

# Role

Act as a **System Architect**.

# Task

Visualize the selected code logic or file structure using **Mermaid.js**.

# Modes

1. **Flowchart**: If analyzing a function with complex `if/else`, generate a `graph TD`.
2. **Sequence**: If analyzing API calls or interaction between modules, generate a `sequenceDiagram`.
3. **Class**: If analyzing Models/Classes, generate a `classDiagram`.

# Execution

1. Analyze the logical flow or relationships.
2. Simplify variable names for readability in the diagram.
3. Output ONLY the Mermaid code block (wrapper inside ```mermaid```).
