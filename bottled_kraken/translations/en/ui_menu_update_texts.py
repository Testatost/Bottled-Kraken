"""UI- und Menü-Überschreibungen für aktuelle Menü-/Multi-OCR-Anpassungen."""

EN_UI_MENU_UPDATE_TEXTS = {'act_overlay_show': 'Overlay box visibility',
 'overlay_mode_none': 'Show none',
 'overlay_mode_current': 'Current line',
 'overlay_mode_selected': 'Selected lines',
 'overlay_mode_all': 'All lines',
 'overlay_resize_menu': 'Scale overlay boxes',
 'act_load_rec_model': 'Load Rec-Model...',
 'act_load_seg_model': 'Load Seg-Model...',
 'act_clear_rec': 'Remove Rec-Model',
 'act_clear_seg': 'Remove Seg-Model',
 'status_rec_model': 'Rec-Model: {}',
 'status_seg_model': 'Seg-Model: {}',
 'btn_rec_model_empty': 'Rec-Model: -',
 'btn_rec_model_value': 'Rec-Model: {}',
 'btn_seg_model_empty': 'Seg-Model: -',
 'btn_seg_model_value': 'Seg-Model: {}',
 'lm_menu_current_line': 'Current line',
 'lm_menu_selected_lines': 'Selected lines',
 'lm_menu_all_lines': 'All lines',
 'lm_menu_lm_ocr': 'LM page OCR (without overlay boxes)',
 'lm_menu_lm_ocr_boxes': 'LM page OCR with overlay boxes',
 'lm_menu_generate_postgres': 'PostgreSQL-json',
 'lm_menu_generate_neo4j': 'Neo4j-json',
 'lm_menu_generate_sqlite': 'SQLite-json',
 'lm_menu_show_canonical_graph': 'Graph view',
 'lm_menu_generate_canonical': 'Graph view',
 'act_lm_generate_gedcom': 'GEDCOM file',
 'msg_sqlite_export_done': 'SQLite-json exported: {}',
 'dlg_sqlite_json_title': 'Save SQLite-json',
 'filter_json_files': 'JSON (*.json);;All Files (*)',
 'ptr_multi_ocr_models_label': 'Which Rec-Models should be used? (enable/disable with checkmarks)',
 'multi_ocr_rec_models_label': 'Which Rec-Models should be used? (enable/disable with checkmarks)',
 'multi_ocr_runs_label': 'OCR repetitions per selected Rec-Model:',
 'multi_ocr_use_seg': 'Use Seg-Model',
 'multi_ocr_variants_tabs_title': 'OCR tabs / variants',
 'multi_ocr_variant_tab': 'Tab ({})',
 'multi_ocr_variant_tooltip': 'Tab ({}), Rec-Model: {}',
 'multi_ocr_variant_add_tooltip': 'Add a new OCR tab',
 'multi_ocr_variant_delete_tab': 'Delete OCR tab',
 'multi_ocr_variant_rename_label': 'New tab name:',
 'multi_ocr_variant_rename_title': 'Rename OCR tab',
 'multi_ocr_variant_rename_action': 'Rename OCR tab',
 'multi_ocr_no_text': '<no text>',
 'act_delete_checked_queue': 'Delete selected',
 'act_delete_checked_queue_tip': 'Delete only the checked files from the queue',
 'ptr_warn_select_recognition_model': 'Please enable at least one Rec-Model with a checkmark.',
 'multi_ocr_models_section': '1) Rec-Models',
 'multi_ocr_variants_section': '2) Image variants',
 'multi_ocr_variants_label': 'Which image variants should be used? (enable/disable with '
                             'checkmarks)',
 'multi_ocr_runs_section': '3) OCR repetitions',
 'multi_ocr_seg_model_fixed': 'The currently loaded Seg-Model is used unchanged for all selected '
                              'Rec-Models.',
 'multi_ocr_variant_original': 'Original',
 'multi_ocr_variant_autocontrast': 'Auto contrast',
 'multi_ocr_variant_contrast': 'Contrast +25%',
 'multi_ocr_variant_sharp': 'Sharpness +60%',
 'multi_ocr_variant_gray_autocontrast': 'Grayscale auto contrast',
 'multi_ocr_variant_binary_otsu': 'Binary/Otsu',
 'multi_ocr_variant_contrast_sharp': 'Contrast + sharpness',
 'multi_ocr_variant_equalize': 'Histogram equalization',
 'multi_ocr_variant_slightly_bright': 'Brightness +5%',
 'multi_ocr_variants_help_button_tooltip': 'Explain image variants',
 'multi_ocr_variants_help_title': 'Image variants explained',
 'multi_ocr_variants_help_intro': 'Image variants do not change the overlay boxes or the '
                                  'Seg-Model. They only create different pixel versions of the '
                                  'same page, so the same Rec-Model can produce several useful OCR '
                                  'candidates for difficult passages.',
 'multi_ocr_variants_help_footer': 'Recommendation: Original, auto contrast, contrast +25%, '
                                   'sharpness +60%, and grayscale auto contrast are a good default '
                                   'set. Binary/Otsu, contrast + sharpness, histogram '
                                   'equalization, and brightness +5% are additional variants for '
                                   'problematic scans.',
 'multi_ocr_variant_original_help': 'Uses the image unchanged after internal normalization. This '
                                    'is the reference variant and should usually remain enabled.',
 'multi_ocr_variant_autocontrast_help': 'Automatically stretches the existing brightness values. '
                                        'This often helps with flat, gray-looking, or poorly lit '
                                        'scans without fundamentally removing color.',
 'multi_ocr_variant_contrast_help': 'Moderately increases contrast by 25%. Light and dark areas '
                                    'become more separated, which can make faint ink or weak print '
                                    'easier to recognize.',
 'multi_ocr_variant_sharp_help': 'Increases edge sharpness by 60%. This can help with slightly '
                                 'blurred lines, but it may also emphasize noise in heavily '
                                 'degraded scans.',
 'multi_ocr_variant_gray_autocontrast_help': 'Converts the image to grayscale and then applies '
                                             'auto contrast. Useful when color is irrelevant for '
                                             'the writing or when color casts disturb recognition.',
 'multi_ocr_variant_binary_otsu_help': 'Converts the image to black and white using an '
                                       'automatically computed Otsu threshold. Good for clean '
                                       'scans with strong foreground-background contrast; often '
                                       'too harsh for stains, shadows, or parchment.',
 'multi_ocr_variant_contrast_sharp_help': 'Combines a careful contrast increase with additional '
                                          'sharpening. Useful for slightly washed-out originals '
                                          'that are not too noisy.',
 'multi_ocr_variant_equalize_help': 'Equalizes the histogram so brightness ranges are distributed '
                                    'more evenly. This can help with uneven illumination, but may '
                                    'create unnatural contrast in some scans.',
 'multi_ocr_variant_slightly_bright_help': 'Slightly increases brightness by 5%. Useful for scans '
                                           'that are generally too dark or where a dark background '
                                           'swallows parts of the writing.'}

# PATCH17_LM_PAGE_OCR_MENU_UPDATE_EN
EN_UI_MENU_UPDATE_TEXTS.update({'lm_menu_lm_ocr': 'LM page OCR (without overlay boxes)', 'lm_menu_lm_ocr_boxes': 'LM page OCR with overlay boxes'})
