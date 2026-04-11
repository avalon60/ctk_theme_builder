---
name: enhance-theme
description: Locate, modify, and optionally promote CTk Theme Builder theme JSON files
---

When asked to enhance, tweak, modify, or promote a theme:

1. Look for the theme JSON file in `~/CTkThemeBuilder/themes/`, using `<theme_name>.json`.
2. If the file does not exist, report that it was not found and do not continue with edits or promotion.
3. Treat the file in `~/CTkThemeBuilder/themes/` as the authoritative editable source for this task.
4. Save all requested theme changes back to `~/CTkThemeBuilder/themes/`. Do not write changes to any seed theme location in the repository.
5. If the user asks to promote the theme, copy the theme JSON file to `<repo-root>/user_themes/`.
6. If the user asks to promote the theme to the control panel themes, copy the theme JSON file to `<repo-root>/assets/themes/`.
7. Where a <theme_name>.json file exists in the ~/CTkThemeBuilder/palettes directory, and a promotion is requested, then the palette file should be copied to the <repo-root>/assets/palettes directory.
8. Preserve valid JSON structure and formatting when editing or copying theme files.
9. If the promotion target already contains a file with the same name, warn before overwriting unless the user has explicitly asked to replace it.
10. If `<repo-root>` cannot be determined from the current working context, report that and ask for clarification before attempting promotion.
