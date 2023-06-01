
# Introduction

*A thank-you to my ever patient, ever loving, beautiful wife, who has let me hide in my office and beaver away at this project, for many an hour.*

### A Bit of History
In case you are wondering, "so where is CTk Theme Builder version 1.0?", well it was never made public. CTk Theme Builder, started with very humble beginnings. In fact it started with a crude CustomTkinter program which was used to display the results of theme file modifications, performed using a Vim editor (yes I use Vim - sue me ;o). Features were added and added, and well, the project grew legs and became a bit of an obsession. Version 1.0 was based on CustomTkinter 4, which had a radically different JSON format for the theme files. So when Tom decided to release v5 with a drastically different format, I decided to take a break and let things with the new version, bed in. Anyway, although the initial CTk Theme Builder was functional, it was never as polished as I would have liked.  The v5 format was actually a game changer - much improved and more object oriented, although it did present some non-trivial re-engineering challenges, but finally, here we are.

### CustomTkinter Version
Version 2.0 of CTk Theme Builder was designed around CustomeTkinter 5.1.3. Any behaviours / features described herein, are based upon this version. When you install CTk Theme Builder, it will install library modules into a virtual environment. Included in this will be CustomTkinter 5.1.3. If you upgrade the installed CustomTkinter version, this may have unpredictable results.

### Primary Windows
There are two main windows, the *Control Panel* and the *Preview Panel*. There are a sections in the guide, which cover these panels as well as other dialogues.

![CTkThemeBuilder-about](https://github.com/avalon60/ctk_theme_builder/assets/89534395/50cdd79a-1216-431c-a107-f40c2fe044f6)


The job of the *Control Panel* is to present necessary interface controls, giving you the means to create and manage the appearance of your theme. 

The *Preview Panel* appears when a theme has been opened and then remains when for the duration of the session. Once opened the *Preview Panel* only closes, when you *Quit* via the *Control Panel*.

### Window Positions
Whenever you drag and release a window into a new location of your display, CTk Theme Builder keeps track of where you place it. So for example you may choose to have the *Preview Panel* on the left and the *Control Panel* to the right of it. When you quit the application, it saves the settings, and will subsequently restore the window positions when CTk Theme Builder next starts up.

### Copy / Paste Operations
There are various sets of colour tiles, presented by the application. These appear in the control panel as well as the Colour Harmonics Panel (you will learn about this one later). In most cases, you can copy and paste hex colour codes (#rrggbb), between these. You can even copy hex colour codes based on searches on the Web, and / or by using colour samplers. As long as you have a valid hex colour code in your clipboard, you can paste it onto a colour tile.

Copy and Paste functions are accessible via a floating menu, which activates when you position your mouse pointer over a tile, and right-click.

### Appearance Modes
If you are sufficiently acquainted with CustomTkinter, you will be aware that the themes designed for CustomTkinter allow you to switch between a Dark Mode and a Light Mode.

When working your themes, you work / see, one appearance mode of a theme, at any given time, but can switch back and forth between the two whenever you wish.

### Concurrency
You can only run once instance of CTk Theme Builder at a time. This is because the *Control Panel* communicates via a fixed socket address (port 5051). If you attempt to run two instances of CTk Theme Builder on the same computer, you will see a timeout message:

![timeout](https://github.com/avalon60/ctk_theme_builder/assets/89534395/9d12b650-8b17-4fe8-b9f0-97bd9d363e5f)

# Menus
As you have possibly noticed, when you launch CTk Theme Builder, the control panel has a menu toolbar. This includes a *File* menu as well as a *Tools* menu, as we see here:

![main-menus](https://github.com/avalon60/ctk_theme_builder/assets/89534395/002721c9-422a-430f-98a8-6a7236e8dbfd)

Note that these are presented differently on MacOS.

The options of the File menu, bear a close correspondence to the buttons displayed on the control panel, whereas the Tools options are only available via the menu toolbar.

### The File Menu


![file-menu](https://github.com/avalon60/ctk_theme_builder/assets/89534395/b2ea6c45-568f-4480-84ae-44abeba35635)

When you first start CTk Theme Builder, if you don't have a theme selected, you will find that most of the *File* menu options are disabled. They only become enabled when you start working on a theme.

The options on the *File* menu, have corresponding buttons in the left hand region of the control panel. Please refer to the section on the Control Panel to read about their function.

### Tools Menu

![tools-menu](https://github.com/avalon60/ctk_theme_builder/assets/89534395/b45fa687-47df-4f9d-ad0d-fad08a8231f3)

The *Tools* menu provides access to:

1. User Preferences
2. Colour Harmonics dialogue
3. About (CTk Theme Builder)

The Colour Harmonics option is only enabled, when you start working on a theme.

Each of these options, are covered in their own dedicated section of the guide. 


# Preferences
The Preferences dialogue is accessed via the *Tools->Preferences* menu option.
The preferences screen will appear something like this:

![preferences](https://github.com/avalon60/ctk_theme_builder/assets/89534395/fbe5926c-919c-4d1e-98be-7af54e91a1a8)

When you start CTk Theme Builder for the very first time, the theme will be set to _GreyGhost_, as we see in the above image.

For new installations, the Preferences dialogue should be the first Port of call.

### Author
For a new installation the Author defaults to the user id that you are logged in as. You can simply over-type this, to whatever suits. The author is embedded into the JSON, of any theme files that you create.


### Control Panel Theme

For a new installation the application defaults to using the GreyGhost theme. If you are not comfortable with this theme, there are a number to choose from. Please be aware that after saving you preferences, the new theme will not come into effect until you re-launch CTk Theme Builder.

### Appearance Mode

This option allows you to choose the Appearance Mode. Changing this effects a change to the Control Panel's  appearance mode. Currently, *Light* and *Dark* modes are supported.
Changing this has an instant effect, once the _Save_ button is pressed. Be aware that the default theme, GreyGhost, will not appear to change when you switch appearance modes - this is by design.

### Tooltips
By default tooltips are enabled. The application is quite generous with tooltips and you might find these useful. However, if you wish you can disable these via this option.

### Colour Palette Labels
If you wish to save some real-estate, you can disable colour palette labels.
By default they are enabled, and you should see something similar to what is shown here:  
  
![palette-labels](https://github.com/avalon60/ctk_theme_builder/assets/89534395/f5545f81-c2a0-4b1f-befe-f6b816d37a77)

### Load Last Theme
If enabled, this causes the last theme you were working on to be automatically opened, when you next start CTk Theme Builder.

### Copy / Paste
Most colour tiles in the application provide *Copy & Paste* functions (some only provide *Copy*), via a right-click to the tile. This way you can copy a colour from one tile and paste it to another.

Linux users should be aware that by default the clipboard contents are emptied if the application is closed. However, there are tools such as *Clipboard Manager*, which can prevent this.

### Single Click Paste
This option is disabled by default. When set to enabled, it activates the single left mouse click to be used to paste colours into a property colour, or palette tile. Be aware that if you enable this, it's all too easy to get mouse-click happy and perform an unintentional paste. If you want to play it safe, stick to using the right click -> context menu to perform a paste operation.

### Adjust Shade Step
This setting allows you to tune the shade step options, which are available when you right click a colour tile. The larger the value chosen, the bigger the colour shade step applied, when the *Lighten Shade/Darken Shade*options are selected.

![shade-steps](https://github.com/avalon60/ctk_theme_builder/assets/89534395/7cc8cfb9-e5c9-4c5b-9b8c-d71541a70224)

*Shade Steps* influence the behaviour demonstrated in the above image, which is taken from the *Colour Mappings* region of the *Control Panel*. This is covered later, in the *Control Panel* section. 

### Colour Picker
Right clicking a colour tile, on any update-able tile, will cause a floating menu to appear. Included on the menu is a *Colour Picker* option. When selected a pop-up will appear, allowing you to choose, or paste a colour.

![colour-picker](https://github.com/avalon60/ctk_theme_builder/assets/89534395/e5ecbb83-c875-47b7-9320-aedad20d30ef)


When the colour picker appears, the initial colour will automatically reflect the colour of the tile, from which it was invoked.

The appearance of the Colour Picker will vary, depending on your operating system. On Linux you will see the Tkinter, built-in colour picker, whereas for example on Windows, you will see a Windows native colour picker. 
 
### Harmony Shade Step
This setting allows you to tune the behaviour of the colours generated in the Colour Harmonics dialogue. The larger the selected value, the bigger the difference in consecutive shades generated to the right side of the dialogue.

![colour-harmonics](https://github.com/avalon60/ctk_theme_builder/assets/89534395/417e0afe-6d92-4483-96bb-7b8733cc4581)
The *Harmonics Panel* is cover a little later.

### Themes Location
The default folder for storing your themes, is the ctk\_theme\_builder/user_themes folder. However you can elect to change this by clicking the Themes Folder icon. This will allow you to navigate to, and select an alternative location.

NOTE: If you change the theme location at any time, you will need to manually copy / paste your themes from the old location, to the new location, as required.  


# Control Panel

![control-panel2](https://github.com/avalon60/ctk_theme_builder/assets/89534395/04ea2241-2467-4fb1-8ab2-3fbdcffa9856)

Here we see the Control Panel. This is where the real work goes on. 

The Main Controls are accessed via selections and buttons on the left hand side. 

The entries we see under *Widget Geometry* are buttons which allow you to define the respective, non-colour, widget properties.

The area immediately below *widget Geometry* is the *Theme Palette*. This is basically a holding space for your common theme colours.

Finally the Colour Mappings region is where you assign colours to CustomTkinter widget properties.

We will go into detail, on these various regions, in the subsequent sections.


## Main Controls
The first thing to note, is that as with the _File_ menu options, until a theme has been opened, most  of the buttons are disabled. CTk Theme Builder maintains the state of your session, and enables / disables buttons and options accordingly. For example, if you save your theme, the _Save_ button becomes disabled until you modify your theme again.

#### Select Theme
This is a drop-down menu which allows you to select a theme, on which to begin work. The list is generated based upon entries in your user theme location (please see the Preferences section).

Note that a "TestCard" theme is automatically included when you install CTk Theme Builder. This intentionally includes some gaudy colours. If you are new to CustomTkinter theme files, you can use this as a scratch theme, to experiment and discover how widget property changes, effect changes in the widget rendering. Be aware that this theme will be overwritten whenever you perform an upgrade to the app.

#### Preview Appearance
This option allows you to switch the *Preview Panel* (covered in a later section)  between the CustomTkinter *Light* and *Dark* modes. 

This also causes the *Theme Palette* and *Colour Mappings* regions to update, to reflect the widget colour properties configured for the selected mode, for the theme that you are working on.

#### Top Frame
The default position for the *Top Frame* is set to enabled. If enabled this renders the Preview Panel, in such as way as to emulate the rendered widgets inside an embedded (top) frame.

When CustomTkinter renders a top frame, it uses the top\_fg\_color property to determine the frame's foreground colour. This is often a contrasting shade (or colour) to the parent frame's fg\_colour.

It's a good idea to toggle this switch, to ensure that your widgets render well, in both modes.

#### Render Disabled
You should occasionally enable this switch, to see how your widget colours render, when they have been disabled. 

This allows you to ensure that the disabled text colour/shade is discernible against the containing frame's foreground colour.

#### Properties View
The *Properties View* allows you to control the way widgets (or widget groupings) are presented for selection in the *Filter View* drop-down. There is a *Basic*view as well as a *Categorised* view. See the next section, for more details on these.

#### Filter View
Depending on the *Properties View* setting, this drop-down menu allows you to control which properties are listed in the *Colour Mappings* region. 

In *Basic* mode, you can select *All*, to render all property widgets, or you can select an individual widget.

In *Categorised* mode, you can also select *All*, or you can select groups of widgets, based on common attribute. For example, all widgets which allow text entry, or which have scrollable components.


![categorised_view](https://github.com/avalon60/ctk_theme_builder/assets/89534395/c0f3ca8b-aa76-4999-b189-b49739dd10ce)

In the above image, we have the *Categorised* view selected and we are filtering on widgets with buttons.

#### Refresh Preview
The *Refresh Preview* button, causes a full reload of the *Preview Panel*. 

This can be useful where you have been changing the state of the widgets in the *Preview Panel*. For example, you may have entered text in a CTkEntry widget and wish to reset its state, such that it re-renders the placeholder text. 

#### Reset Button
This allows you to roll back any changes to your last *Save*. When this is done, the *Preview Panel* is also flashed back to the reset state. 
  
We all make mistakes ;o)

#### New Theme
As this suggests, this allows you to create a brand new theme. When pressed a pop-up dialogue will be displayed, where you can enter the new theme name. When you click *OK* on the New Theme pop-up dialog, the theme is created and automatically saved. 

If you have been working on another theme, and have unsaved changes, a pop-up dialogue will appear, asking you if you wish to discard your changes.

#### Sync Modes

The Sync Modes button, operates against the **displayed** widget colour properties, which you have currently selected via the *Filter View*, and which are rendered in the *Colour Mappings* region. It's effect is to copy the colour properties to the complementary appearance mode. For example, if you have *Dark Mode* selected, the colour properties will be copied over to the *Light Mode* property counter-parts.

Here we see an example, where we have selected the *Categorised* view and filtered based on widgets with borders:  
  
![sync-modes](https://github.com/avalon60/ctk_theme_builder/assets/89534395/1d731e2a-f0c6-49d9-a04a-0167d34cbc6a)

We can see from the display, that we are working on the *Dark* appearance mode (Dark Mode button is a lighter colour - enabled). The properties showing are all border properties for various widget types. Using the *Sync Modes* here, would result in the border colours on display, being copied to the *Light* mode properties.

This operation does not include the Theme Palette properties.

#### Sync Palette
The Theme Palette holds a separate set of colours, for each of your theme's appearance modes. This function behaves in a similar fashion to the *Sync Modes* button, except that it only effects changes to the *Theme Palette* colours.
 
#### Remaining Buttons
Hopefully you will find the functionality of *Save*, *Save As*, *Delete* and *Quit* somewhat obvious.
Needless to say, if you have any unsaved changes, you will be prompted with a choice of what you wish to do with them.

NOTE: You should use the CTk Theme Builder app to delete unwanted theme files. Deleting them from outside of the application, can lead to orphaned template files, accumulating on disk.

## Widget Geometry
The *Widget Geometry* buttons allow you to target a particular widget type, and adjust its geometry properties (corner radius, border width etc).

![geometry-dialog](https://github.com/avalon60/ctk_theme_builder/assets/89534395/2651f55e-8281-44b8-8c31-f7cf760eb228)


To make adjustments, move the sliders and the rendered widget will respond, to provide a mini-preview or the effects of your changes.

Depending on the widget type, different property sliders may appear.

When you *Save* your changes, the preview panel will also update the rendering accordingly, for any matching widget types.

## Theme Palette
Depending on your methodology, you might find the *Theme Palette*, more or less useful. It's an area where you can persist colours, whilst switching between *Filter View* selections, as well as between theme maintenance sessions. 

If you are more methodical, you can use it to plan your colours, in order to strive for better consistency. For example, you may want to use the same colour / shade for most of your widget borders. 
  
  Be aware that the *Colour Harmonics* dialogue has a *copy to Palette** button. When pressed, this will cause the keystone colour, and the generated base colours, to be copied to the first tiles in the Theme Palette (*Scratch1, Scratch2* etc. up to 4 colours in total, depending on the selected harmony method).
  
If you right-click a tile in the *Theme Palette* region, you will be presented with a floating  menu. This will provide options for copying, pasting or various options for adjusting the colour of the selected tile. 

If you don't care for the labels which appear below the Theme Palette tiles, they can be switched off, via the Tools > Preferences menu selection.
  
## Colour Mappings Region
Here is where you target and manage individual widget colour properties. This region reflects the colour properties of the widgets selected via the *Properties View / Filter View* widgets. Depending on your selection, you will see the widget colour properties, for one, several, or all widget types.

As with the *Theme Palette* tiles, floating menus are available, which allow you to perform operations, as we see here:  
  
![floating-menu](https://github.com/avalon60/ctk_theme_builder/assets/89534395/8696d5f7-292a-4272-8fed-f506f58878eb)

#### Shade Adjustment Operations  
The *Lighter Shade/Darker Shade* options, cause incremental adjustments in the shade of the colour, based upon the *Adjust Shade Step*, setting described under user *Preferences*. 

As you can see there are multiplier options, which allow you to magnify the shade step adjustment. 

The *Lighter Shade/Darker Shade* controls maintain the differential between the RGB channels. This means that as soon as one of the channels touches the min or max allowed values (decimal 0, 255), further adjustments have no effect.

![colour-differental-bound](https://github.com/avalon60/ctk_theme_builder/assets/89534395/537b7c7e-3473-43b8-bf82-82ca16df2de5)

So in the colour example above, we can see that the red channel is maxed out (0xff = 255). This would therefore block any Lighter Shade operations from having any effect. This is done, to prevent the colour from mutating.

#### Copying & Pasting Colours

By using the right mouse click, you can also Copy / Paste colours between tiles. 



# Colour Harmonics

The *Colour Harmonics* panel, is accessed via the *Tools* menu, and only becomes available when you open a theme.

The idea behind it, is that you can generate colours, around which you can base a new theme.


![harmonics](https://github.com/avalon60/ctk_theme_builder/assets/89534395/26160748-c1c9-4d6c-9829-715522932459)


Amongst other functions, right clicking the *Keystone Colour* tile, presents a *Paste* option, allowing you to seed a hex colour code, which is then used to generate complementary colours. The core generated colours are rendered below the Keystone Colour* on the left. 

The tiles to the right are produced by taking the core colours, and copying them to the first row. Theses are then used to produce shade variants, with each successive row being darkened slightly, as you scan down from the top row of colours, to the bottom. 

You can of course, copy one of the generated darker shades and paste it to the *Keystone Colour*, causing it to generate another set of shade variants. 

### Method Options

The drop-down menu, below the *Keystone Colour* tile, allows you the choice of a number of harmony methods:

* Analogous (2)
* Complementary (1)
* Split-complementary (2)
* Triadic (2)
* Tetradic (3)

The numbers in parentheses, indicate the number of generated complementary colours, associated with the method chosen.

You can read more about the methods [here](https://www.oberlo.com/blog/color-combinations-cheat-sheet)

### Copy to Palette

When pressed, the *Copy to Palette* button, causes the *Keystone Colour*, and the generated colours, immediately below it, to be copied to the *Scratch* tiles on the theme's Theme Palette display. 

### Tag Keystone
The *Tag Keystone* button, causes the Keystone colour and the chosen harmony method to be tagged to your theme. If you subsequently open the *Colour Harmonics* panel, for a given theme, the colours will be restored to the same state, as per when they were tagged.  


# Preview Panel
The *Preview Panel* is launched as soon as a theme is opened. This panel listens for instructions, sent by the *Control Panel*, which tell it what widget   properties, to adjust within the display. It's job, is to make the task of maintaining themes as WYSIWYG as possible.

![preview-panel](https://github.com/avalon60/ctk_theme_builder/assets/89534395/f785217f-4a12-4a27-a4fd-634a8264c9ee)


Whenever you change a widget property, whether that be a colour property or a property relating to the widget's geometry, a message is sent to the *Preview Panel*, instructing it as to what needs updating.

The only way to close the *Preview Panel* is via the *Quit* button, on the *Control Panel* interface. Doing so causes a message to be sent, telling it to close down.

Please refer to *Known Issues & Behaviours* for details on some behaviours of the *Preview Panel*.
 

# The About CTk Theme Builder Dialog

![about](https://github.com/avalon60/ctk_theme_builder/assets/89534395/e37d58b7-6e6b-4291-acb5-77d64f22c5d5)

This is accessible, via the Tools menu.  

Aside from a picture of a cute tekno-colour bear, the About dialogue is useful for confirming the versions of CTk Theme Builder & CustomTkinter you are working with. 

If you are creating an issue on GitHub, you should quote the reported versions on the About dialogue.

# Composite Widgets
This section covers widgets which are composites of other widgets. These are worth mentioning to avoid any confusion.

### CTkScrollableFrame

As you can guess by the name, this is an extension of the CTkFrame widget. With the exception of its label_fg_color property, its other property defaults are taken from CTkFrame and CTkScrollbar. Changing the properties of these widgets, will result in changes to the CTkScrollableFrame widget.

### CTkTabview

The CTkTabview widget is a composite of CTkFrame and CTkSegmentedButton. It has no properties of its own in a theme file and so inherits its defaults from these two widget types.


# Known Issues and Behaviours

### CustomtKinter

#### Colour Property Updates
There are some issues which needed to be worked around, in respect of the *Preview Panel* operations. During release 2.0.0 of CTk Theme Builder, the latest release of CustomTkinter was 5.1.3. This had several associated issues:  
  
1. CTk 5.1.2 CTkCheckBox.configure(text\_color\_disabled=...) causes exception [#1591](https://github.com/TomSchimansky/CustomTkinter/issues/1591)
2. CTk 5.1.2: Omission: Theme JSON property checkmark\_color of CTkCheckBox has no configure option [#1586](https://github.com/TomSchimansky/CustomTkinter/issues/1586)
3. CTk 5.1.2: CTkSegmentedButton property setting issues [#1562](https://github.com/TomSchimansky/CustomTkinter/issues/1562)
4. CTk 5.1.2: CTkOptionMenu.configure(text\_color\_disabled=...) raises exception [#1559](https://github.com/TomSchimansky/CustomTkinter/issues/1559)
5.  CTk 5.1.2: Disabling CTkLabel - no text_color_disabled property (Regression) [#1557](https://github.com/TomSchimansky/CustomTkinter/issues/1557)

CTk Theme Builder has a safety mechanism, allowing it to avoid most of these issues. It does this by taking a less surgical approach to updating the *Preview Panel*. Rather than updating at the widget level, a full top level refresh is performed, tearing down the frames and rebuilding the widgets within the top level. This is not as elegant as the default behaviour, but it does allow you to get on with the task at hand. If / when these issues are discovered to have been fixed, the Preview Panel will be updated accordingly.

In respect of number 5, the *Preview Panel* is unable to compensate, as it has no underlying property to work with. The disabled text colour of a CTkLabel, appears to be decided upon by Tkinter, as though we had rendered a tkinter.Label widget.

#### DropdownMenu

In addition, there is the *DropdownMenu* theme property to consider. You can perhaps think of this as a sub-component, used by *CTkComboBox* and *CTkOptionMenu*. The bottom line is that it is not a widget in its own right. This means that to effect any changes made to it in the *Control Panel*, we currently perform a similar action, to that described above - tearing down and rebuilding the widgets in the *Preview Panel*. Unfortunately these widget types don't currently have configurable properties, allowing the drop-down properties to be changed on the fly.

#### Geometry Updates

1.  CTk 5.1.2: CTkSegmentedButton width property seems to have no effect [	#1533](https://github.com/TomSchimansky/CustomTkinter/issues/1533) 

This issue causes the described geometry property to be ignored.

### CTk Theme Builder
#### Colour Harmonics
You may encounter a situation where, despite having an open theme, the Colour Harmonics option is greyed out (disabled). this doesn't happen that frequently, but if it does. you can work around this by saving any changes and restarting the app.

As soon as I spot the workflow which causes this I will fix it (it's a difficult one to spot).

#### Listener Timeout
When this occurs, the *Control Panel* cannot communicate with the *Preview Panel*, leaving it in a "zombie" state. This should be rare, unless you keep attempting to launch the application whilst another instance of it is already running.

Depending on your operating system, this means that you will need to use xkill, Task manager etc,  to kill the panel.

#### Copy / Paste
Linux users should be aware that by default the clipboard contents are emptied if the application is closed. However, there are tools, such as *Clipboard Manager*, which can prevent this.

#### Floating Menu Options / Transparent Colour Property
When working in the Colour Mappings region, by using the right mouse click, you can Copy / Paste colours between tiles. However for widget properties which have a value set to "transparent", for example CTkLabel > fg_color, this functionality is disabled. In addition the Colour Picker is also disabled.

This will likely be addressed in a future version.