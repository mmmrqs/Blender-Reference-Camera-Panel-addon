# Some Basic Documentation

## Camera Movements Cheat Sheet
![Standard Camera Movements](https://github.com/mmmrqs/Blender-Reference-Camera-Panel-addon/blob/main/media/Camera%20Movements%20Cheat%20Sheet.jpg)

# Blender UI Widgets

The Reference Cameras Panel addon uses my fork of **Jayanam's Blender UI Widgets** for displaying a floating 'Remote Control' panel. This is a collection of UI Widgets that allows the creation of addons with a persistent (modal) draggable floating panel, textboxes, checkboxes, buttons and sliders for **Blender 2.8** and newer versions.

Each widget object has many attributes that can be set by the programmer to customize its appearance and behavior.  One can opt to let the widgets automatically take the appearance of the selected Blender's Theme or can override any of those characteristics individually, and per widget.

The widgets are also fully scalable, bound to Blender's Resolution Scale configuration ("ui_scale") and/or by programmer's customization.  It is also ready to get tied to an Addon Preferences setup page, as can be seen in the included **demo panel** (more about that below).

Not much documentation is available for now, but the code has a lot of annotations to help you out and each module has its mod log listing all added features.  Also, at each module's init method you can find all available attributes described with detailed information.

The GPU module of Blender 2.8 is used for drawing.  This package has a demo panel to showcase all available widgets so that you can install it and have a quick testing.  It also serves as a template or a baseline for creating **your own addons**.  I attempted to add a little bit of each feature to the demo code in order to help starters. You can have it installed by using the alternate **\_\_init\_\_.py** file available in the '\_\_init\_\_backups' folder, so check that out please. 

## Classes relationships for the Remote Control draggable panel
![BL_UI_Widgets UML](https://github.com/mmmrqs/Blender-Reference-Camera-Panel-addon/blob/main/media/Classes_UML1.png)

## Classes relationships for the integrated BL_UI_Widgets
![BL_UI_Widgets UML](https://github.com/mmmrqs/Blender-Reference-Camera-Panel-addon/blob/main/media/Classes_UML2.png)
