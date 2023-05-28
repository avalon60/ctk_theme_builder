[<- Back](user_guide.md)
# Known Issues and Behaviours

### CustomtKinter

#### Colour Property Updates
There are some issues which needed to be worked around, in respect of the *Preview Panel* operations. During release 2.0.0 of CTk Theme Builder, the latest release of CustomTkinter was 5.1.3. This had several associated issues:  
  
1. CTk 5.1.2 CTkCheckBox.configure(text\_color\_disabled=...) causes exception [#1591](https://github.com/TomSchimansky/CustomTkinter/issues/1591)
2. CTk 5.1.2: Omission: Theme JSON property checkmark\_color of CTkCheckBox has no configure option [#1586](https://github.com/TomSchimansky/CustomTkinter/issues/1586)
3. CTk 5.1.2: CTkSegmentedButton property setting issues [#1562](https://github.com/TomSchimansky/CustomTkinter/issues/1562)
4. CTk 5.1.2: CTkOptionMenu.configure(text\_color\_disabled=...) raises exception [#1559](https://github.com/TomSchimansky/CustomTkinter/issues/1559)
5.  CTk 5.1.2: Disabling CTkLabel - no text_color_disabled property (Regression) [#1557](https://github.com/TomSchimansky/CustomTkinter/issues/1557)

CTk Theme Builder has a safety mechanism, allowing it to avoid most of these issues. It does this by taking a less surgical approach to updating the *Preview Panel*. Rather than update at the widget level, a full top level refresh is performed, tearing down the frames and rebuilding the widgets within the top level. This is not as elegant as the default behaviour, but it does allow you to get on with the task at hand. If / when these issues are discovered to have been fixed, the Preview Panel will be updated accordingly.

In respect of number 5, the *Preview Panel* is unable to compensate, as it has no underlying property to work with. The disabled text colour of a CTkLabel, appears to be decided upon by Tkinter, as though we had rendered a tkinter.Label widget.

#### DropdownMenu

In addition,there is the *DropdownMenu* theme property to consider. You can perhaps think of this as a sub-component, used by *CTkComboBox* and *CTkOptionMenu*. The bottom line is that it is not a widget in its own right. This means that to effect any changes made to it in the *Control Panel*, we currently perform a similar action, to that described above - tearing down and rebuilding the widgets in the *Preview Panel*.

This is possibly something that can be improved in a future version of CTk Theme Builder.

#### Geometry Updates

1.  CTk 5.1.2: CTkSegmentedButton width property seems to have no effect [	#1533](https://github.com/TomSchimansky/CustomTkinter/issues/1533) 

This issue causes the described geometry property to be ignored.

### CTk Theme Builder
#### Colour Harmonics
You may encounter a situation where, despite having an open theme, the Colour Harmonics option is greyed out (disabled). You can work around this by saving any changes and restarting the app.

As soon as I spot the workflow which causes this I will fix it. (It's a difficult one to spot)

#### Listener Timeout
When this occurs, the *Control Panel* cannot communicate with the *Preview Panel*, leaving it in a "zombie" state. This should be rare, unless you keep attempting to launch the application whilst an instance of it is already running.

Depending on your operating system, this means that you will need to use xkill, Task manager etc,  to kill the panel.

[<- Back](user_guide.md)