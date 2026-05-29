BK_GEDCOM_PROMPT_DEFAULTS_EN = {
    'act_lm_generate_gedcom': 'GEDCOM file',
    'dlg_gedcom_title': 'GEDCOM file',
    'dlg_gedcom_notice': 'The recognized page will be analyzed by the local AI model. The model will try to create a GEDCOM file from it. Please review the result carefully in your genealogy software afterwards.',
    'msg_gedcom_started': 'GEDCOM generation started.',
    'msg_gedcom_done': 'GEDCOM file saved: {}',
    'msg_gedcom_cancelled': 'GEDCOM generation cancelled.',
    'msg_gedcom_failed': 'GEDCOM generation failed.',
    'log_gedcom_started': 'GEDCOM generation started: {}',
    'log_gedcom_done': 'GEDCOM generation finished: {}',
    'log_gedcom_failed': 'GEDCOM generation error: {} -> {}',
    'dlg_save_gedcom': 'Save GEDCOM file',
    'dlg_filter_gedcom': 'GEDCOM file (*.ged)',
    'warn_no_text_for_gedcom': 'There is no usable text for GEDCOM generation.',
    'lm_prompt_gedcom_system': 'GEDCOM – system prompt',
    'lm_prompt_gedcom_user': 'GEDCOM – user prompt',
    'ai_prompt_gedcom_system': (
        'You are a precise genealogy and GEDCOM assistant.\nYour task is to turn OCR text into a compatible GEDCOM file.\nCreate GEDCOM 5.5.1 in LINEAGE-LINKED format.\nUse UTF-8 and set CHAR UTF-8 in the header.\nReturn raw GEDCOM text only: no markdown, no explanation, no code fences.\nUse only information that is actually supported by the text. Do not invent people, dates, places, or relationships.\nCreate people as INDI records. Create FAM records only when a marriage, parent-child, or family relationship is clearly supported.\nIf birth, death, marriage, or place information is uncertain, store it as NOTE rather than as a fact.\nWhere possible, write names as GEDCOM NAME values with slashes around the surname, e.g. 1 NAME John /Miller/.\nIf the surname is uncertain, keep the name conservative and add a NOTE.\nUse stable IDs such as @I1@, @I2@ for individuals and @F1@, @F2@ for families.\nThe file must begin with 0 HEAD and end with 0 TRLR.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_gedcom_user': (
        'Create an importable GEDCOM file from the following OCR text.\n\nTechnical requirements:\n- GEDCOM version: 5.5.1\n- Header with: 0 HEAD, 1 SOUR BottledKraken, 1 GEDC, 2 VERS 5.5.1, 2 FORM LINEAGE-LINKED, 1 CHAR UTF-8\n- Individuals: 0 @I1@ INDI, 1 NAME ..., optional BIRT/DEAT/OCCU/RESI/NOTE only when supported\n- Families: 0 @F1@ FAM with HUSB/WIFE/CHIL only for clear relationships\n- Put source hints or uncertain readings into NOTE\n- No explanations outside the GEDCOM text\n\nOCR text:\n{}\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'lm_prompt_canonical_system': 'Canonical JSON – system prompt',
    'lm_prompt_canonical_user': 'Canonical JSON – user prompt',
    'ai_prompt_canonical_system': (
        'You are a JSON-only extraction engine for genealogical and historical OCR text. Return exactly one valid JSON object. No markdown, no explanations, no code fences. Extract only information supported by the OCR text.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_canonical_user': (
        'Create canonical_graph JSON from the following OCR text.\nUse exactly this structure:\n{schema_template}\n\nRules:\n- Entities: PERSON, PLACE, YEAR, AGE, EVENT, DOCUMENT, ENTITY.\n- Relations: RELATED_TO, LOCATED_IN, DURING, PART_OF, ASSOCIATED_WITH.\n- strength is a number from 0.0 to 1.0.\n- Use null for unknown values.\n- Return JSON only.\n\nOCR_TEXT_START\n{ocr_text}\nOCR_TEXT_END\n- Extract ages/age expressions (years, months, days) as AGE entities and as age attributes on PERSON nodes when possible.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_postgresql_system': (
        'You are an extraction assistant for OCR-derived historical or administrative texts. Return valid JSON only. No explanations, no markdown. Do not invent missing information.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_postgresql_user': (
        'Create a PostgreSQL-oriented JSON payload from the following text.\nReturn exactly one JSON object with these keys:\n{schema_template}\n\nText:\n{ocr_text}\n- Include age/age expressions when present in the source text.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_neo4j_system': (
        'You are a graph extraction assistant for OCR-derived texts. Return valid JSON only. Create only supported nodes and relationships. No explanations, no markdown.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_neo4j_user': (
        'Create a Neo4j-oriented graph JSON payload from the following text.\nReturn exactly one JSON object with these keys:\n{schema_template}\n\nText:\n{ocr_text}\n- Include age/age expressions when present in the source text.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_fullpage_lm_ocr_system': 'You are a precise OCR system. Return valid JSON only. Detect every text line separately in natural reading order. Ditto marks are only real quotation marks such as " or "" or -"-. Periods or dotted leaders are NOT ditto marks. A ditto mark means: copy the meaningful value from the same visual column in the previous line and write it out; never output the mark literally.',
    'ai_prompt_fullpage_lm_ocr_user': 'Run OCR for the complete visible document page. Ignore existing overlay boxes. Return JSON only: {"lines":[{"text":"..."}]}. Every detected entry must be its own line; do not merge entries into paragraphs. Ditto marks are only " / "" / -"-. Periods are not ditto marks. Replace ditto marks with the value from the same visual column in the previous line.',
    'lm_busy_default_message': 'The local model is working. Duration depends on the model, image size and page complexity. Please wait.',
    'lm_busy_revision_status': 'The local model is revising the lines. First the complete page is read as context, then three overlay boxes at a time are analyzed.',
    'ai_status_step0_fullpage_context': '1/3: Reading the complete page only as context: {}',
    'lm_prompt_sqlite_system': 'SQLite – system prompt',
    'lm_prompt_sqlite_user': 'SQLite – user prompt',
    'prompt_desc_sqlite_system': 'System instruction for local AI extraction of SQLite-compatible person and register data.',
    'prompt_desc_sqlite_user': 'User instruction for SQLite data: extracts persons, entries, ages, places, years and evidence into flat JSON tables.',
    'ai_prompt_sqlite_system': 'You are a precise extraction assistant. Return only valid JSON for an SQLite export. No Markdown explanation.',
    'ai_prompt_sqlite_user': (
        'Extract an SQLite-compatible structure from the OCR text with documents, persons and entries. Each detected person/registration should get its own record. Preserve names, ages, places, years, dates and original evidence. OCR text:\n{}'
),
    'busy_queue_ref': 'Queue #{}',
}
BK_GEDCOM_VISION_TEXTS_EN = {
    'dlg_gedcom_notice': 'The current page will be analyzed by the local AI model. The page image and any available OCR lines will be considered together. The result is a GEDCOM file that you should review in your genealogy software afterwards.',
    'msg_gedcom_started': 'GEDCOM generation started. Page image and OCR text are being analyzed.',
    'warn_gedcom_needs_text_or_image': 'GEDCOM generation needs a loaded page image or usable OCR text.',
    'log_gedcom_retry_text_only': 'GEDCOM: The model did not accept the image request. Retrying with OCR text only.',
    'ai_prompt_gedcom_system': (
        "You are a precise genealogy, archival, and GEDCOM assistant.\nYou analyze historical civil-register forms, church records, handwritten entries, and marginal notes.\nYour task is to create an importable GEDCOM file from the page image and optional OCR text.\n\nImportant for German civil-register forms:\n- Wording like 'appeared ... and reported that his wife ... gave birth to a child' usually describes a birth record.\n- The informant is often the father. The named wife is often the mother.\n- 'geborene' usually introduces the mother's maiden name.\n- If the child has not yet received given names, still create a child, use the parents' surname, set SEX if supported, and add a NOTE.\n- Dates and places from form fields may be used when readable. Mark uncertain readings as NOTE.\n\nGEDCOM rules:\n- Create GEDCOM 5.5.1 in LINEAGE-LINKED format.\n- Use UTF-8 and set CHAR UTF-8 in the header.\n- Return raw GEDCOM text only: no markdown, no explanation, no code fences.\n- The file must begin with 0 HEAD and end with 0 TRLR.\n- Use stable IDs such as @I1@, @I2@, @F1@, and @S1@.\n- Create people as INDI records. Create FAM records when parent-child, marriage, or family relationships are supported by the source.\n- Names should use 1 NAME Given /Surname/. If the given name is missing: 1 NAME /Surname/.\n- Use BIRT, DEAT, MARR, OCCU, RESI, NOTE, and SOUR only when supported or clearly marked as uncertain.\n- Do not invent people, dates, places, or relationships. If uncertain, write a NOTE rather than a hard fact.\n- If a genealogical person is visible, create at least one INDI record.\n\nImportant: A single"
        ' " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'ai_prompt_gedcom_user': (
        'Create an importable GEDCOM file from the following source.\n\nAnalyze the attached page image first. The OCR text is only a hint and may contain errors.\nIf image and OCR disagree, use the more plausible reading from the image and put uncertainty into NOTE.\n\nRequired minimum structure:\n0 HEAD\n1 SOUR BottledKraken\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n1 CHAR UTF-8\n...\n0 TRLR\n\nAlso create a SOUR record for the analyzed page where possible and cite it from people/families.\nFor birth records, create child, father, mother, and a FAM link when these details are visible.\n\nOCR text, if available:\n{}\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'lm_prompt_sqlite_system': 'SQLite – system prompt',
    'lm_prompt_sqlite_user': 'SQLite – user prompt',
    'prompt_desc_sqlite_system': 'System instruction for local AI extraction of SQLite-compatible person and register data.',
    'prompt_desc_sqlite_user': 'User instruction for SQLite data: extracts persons, entries, ages, places, years and evidence into flat JSON tables.',
    'ai_prompt_sqlite_system': 'You are a precise extraction assistant. Return only valid JSON for an SQLite export. No Markdown explanation.',
    'ai_prompt_sqlite_user': (
        'Extract an SQLite-compatible structure from the OCR text with documents, persons and entries. Each detected person/registration should get its own record. Preserve names, ages, places, years, dates and original evidence. OCR text:\n{}'
),
    'busy_queue_ref': 'Queue #{}',
}
BK_GEDCOM_SAVE_FIX_TEXTS_EN = {
    'warn_gedcom_no_output': 'The local model did not return usable GEDCOM text.',
    'warn_gedcom_no_person_records': (
        'The generated GEDCOM does not contain clearly recognizable person records (INDI).\n\nYou can still save the file, but you should review it especially carefully afterwards.'
),
    'dlg_gedcom_save_weak_title': 'Review GEDCOM',
    'dlg_gedcom_save_weak_question': 'Save it as a GEDCOM file anyway?',
    'msg_gedcom_generated_not_saved': 'GEDCOM was generated but not saved.',
    'msg_gedcom_save_dialog_open': 'GEDCOM was generated. Please choose where to save it.',
    'log_gedcom_not_saved': 'GEDCOM generated but not saved: {}',
    'dlg_save_gedcom': 'Save GEDCOM file',
    'dlg_filter_gedcom': 'GEDCOM file (*.ged)',
    'msg_gedcom_done': 'GEDCOM file saved: {}',
    'msg_gedcom_failed': 'GEDCOM generation failed.',
    'msg_gedcom_cancelled': 'GEDCOM generation cancelled.',
    'log_gedcom_done': 'GEDCOM generation finished: {}',
    'log_gedcom_failed': 'GEDCOM generation error: {} -> {}',
    'warn_gedcom_needs_text_or_image': 'GEDCOM generation needs a loaded page image or usable OCR text.',
    'lm_prompt_sqlite_system': 'SQLite – system prompt',
    'lm_prompt_sqlite_user': 'SQLite – user prompt',
    'prompt_desc_sqlite_system': 'System instruction for local AI extraction of SQLite-compatible person and register data.',
    'prompt_desc_sqlite_user': 'User instruction for SQLite data: extracts persons, entries, ages, places, years and evidence into flat JSON tables.',
    'ai_prompt_sqlite_system': 'You are a precise extraction assistant. Return only valid JSON for an SQLite export. No Markdown explanation.',
    'ai_prompt_sqlite_user': (
        'Extract an SQLite-compatible structure from the OCR text with documents, persons and entries. Each detected person/registration should get its own record. Preserve names, ages, places, years, dates and original evidence. OCR text:\n{}'
),
    'busy_queue_ref': 'Queue #{}',
}
BK_GEDCOM_ROBUST_TEXTS_EN = {
    'log_gedcom_retry_strict': 'The GEDCOM response was not importable; retrying with stricter GEDCOM instructions.',
    'log_gedcom_fallback_note': 'Created GEDCOM fallback: model response was embedded as a NOTE in a GEDCOM wrapper.',
    'warn_gedcom_no_person_records': (
        'The generated GEDCOM file contains no reliably recognized individual records, or only a placeholder.\n\nThis can happen when the local model reads the entry but does not convert it into proper GEDCOM structure. You can still save the file, but you should review and correct it carefully in your genealogy software.'
),
    'gedcom_fallback_note_title': 'Automatically generated GEDCOM fallback. The local model did not return clean GEDCOM text.',
    'ai_prompt_gedcom_system': (
        'You are a precise genealogy, transcription, and GEDCOM assistant.\nYou analyze historical civil registers, church books, and registry-office forms.\nYour output MUST be only a GEDCOM 5.5.1 file in LINEAGE-LINKED format.\nNo explanation, no markdown, no JSON, no code fences, no comments outside GEDCOM.\nThe first line MUST be exactly `0 HEAD`. The last line MUST be exactly `0 TRLR`.\nUse `1 CHAR UTF-8`. Use stable IDs such as @I1@, @I2@, @F1@.\nCreate an INDI record for every reliably identifiable person.\nFor birth records: create the child as an INDI record even if unnamed; use `1 NAME Unnamed //` and add a NOTE about the uncertainty.\nCreate parent INDI records when parents are named. Connect parents and child through a FAM record with HUSB/WIFE/CHIL when the relationship is clear.\nUse BIRT/DATE/PLAC, RESI, OCCU, NOTE, and SOUR only when supported or explicitly uncertain.\nWrite names in GEDCOM form, e.g. `1 NAME August /Böttcher/`. Maiden names may be added as NOTE.\nIf a given name, surname, place, or date is uncertain, do not invent it; record the uncertain reading as NOTE.\nEven with difficult handwriting, create a minimal importable GEDCOM file; do not refuse.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'ai_prompt_gedcom_user': (
        'Create an importable GEDCOM file from the page image and OCR text.\n\nImportant for German civil-register forms:\n- identify registry office/place, record number, entry date, and birth date\n- identify informant, father, mother, mother\'s maiden name, residence, occupation/status, and child\n- if the child has no given name, create it as `1 NAME Unnamed //`\n- connect child and parents with a FAM record when father/mother are clearly supported\n\nMinimum GEDCOM structure:\n0 HEAD\n1 SOUR BottledKraken\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n1 CHAR UTF-8\n0 @I1@ INDI\n1 NAME ...\n0 TRLR\n\nReturn only GEDCOM level lines. Every line must start with a level number.\nIf something is uncertain, write it as NOTE, but still create a GEDCOM file.\n\nOCR text as additional context:\n{}\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'lm_prompt_sqlite_system': 'SQLite – system prompt',
    'lm_prompt_sqlite_user': 'SQLite – user prompt',
    'prompt_desc_sqlite_system': 'System instruction for local AI extraction of SQLite-compatible person and register data.',
    'prompt_desc_sqlite_user': 'User instruction for SQLite data: extracts persons, entries, ages, places, years and evidence into flat JSON tables.',
    'ai_prompt_sqlite_system': 'You are a precise extraction assistant. Return only valid JSON for an SQLite export. No Markdown explanation.',
    'ai_prompt_sqlite_user': (
        'Extract an SQLite-compatible structure from the OCR text with documents, persons and entries. Each detected person/registration should get its own record. Preserve names, ages, places, years, dates and original evidence. OCR text:\n{}'
),
    'busy_queue_ref': 'Queue #{}',
}
BK_GEDCOM_STRUCTURED_TEXTS_EN = {
    'log_gedcom_structured_start': 'GEDCOM: extracting structured genealogical data from image and OCR context.',
    'log_gedcom_structured_success': 'GEDCOM: structured data recognized; generating GEDCOM deterministically.',
    'log_gedcom_structured_fallback': 'GEDCOM: structured extraction was not usable; using direct GEDCOM fallback.',
    'lm_prompt_gedcom_extract_system': 'GEDCOM – extraction system prompt',
    'lm_prompt_gedcom_extract_user': 'GEDCOM – extraction user prompt',
    'ai_prompt_gedcom_extract_system': (
        'You are a precise genealogical extraction assistant for historical German civil-register forms, church books, and vital records.\nYour task is NOT to write GEDCOM directly, but to extract genealogical facts as valid JSON.\nUse the page image as the primary source. OCR text is only additional context and may be wrong.\nFor German birth records the form usually contains: registry office/place, record number, informant, father, mother, residence, religion, birth date, birth time, sex, and child.\nExtract only information visible in the image or OCR context. Do not invent names.\nIf a reading is uncertain, still put it into the appropriate field and set uncertainty to true.\nReply only with JSON. No markdown, no explanation.\n\nImportant for register/table pages: do not extract only one person. Also create a `registrations` list. Each item corresponds to exactly one row/register entry with person.given_names, person.surname, age, event_date, event_place, residence, occupation, notes, source_line and uncertainty. Age expressions in years/months/days must be preserved.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'ai_prompt_gedcom_extract_user': (
        'Extract genealogical data from this page as JSON. Prefer the image; OCR is only a hint.\n\nReturn exactly this structure:\n{{\n  "record_type": "birth|marriage|death|unknown",\n  "registry_place": "",\n  "record_number": "",\n  "entry_date": "",\n  "event_date": "",\n  "event_time": "",\n  "event_place": "",\n  "child": {{"given_names": "", "surname": "", "sex": "M|F|U", "note": ""}},\n  "father": {{"given_names": "", "surname": "", "occupation": "", "residence": "", "religion": "", "note": ""}},\n  "mother": {{"given_names": "", "surname": "", "maiden_surname": "", "occupation": "", "residence": "", "religion": "", "note": ""}},\n  "informant": {{"given_names": "", "surname": "", "occupation": "", "residence": "", "relation": "", "note": ""}},\n  "source_title": "",\n  "transcription_or_notes": "",\n  "uncertainty": true\n}}\n\nSpecial rule for birth records: If the form says that the child has not yet received given names, set child.given_names to "Unnamed" and note that in child.note.\nIf the child\'s surname is not explicitly written but the parents are clear, you may derive the surname from the father and mark it as derived in child.note.\n\nOCR context:\n{}\n\nImportant for register/table pages: do not extract only one person. Also create a `registrations` list. Each item corresponds to exactly one row/register entry with person.given_names, person.surname, age, event_date, event_place, residence, occupation, notes, source_line and uncertainty. Age expressions in years/months/days must be preserved.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value fro'
        'm the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'lm_prompt_sqlite_system': 'SQLite – system prompt',
    'lm_prompt_sqlite_user': 'SQLite – user prompt',
    'prompt_desc_sqlite_system': 'System instruction for local AI extraction of SQLite-compatible person and register data.',
    'prompt_desc_sqlite_user': 'User instruction for SQLite data: extracts persons, entries, ages, places, years and evidence into flat JSON tables.',
    'ai_prompt_sqlite_system': 'You are a precise extraction assistant. Return only valid JSON for an SQLite export. No Markdown explanation.',
    'ai_prompt_sqlite_user': (
        'Extract an SQLite-compatible structure from the OCR text with documents, persons and entries. Each detected person/registration should get its own record. Preserve names, ages, places, years, dates and original evidence. OCR text:\n{}'
),
    'busy_queue_ref': 'Queue #{}',
}
BK_GEDCOM_REVIEW_TEXTS_EN = {
    'dlg_gedcom_review_title': 'Review and export GEDCOM',
    'gedcom_review_intro': 'The GEDCOM file has been generated. Review the recognized data, correct it if necessary, and then export the GEDCOM file.',
    'gedcom_review_tab_data': 'Recognized data',
    'gedcom_review_tab_text': 'GEDCOM text',
    'gedcom_review_field': 'Field',
    'gedcom_review_value': 'Value',
    'gedcom_review_update': 'Update GEDCOM from overview',
    'gedcom_review_export': 'Export GEDCOM...',
    'gedcom_review_close': 'Close',
    'gedcom_review_no_structured': 'No structured extraction data is available. You can edit the GEDCOM text directly in the second tab and export it.',
    'gedcom_review_weak_warning': 'Note: the generated GEDCOM contains no reliable individual records or was created as a fallback. Review it especially carefully.',
    'gedcom_review_update_failed': (
        'The GEDCOM file could not be rebuilt from the edited data:\n{}'
),
    'gedcom_review_export_empty': 'The GEDCOM text is empty and cannot be exported.',
    'gedcom_review_export_weak': (
        'The GEDCOM text contains no clearly identifiable INDI individual records or was created as a fallback.\n\nExport anyway?'
),
    'gedcom_review_export_cancelled': 'GEDCOM was generated but not exported.',
    'gedcom_review_export_done': 'GEDCOM file exported: {}',
    'gedcom_review_export_failed': (
        'The GEDCOM file could not be saved:\n{}'
),
    'gedcom_group_general': 'General',
    'gedcom_group_child': 'Child / main person',
    'gedcom_group_father': 'Father',
    'gedcom_group_mother': 'Mother',
    'gedcom_group_informant': 'Informant',
    'gedcom_field_record_type': 'Record type',
    'gedcom_field_registry_place': 'Registry office / place',
    'gedcom_field_record_number': 'Record number',
    'gedcom_field_entry_date': 'Entry date',
    'gedcom_field_event_date': 'Event date',
    'gedcom_field_event_time': 'Event time',
    'gedcom_field_event_place': 'Event place',
    'gedcom_field_source_title': 'Source title',
    'gedcom_field_transcription_or_notes': 'Transcription / notes',
    'gedcom_field_uncertainty': 'Uncertain reading',
    'gedcom_field_given_names': 'Given name(s)',
    'gedcom_field_surname': 'Surname',
    'gedcom_field_maiden_surname': 'Maiden surname',
    'gedcom_field_sex': 'Sex',
    'gedcom_field_occupation': 'Occupation',
    'gedcom_field_residence': 'Residence',
    'gedcom_field_religion': 'Religion',
    'gedcom_field_relation': 'Relation',
    'gedcom_field_note': 'Note',
    'gedcom_overview_person_count': 'Individual records',
    'gedcom_overview_family_count': 'Family records',
    'gedcom_overview_names': 'Names in GEDCOM',
    'gedcom_group_registrations': 'Registrations / persons',
    'gedcom_registration_selected': 'Export',
    'gedcom_registration_name': 'Name',
    'gedcom_registration_age': 'Age',
    'gedcom_registration_date': 'Date/year',
    'gedcom_registration_place': 'Place',
    'gedcom_registration_note': 'Note',
    'lm_prompt_sqlite_system': 'SQLite – system prompt',
    'lm_prompt_sqlite_user': 'SQLite – user prompt',
    'prompt_desc_sqlite_system': 'System instruction for local AI extraction of SQLite-compatible person and register data.',
    'prompt_desc_sqlite_user': 'User instruction for SQLite data: extracts persons, entries, ages, places, years and evidence into flat JSON tables.',
    'ai_prompt_sqlite_system': 'You are a precise extraction assistant. Return only valid JSON for an SQLite export. No Markdown explanation.',
    'ai_prompt_sqlite_user': (
        'Extract an SQLite-compatible structure from the OCR text with documents, persons and entries. Each detected person/registration should get its own record. Preserve names, ages, places, years, dates and original evidence. OCR text:\n{}'
),
    'busy_queue_ref': 'Queue #{}',
}
BK_PROMPT_UX_EXTRA_TEXTS_EN = {
    'dlg_lm_prompts_hint_optimized': 'Select a prompt on the left. On the right you see a short explanation and can edit the prompt. For GEDCOM, the data-extraction prompts are normally the important ones; direct GEDCOM generation is only a fallback. Keep placeholders such as {} and doubled JSON braces {{...}} intact.',
    'chk_show_advanced_prompts': 'Show advanced/fallback prompts',
    'prompt_group_local_ocr': 'Local OCR/revision prompts',
    'prompt_group_gedcom_main': 'GEDCOM – recommended main path',
    'prompt_group_gedcom_fallback': 'GEDCOM – fallback / direct GEDCOM',
    'prompt_desc_single_system': 'System instruction for rereading one line from a small image crop.',
    'prompt_desc_single_user': 'User instruction for rereading one line. Contains the line-number placeholder.',
    'prompt_desc_block_system': 'System instruction for small line blocks that provide context during revision.',
    'prompt_desc_block_user': 'User instruction for small line blocks. Used for selected lines and parts of all-line revision.',
    'prompt_desc_page_system': 'System instruction for page-related line recognition with a fixed line count.',
    'prompt_desc_page_user': 'User instruction for page-related line recognition. Keep placeholders and JSON structure intact.',
    'prompt_desc_decision_system': 'System instruction for choosing between Kraken OCR, box OCR, and page/block context.',
    'prompt_desc_decision_user': 'User instruction for the final per-line decision. Keep placeholders intact.',
    'prompt_desc_fullpage_ocr_system': 'System instruction for LM page OCR without overlay boxes: the vision model reads the full page and creates new text lines independently of existing boxes.',
    'prompt_desc_fullpage_ocr_user': 'User instruction for LM page OCR without overlay boxes. The model should return plain lines; existing overlay boxes are intentionally ignored and not reused afterwards.',
    'prompt_desc_gedcom_extract_system': 'Most important GEDCOM prompt: the model extracts genealogical facts as JSON. The program builds the GEDCOM file and review overview from it.',
    'prompt_desc_gedcom_extract_user': 'Most important GEDCOM user prompt: defines which fields should be recognized from image and OCR. Keep the JSON structure intact.',
    'prompt_desc_gedcom_system': 'Fallback prompt: only used if structured GEDCOM extraction fails. The model should write GEDCOM directly.',
    'prompt_desc_gedcom_user': 'Fallback user prompt: reserve path only. You normally do not need to adjust this prompt.',
    'lm_prompt_gedcom_system': 'GEDCOM – direct fallback – system prompt',
    'lm_prompt_gedcom_user': 'GEDCOM – direct fallback – user prompt',
    'lm_prompt_gedcom_extract_system': 'GEDCOM – recommended data extraction – system prompt',
    'lm_prompt_gedcom_extract_user': 'GEDCOM – recommended data extraction – user prompt',
    'ditto_instruction_strict': 'Ditto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.',
    'export_format_docx': 'Word (.docx)',
    'ai_prompt_fullpage_lm_ocr_system': 'You are a precise OCR system. Return valid JSON only. Detect every text line separately in natural reading order. Ditto marks such as " or -"- mean that the value from the same visual column in the previous line is repeated. Write out the repeated value and never output the mark literally.',
    'ai_prompt_fullpage_lm_ocr_user': 'Run OCR for the complete visible document page. Ignore existing overlay boxes. Return JSON only in the format {"lines":[{"text":"..."}]}. Every detected entry must be its own line; do not merge entries into paragraphs. If " or -"- appears in a table/register column, replace it with the value from the same visual column in the previous line.',
    'lm_prompt_sqlite_system': 'SQLite – system prompt',
    'lm_prompt_sqlite_user': 'SQLite – user prompt',
    'prompt_desc_sqlite_system': 'System instruction for local AI extraction of SQLite-compatible person and register data.',
    'prompt_desc_sqlite_user': 'User instruction for SQLite data: extracts persons, entries, ages, places, years and evidence into flat JSON tables.',
    'ai_prompt_sqlite_system': 'You are a precise extraction assistant. Return only valid JSON for an SQLite export. No Markdown explanation.',
    'ai_prompt_sqlite_user': (
        'Extract an SQLite-compatible structure from the OCR text with documents, persons and entries. Each detected person/registration should get its own record. Preserve names, ages, places, years, dates and original evidence. OCR text:\n{}'
),
    'busy_queue_ref': 'Queue #{}',
    'lm_prompt_fullpage_ocr_system': 'LM page OCR (without overlay boxes) – system prompt',
    'lm_prompt_fullpage_ocr_user': 'LM page OCR (without overlay boxes) – user prompt',
    'lm_prompt_page_boxes_align_system': 'LM page OCR with overlay boxes – alignment system prompt',
    'lm_prompt_page_boxes_align_user': 'LM page OCR with overlay boxes – alignment user prompt',
    'prompt_desc_page_boxes_align_system': 'System instruction for LM page OCR with overlay boxes: the model maps the full-page OCR lines exactly to the existing overlay boxes.',
    'prompt_desc_page_boxes_align_user': 'User instruction for LM page OCR with overlay boxes. Keep the placeholders for box count, page-OCR lines and overlay-box anchors intact.',
}
BK_GEDCOM_TRANSLATIONS_EN = {
    'act_lm_generate_gedcom': 'GEDCOM file',
    'dlg_gedcom_title': 'GEDCOM file',
    'dlg_gedcom_notice': 'The current page will be analyzed by the local AI model. The page image and any available OCR lines will be considered together. The result is a GEDCOM file that you should review in your genealogy software afterwards.',
    'msg_gedcom_started': 'GEDCOM generation started. Page image and OCR text are being analyzed.',
    'msg_gedcom_done': 'GEDCOM file saved: {}',
    'msg_gedcom_cancelled': 'GEDCOM generation cancelled.',
    'msg_gedcom_failed': 'GEDCOM generation failed.',
    'log_gedcom_started': 'GEDCOM generation started: {}',
    'log_gedcom_done': 'GEDCOM generation finished: {}',
    'log_gedcom_failed': 'GEDCOM generation error: {} -> {}',
    'dlg_save_gedcom': 'Save GEDCOM file',
    'dlg_filter_gedcom': 'GEDCOM file (*.ged)',
    'warn_no_text_for_gedcom': 'There is no usable text for GEDCOM generation.',
    'lm_prompt_gedcom_system': 'GEDCOM – direct fallback – system prompt',
    'lm_prompt_gedcom_user': 'GEDCOM – direct fallback – user prompt',
    'ai_prompt_gedcom_system': (
        'You are a precise genealogy, transcription, and GEDCOM assistant.\nYou analyze historical civil registers, church books, and registry-office forms.\nYour output MUST be only a GEDCOM 5.5.1 file in LINEAGE-LINKED format.\nNo explanation, no markdown, no JSON, no code fences, no comments outside GEDCOM.\nThe first line MUST be exactly `0 HEAD`. The last line MUST be exactly `0 TRLR`.\nUse `1 CHAR UTF-8`. Use stable IDs such as @I1@, @I2@, @F1@.\nCreate an INDI record for every reliably identifiable person.\nFor birth records: create the child as an INDI record even if unnamed; use `1 NAME Unnamed //` and add a NOTE about the uncertainty.\nCreate parent INDI records when parents are named. Connect parents and child through a FAM record with HUSB/WIFE/CHIL when the relationship is clear.\nUse BIRT/DATE/PLAC, RESI, OCCU, NOTE, and SOUR only when supported or explicitly uncertain.\nWrite names in GEDCOM form, e.g. `1 NAME August /Böttcher/`. Maiden names may be added as NOTE.\nIf a given name, surname, place, or date is uncertain, do not invent it; record the uncertain reading as NOTE.\nEven with difficult handwriting, create a minimal importable GEDCOM file; do not refuse.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'ai_prompt_gedcom_user': (
        'Create an importable GEDCOM file from the page image and OCR text.\n\nImportant for German civil-register forms:\n- identify registry office/place, record number, entry date, and birth date\n- identify informant, father, mother, mother\'s maiden name, residence, occupation/status, and child\n- if the child has no given name, create it as `1 NAME Unnamed //`\n- connect child and parents with a FAM record when father/mother are clearly supported\n\nMinimum GEDCOM structure:\n0 HEAD\n1 SOUR BottledKraken\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n1 CHAR UTF-8\n0 @I1@ INDI\n1 NAME ...\n0 TRLR\n\nReturn only GEDCOM level lines. Every line must start with a level number.\nIf something is uncertain, write it as NOTE, but still create a GEDCOM file.\n\nOCR text as additional context:\n{}\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'lm_prompt_canonical_system': 'Canonical JSON – system prompt',
    'lm_prompt_canonical_user': 'Canonical JSON – user prompt',
    'ai_prompt_canonical_system': (
        'You are a JSON-only extraction engine for genealogical and historical OCR text. Return exactly one valid JSON object. No markdown, no explanations, no code fences. Extract only information supported by the OCR text.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_canonical_user': (
        'Create canonical_graph JSON from the following OCR text.\nUse exactly this structure:\n{schema_template}\n\nRules:\n- Entities: PERSON, PLACE, YEAR, AGE, EVENT, DOCUMENT, ENTITY.\n- Relations: RELATED_TO, LOCATED_IN, DURING, PART_OF, ASSOCIATED_WITH.\n- strength is a number from 0.0 to 1.0.\n- Use null for unknown values.\n- Return JSON only.\n\nOCR_TEXT_START\n{ocr_text}\nOCR_TEXT_END\n- Extract ages/age expressions (years, months, days) as AGE entities and as age attributes on PERSON nodes when possible.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_postgresql_system': (
        'You are an extraction assistant for OCR-derived historical or administrative texts. Return valid JSON only. No explanations, no markdown. Do not invent missing information.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_postgresql_user': (
        'Create a PostgreSQL-oriented JSON payload from the following text.\nReturn exactly one JSON object with these keys:\n{schema_template}\n\nText:\n{ocr_text}\n- Include age/age expressions when present in the source text.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_neo4j_system': (
        'You are a graph extraction assistant for OCR-derived texts. Return valid JSON only. Create only supported nodes and relationships. No explanations, no markdown.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_neo4j_user': (
        'Create a Neo4j-oriented graph JSON payload from the following text.\nReturn exactly one JSON object with these keys:\n{schema_template}\n\nText:\n{ocr_text}\n- Include age/age expressions when present in the source text.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.\n\nDitto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.'
),
    'ai_prompt_fullpage_lm_ocr_system': 'You are a precise OCR system. Return valid JSON only. Detect every text line separately in natural reading order. Ditto marks such as " or -"- mean that the value from the same visual column in the previous line is repeated. Write out the repeated value and never output the mark literally.',
    'ai_prompt_fullpage_lm_ocr_user': 'Run OCR for the complete visible document page. Ignore existing overlay boxes. Return JSON only in the format {"lines":[{"text":"..."}]}. Every detected entry must be its own line; do not merge entries into paragraphs. If " or -"- appears in a table/register column, replace it with the value from the same visual column in the previous line.',
    'lm_busy_default_message': 'The local model is working. Duration depends on the model, image size and page complexity. Please wait.',
    'lm_busy_revision_status': 'The local model is revising the lines. First the complete page is read as context, then three overlay boxes at a time are analyzed.',
    'ai_status_step0_fullpage_context': '1/3: Reading the complete page only as context: {}',
    'lm_prompt_sqlite_system': 'SQLite – system prompt',
    'lm_prompt_sqlite_user': 'SQLite – user prompt',
    'prompt_desc_sqlite_system': 'System instruction for local AI extraction of SQLite-compatible person and register data.',
    'prompt_desc_sqlite_user': 'User instruction for SQLite data: extracts persons, entries, ages, places, years and evidence into flat JSON tables.',
    'ai_prompt_sqlite_system': 'You are a precise extraction assistant. Return only valid JSON for an SQLite export. No Markdown explanation.',
    'ai_prompt_sqlite_user': (
        'Extract an SQLite-compatible structure from the OCR text with documents, persons and entries. Each detected person/registration should get its own record. Preserve names, ages, places, years, dates and original evidence. OCR text:\n{}'
),
    'busy_queue_ref': 'Queue #{}',
    'warn_gedcom_needs_text_or_image': 'GEDCOM generation needs a loaded page image or usable OCR text.',
    'log_gedcom_retry_text_only': 'GEDCOM: The model did not accept the image request. Retrying with OCR text only.',
    'warn_gedcom_no_output': 'The local model did not return usable GEDCOM text.',
    'warn_gedcom_no_person_records': (
        'The generated GEDCOM file contains no reliably recognized individual records, or only a placeholder.\n\nThis can happen when the local model reads the entry but does not convert it into proper GEDCOM structure. You can still save the file, but you should review and correct it carefully in your genealogy software.'
),
    'dlg_gedcom_save_weak_title': 'Review GEDCOM',
    'dlg_gedcom_save_weak_question': 'Save it as a GEDCOM file anyway?',
    'msg_gedcom_generated_not_saved': 'GEDCOM was generated but not saved.',
    'msg_gedcom_save_dialog_open': 'GEDCOM was generated. Please choose where to save it.',
    'log_gedcom_not_saved': 'GEDCOM generated but not saved: {}',
    'log_gedcom_retry_strict': 'The GEDCOM response was not importable; retrying with stricter GEDCOM instructions.',
    'log_gedcom_fallback_note': 'Created GEDCOM fallback: model response was embedded as a NOTE in a GEDCOM wrapper.',
    'gedcom_fallback_note_title': 'Automatically generated GEDCOM fallback. The local model did not return clean GEDCOM text.',
    'log_gedcom_structured_start': 'GEDCOM: extracting structured genealogical data from image and OCR context.',
    'log_gedcom_structured_success': 'GEDCOM: structured data recognized; generating GEDCOM deterministically.',
    'log_gedcom_structured_fallback': 'GEDCOM: structured extraction was not usable; using direct GEDCOM fallback.',
    'lm_prompt_gedcom_extract_system': 'GEDCOM – recommended data extraction – system prompt',
    'lm_prompt_gedcom_extract_user': 'GEDCOM – recommended data extraction – user prompt',
    'ai_prompt_gedcom_extract_system': (
        'You are a precise genealogical extraction assistant for historical German civil-register forms, church books, and vital records.\nYour task is NOT to write GEDCOM directly, but to extract genealogical facts as valid JSON.\nUse the page image as the primary source. OCR text is only additional context and may be wrong.\nFor German birth records the form usually contains: registry office/place, record number, informant, father, mother, residence, religion, birth date, birth time, sex, and child.\nExtract only information visible in the image or OCR context. Do not invent names.\nIf a reading is uncertain, still put it into the appropriate field and set uncertainty to true.\nReply only with JSON. No markdown, no explanation.\n\nImportant for register/table pages: do not extract only one person. Also create a `registrations` list. Each item corresponds to exactly one row/register entry with person.given_names, person.surname, age, event_date, event_place, residence, occupation, notes, source_line and uncertainty. Age expressions in years/months/days must be preserved.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value from the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'ai_prompt_gedcom_extract_user': (
        'Extract genealogical data from this page as JSON. Prefer the image; OCR is only a hint.\n\nReturn exactly this structure:\n{{\n  "record_type": "birth|marriage|death|unknown",\n  "registry_place": "",\n  "record_number": "",\n  "entry_date": "",\n  "event_date": "",\n  "event_time": "",\n  "event_place": "",\n  "child": {{"given_names": "", "surname": "", "sex": "M|F|U", "note": ""}},\n  "father": {{"given_names": "", "surname": "", "occupation": "", "residence": "", "religion": "", "note": ""}},\n  "mother": {{"given_names": "", "surname": "", "maiden_surname": "", "occupation": "", "residence": "", "religion": "", "note": ""}},\n  "informant": {{"given_names": "", "surname": "", "occupation": "", "residence": "", "relation": "", "note": ""}},\n  "source_title": "",\n  "transcription_or_notes": "",\n  "uncertainty": true\n}}\n\nSpecial rule for birth records: If the form says that the child has not yet received given names, set child.given_names to "Unnamed" and note that in child.note.\nIf the child\'s surname is not explicitly written but the parents are clear, you may derive the surname from the father and mark it as derived in child.note.\n\nOCR context:\n{}\n\nImportant for register/table pages: do not extract only one person. Also create a `registrations` list. Each item corresponds to exactly one row/register entry with person.given_names, person.surname, age, event_date, event_place, residence, occupation, notes, source_line and uncertainty. Age expressions in years/months/days must be preserved.\n\nImportant: A single " or -"- in a table/register column is a ditto mark. It means the value fro'
        'm the same column in the previous line is repeated. Write out the repeated value and do not output the mark literally. Example: if " appears below “Beltzkey”, the value is “Beltzkey” again.'
),
    'dlg_gedcom_review_title': 'Review and export GEDCOM',
    'gedcom_review_intro': 'The GEDCOM file has been generated. Review the recognized data, correct it if necessary, and then export the GEDCOM file.',
    'gedcom_review_tab_data': 'Recognized data',
    'gedcom_review_tab_text': 'GEDCOM text',
    'gedcom_review_field': 'Field',
    'gedcom_review_value': 'Value',
    'gedcom_review_update': 'Update GEDCOM from overview',
    'gedcom_review_export': 'Export GEDCOM...',
    'gedcom_review_close': 'Close',
    'gedcom_review_no_structured': 'No structured extraction data is available. You can edit the GEDCOM text directly in the second tab and export it.',
    'gedcom_review_weak_warning': 'Note: the generated GEDCOM contains no reliable individual records or was created as a fallback. Review it especially carefully.',
    'gedcom_review_update_failed': (
        'The GEDCOM file could not be rebuilt from the edited data:\n{}'
),
    'gedcom_review_export_empty': 'The GEDCOM text is empty and cannot be exported.',
    'gedcom_review_export_weak': (
        'The GEDCOM text contains no clearly identifiable INDI individual records or was created as a fallback.\n\nExport anyway?'
),
    'gedcom_review_export_cancelled': 'GEDCOM was generated but not exported.',
    'gedcom_review_export_done': 'GEDCOM file exported: {}',
    'gedcom_review_export_failed': (
        'The GEDCOM file could not be saved:\n{}'
),
    'gedcom_group_general': 'General',
    'gedcom_group_child': 'Child / main person',
    'gedcom_group_father': 'Father',
    'gedcom_group_mother': 'Mother',
    'gedcom_group_informant': 'Informant',
    'gedcom_field_record_type': 'Record type',
    'gedcom_field_registry_place': 'Registry office / place',
    'gedcom_field_record_number': 'Record number',
    'gedcom_field_entry_date': 'Entry date',
    'gedcom_field_event_date': 'Event date',
    'gedcom_field_event_time': 'Event time',
    'gedcom_field_event_place': 'Event place',
    'gedcom_field_source_title': 'Source title',
    'gedcom_field_transcription_or_notes': 'Transcription / notes',
    'gedcom_field_uncertainty': 'Uncertain reading',
    'gedcom_field_given_names': 'Given name(s)',
    'gedcom_field_surname': 'Surname',
    'gedcom_field_maiden_surname': 'Maiden surname',
    'gedcom_field_sex': 'Sex',
    'gedcom_field_occupation': 'Occupation',
    'gedcom_field_residence': 'Residence',
    'gedcom_field_religion': 'Religion',
    'gedcom_field_relation': 'Relation',
    'gedcom_field_note': 'Note',
    'gedcom_overview_person_count': 'Individual records',
    'gedcom_overview_family_count': 'Family records',
    'gedcom_overview_names': 'Names in GEDCOM',
    'gedcom_group_registrations': 'Registrations / persons',
    'gedcom_registration_selected': 'Export',
    'gedcom_registration_name': 'Name',
    'gedcom_registration_age': 'Age',
    'gedcom_registration_date': 'Date/year',
    'gedcom_registration_place': 'Place',
    'gedcom_registration_note': 'Note',
    'dlg_lm_prompts_hint_optimized': 'Select a prompt on the left. On the right you see a short explanation and can edit the prompt. For GEDCOM, the data-extraction prompts are normally the important ones; direct GEDCOM generation is only a fallback. Keep placeholders such as {} and doubled JSON braces {{...}} intact.',
    'chk_show_advanced_prompts': 'Show advanced/fallback prompts',
    'prompt_group_local_ocr': 'Local OCR/revision prompts',
    'prompt_group_gedcom_main': 'GEDCOM – recommended main path',
    'prompt_group_gedcom_fallback': 'GEDCOM – fallback / direct GEDCOM',
    'prompt_desc_single_system': 'System instruction for rereading one line from a small image crop.',
    'prompt_desc_single_user': 'User instruction for rereading one line. Contains the line-number placeholder.',
    'prompt_desc_block_system': 'System instruction for small line blocks that provide context during revision.',
    'prompt_desc_block_user': 'User instruction for small line blocks. Used for selected lines and parts of all-line revision.',
    'prompt_desc_page_system': 'System instruction for page-related line recognition with a fixed line count.',
    'prompt_desc_page_user': 'User instruction for page-related line recognition. Keep placeholders and JSON structure intact.',
    'prompt_desc_decision_system': 'System instruction for choosing between Kraken OCR, box OCR, and page/block context.',
    'prompt_desc_decision_user': 'User instruction for the final per-line decision. Keep placeholders intact.',
    'prompt_desc_fullpage_ocr_system': 'System instruction for LM Page OCR: the vision model reads the whole page without existing overlay boxes.',
    'prompt_desc_fullpage_ocr_user': 'User instruction for LM Page OCR. The model should return plain lines; overlay boxes are intentionally not reused afterwards.',
    'prompt_desc_gedcom_extract_system': 'Most important GEDCOM prompt: the model extracts genealogical facts as JSON. The program builds the GEDCOM file and review overview from it.',
    'prompt_desc_gedcom_extract_user': 'Most important GEDCOM user prompt: defines which fields should be recognized from image and OCR. Keep the JSON structure intact.',
    'prompt_desc_gedcom_system': 'Fallback prompt: only used if structured GEDCOM extraction fails. The model should write GEDCOM directly.',
    'prompt_desc_gedcom_user': 'Fallback user prompt: reserve path only. You normally do not need to adjust this prompt.',
    'ditto_instruction_strict': 'Ditto marks: a single " or multiple "" or -"- ALWAYS mean repetition from the previous line in the same column. It can be a name, place, date, year, number or any other field. Never output these signs literally. Example: if only " or ""Beltzkey appears below/at Beltzkey, write Beltzkey as the repeated value.',
    'export_format_docx': 'Word (.docx)',
}
