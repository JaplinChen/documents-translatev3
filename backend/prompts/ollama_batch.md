Translate each text block into {target_language_label}.
If a block contains [SOURCE_TEXT: ...], use it as the semantic reference to correct [EXISTING_TRANSLATION: ...].

CRITICAL INSTRUCTIONS:
- Output language MUST be {target_language_label} (code: {target_language_code})
- DO NOT output any other languages.
- For bilingual pairs, provide the optimized/corrected version of the translation.
{language_hint}

{language_guard}

EXAMPLE (follow this format exactly):
Input:
<<<BLOCK:0>>>
企業解決方案
<<<END>>>

Output:
{language_example}

Now translate the following:
{blocks}
