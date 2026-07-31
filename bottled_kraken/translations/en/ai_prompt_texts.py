EN_AI_PROMPT_TEXTS_TRANSLATIONS = {
    'ai_prompt_export_orientation_portrait': (
        'The target document will be exported in portrait orientation (A4 portrait). Plan the number of columns and column widths for a tall, narrow page.'
    ),
    'ai_prompt_export_orientation_landscape': (
        'The target document will be exported in landscape orientation (A4 landscape). There is more horizontal space available for columns.'
    ),
    'ai_prompt_export_zones_user_compact': (
        '/no_think\n'
        'Immediately return final JSON only. No analysis, no thinking text, no explanation.\n'
        'Create a table exclusively from candidates_from_selected_zones_only.\n'
        'The page image may only serve as reading context. Do not export any row that is not in the candidates.\n'
        'Use only these JSON keys: {0}.\n'
        'Columns: {1}\n'
        'Rules:\n'
        '- Each candidate n is at most one table row. Never merge or duplicate candidates.\n'
        '- Values from cells are already assigned to the drawn selection zones; stick to that.\n'
        '- If unknown exists as a column: only write real text from cells.unknown, never the word Unknown as a placeholder.\n'
        '- heading and subheading are normal free text columns, but not an instruction to create additional data rows.\n'
        '- Leave missing or uncertain cells empty.\n'
        '- Answer format exactly: {{"rows":[{{...}}]}}.\n'
        'Context:\n{2}\n/no_think'
    ),
    'ai_prompt_export_zones_system': (
        'You are a table extractor. Without analysis, immediately return valid JSON only in the format {{"rows":[{{...}}]}}. No markdown, no explanation, no processing notes. Use real register entries only. Ignore page headers, headings, separators, and decorative marks. Each output row must represent exactly one visual register row; never merge several OCR candidates into one table cell. Fill unknown only when that column has a real row value; never fill it with the whole original line.'
    ),
    'ai_prompt_export_zones_user': (
        """Create a table from the page image, overlay boxes, defined export zones, and OCR candidates for the whole page.
Use only these keys: {}.
Columns: {}
The context contains zones, overlay_boxes, and candidates: {}
Rules:
- Defined zones are column/field templates. Their x-range and data type apply to the whole page, not only to the drawn height.
- Use overlay boxes and candidates line by line from top to bottom. Values on the same visual y-line belong together.
- A candidate row contains fragments with x/y position, type_hint, and OCR text. type_hint is only a hint; correct it using the image and zones when needed.
- Output only register/person entries. Skip page headers, page numbers, section headings, table lines, separator lines, and empty ornament rows as output rows.
- Use headings/years only as context for following entries when they clearly match.
- Leave uncertain cells empty; do not invent information.
- Preserve historical spelling.
Reply only with a JSON object: {{"rows":[{{...}}]}}."""
    ),
}
