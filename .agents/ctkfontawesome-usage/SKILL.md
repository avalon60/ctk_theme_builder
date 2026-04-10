---
name: ctkfontawesome-usage
description: Use when implementing Font Awesome icons in a CustomTkinter app with the ctkfontawesome package. Covers how to find icon names, create icon images, keep image references alive, size and recolor icons, and attach them to CTk widgets such as CTkButton and CTkLabel.
---

# CTkFontAwesome Usage

Use this skill when the task is to add or update an icon in a CustomTkinter UI using `ctkfontawesome`.

## Core Facts

- Import from `ctkfontawesome`, not `CTkFontAwesome`.
- The main API for widgets is `icon_to_image(...)`.
- `icon_to_image(...)` returns a `tkinter.PhotoImage` compatible object, so it can be passed anywhere a CTk widget accepts an `image=` argument.
- The optional image backend is required for `icon_to_image(...)`. If missing, the library raises `RuntimeError` telling you to install `ctkfontawesome[images]`.
- Valid icon names are Font Awesome free icon names such as `"gear"`, `"trash"`, `"circle-info"`, `"floppy-disk"`, or `"fa-gear"`. The `fa-` prefix is accepted.

## Default Workflow

1. Find the icon name.
2. Create the image with `icon_to_image(...)`.
3. Store the image on a persistent object attribute so Tk does not garbage-collect it.
4. Pass that image to the CTk widget.
5. If the widget state changes, regenerate the icon if the color or size should also change.

## Preferred Pattern

```python
from ctkfontawesome import icon_to_image
import customtkinter as ctk


class Toolbar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.settings_icon = icon_to_image(
            "gear",
            fill="#DCE4EE",
            scale_to_width=18,
        )

        self.settings_button = ctk.CTkButton(
            self,
            text="Settings",
            image=self.settings_icon,
            compound="left",
        )
        self.settings_button.pack(padx=12, pady=12)
```

## Rules For Codex

- Always keep a reference to the created image on `self`, a controller object, or another long-lived object.
- Do not create the image inline without storing it first if the widget may outlive the local scope.
- Match icon color to the current UI state. Typical choices are:
  - normal foreground text color for standard actions
  - muted text color for secondary actions
  - disabled text color for disabled controls
- Prefer `scale_to_width=` for predictable sizing in buttons, labels, toolbars, and row actions.
- If both width and height are supplied, the library uses those exact dimensions. Prefer one dimension unless distortion is intentional.
- Regenerate the icon when appearance mode, theme, or widget state changes and the icon color should change with it.

## Common Widget Patterns

### Icon-only button

```python
self.delete_icon = icon_to_image("trash", fill="#F16C6C", scale_to_width=16)
self.delete_button = ctk.CTkButton(
    parent,
    text="",
    width=28,
    image=self.delete_icon,
)
```

### Button with icon and text

```python
self.save_icon = icon_to_image("floppy-disk", fill="#FFFFFF", scale_to_width=16)
self.save_button = ctk.CTkButton(
    parent,
    text="Save",
    image=self.save_icon,
    compound="left",
)
```

### Label used as an icon holder

```python
self.info_icon = icon_to_image("circle-info", fill="#3B8ED0", scale_to_width=18)
self.info_label = ctk.CTkLabel(parent, text="", image=self.info_icon)
```

## Finding Icon Names

- Use the installed browser if available: `ctkfontawesome-browser`
- If code needs to inspect names programmatically:

```python
from ctkfontawesome import icon_names

names = icon_names()
```

- If an icon name is invalid, `icon_to_svg(...)` and therefore `icon_to_image(...)` raise `ValueError`.

## Failure Modes

- Missing optional image dependencies:
  - `RuntimeError: svg_to_image() requires the optional image dependencies...`
  - Fix by installing `ctkfontawesome[images]`
- Invalid icon name:
  - `ValueError`
- Image disappears from the widget:
  - usually caused by not keeping a persistent reference to the returned `PhotoImage`

## App Integration Guidance

- For toolbar and menu-like actions, create icons once during widget construction and reuse them.
- For stateful controls, create separate images for normal and disabled states if the icon needs to visibly change.
- For theme-aware UIs, derive icon color from the same theme token family as the widget text or foreground color.
- If the task is only to render or inspect an icon without attaching it to a widget, `icon_to_svg(...)` is sufficient.

## Minimal Snippet For Fast Edits

```python
from ctkfontawesome import icon_to_image

self.my_icon = icon_to_image("gear", fill="#DCE4EE", scale_to_width=16)
widget.configure(image=self.my_icon)
```
