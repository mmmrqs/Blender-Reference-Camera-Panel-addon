# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

'''
Reference Cameras add-on
'''
#--- ### Header
bl_info = {
    "name": "BL UI Widgets",
    "description": "UI Widgets to draw in the 3D view",
    "author": "Jayanam (enhancements by Marcelo M. Marques)",
    "version": (0, 6, 5, 0),
    "blender": (2, 80, 3),
    "location": "View3D",
    "support": "COMMUNITY",
    "category": "3D View",
    "warning": ""
    }
    
#--- ### Change log

#v0.6.5 (08.01.2021) - by Marcelo M. Marques 
#Added: A control to check if the panel can be dragged by the user or must stay locked in position
#Chang: Renamed some local variables so that those become restricted to this class only.

#--- ### Imports
import bpy

from . bl_ui_patch import BL_UI_Patch

class BL_UI_Drag_Panel(BL_UI_Patch): 

    def __init__(self, x, y, width, height):

        RC_POSITION = bpy.context.preferences.addons[__package__].preferences.RC_POSITION
        RC_POS_X = bpy.context.preferences.addons[__package__].preferences.RC_POS_X
        RC_POS_Y = bpy.context.preferences.addons[__package__].preferences.RC_POS_Y
    
        if RC_POSITION:
            if RC_POS_X != -10000 and RC_POS_Y != -10000: 
                # Override input values with the ones saved from last time (any scene/session)
                x = RC_POS_X
                y = RC_POS_Y
        else:
            if bpy.context.scene.get("bl_ui_panel_saved_data") is None:
                pass        
            else:
                # Override input values with the ones saved from last session
                x = bpy.context.scene.get("bl_ui_panel_saved_data")["panX"]
                y = bpy.context.scene.get("bl_ui_panel_saved_data")["panY"]

        # Need to apply scale to compensate for posterior calculations
        over_scale = self.over_scale(10000)/10000 # This to get the raw factors without being rounded or integered
        x = int(round((x / over_scale)))
        y = int(round(((y - height) / over_scale)))

        super().__init__(x,y, width, height)

        self.widgets = []
        
        # Note: bg_style value will always be ignored if the bg_color value is overriden after object initialization.

        self._bg_style = 'NONE'                 # Panel background color styles are: {HEADER,PANEL,SUBPANEL,TOOLTIP,NONE}
        self._bg_color = None                   # Panel background color (defaults to invisible)
        self._outline_color = None              # Panel outline color (defaults to invisible)
        self._roundness = 0                     # Panel corners roundness factor [0..1]
        self._radius = 0                        # Panel corners circular radius
        self._rounded_corners = (0,0,0,0)       # 1=Round/0=Straight, coords:(bottomLeft,topLeft,topRight,bottomRight)
        self._has_shadow = False                # Indicates whether a shadow must be drawn around the panel 

        self._anchored = False    # Indicates whether panel can be dragged around the viewport or not

        self.__drag_offset_x = 0
        self.__drag_offset_y = 0
        self.__is_drag = False

    @property
    def anchored(self):
        return self._anchored

    @anchored.setter
    def anchored(self, value):
        self._anchored = value

    def add_widget(self, widget):
        self.widgets.append(widget)
        
    def add_widgets(self, widgets):
        for widget in widgets:
            self.add_widget(widget)
        
    def layout_widgets(self):
        for widget in self.widgets:
            widget.update(self.x_screen + widget.x, self.y_screen + widget.y)   

    def child_widget_focused(self, x, y):
        for widget in self.widgets:
            if widget.is_in_rect(x, y):
                return True 
        return False
    
    def save_panel_coords(self, x, y):
        # Update the new coord values in the session's saved data dictionary.
        # Note: Because of the scaling logic it was necessary to make this weird correction math below
        area_height = self.get_area_height()
        over_scale = self.over_scale(10000)/10000 # This to get the raw factors without being rounded or integered
        new_x = self.over_scale(x)
        new_y = self.over_scale(area_height - y) - int(self.height * (over_scale - 1))
        bpy.context.scene["bl_ui_panel_saved_data"] = {"panX" : new_x, "panY" : new_y}
        # Update values also in the add-on's preferences properties
        bpy.context.preferences.addons[__package__].preferences.RC_POS_X = new_x
        bpy.context.preferences.addons[__package__].preferences.RC_POS_Y = new_y

    # Overrides base class function
    def update(self, x, y):
        super().update(x,y)
        if self.__is_drag:
            # Inform that widget has shift position so that tooltip know it must be recalculated
            base_class = super().__thisclass__.__mro__[-2]  # This stunt only to avoid hard coding the Base class name
            widget = base_class.g_tooltip_widget
            if widget is None:
                pass
            else:    
                widget.tooltip_moved = True

    # Overrides base class function
    def set_location(self, x, y):
        super().set_location(x,y)
        self.layout_widgets()
    
    # Overrides base class function
    def mouse_down(self, event, x, y):
        if self.child_widget_focused(x, y):
            # Means the focus is on some sub-widget (e.g.: a button)
            return False
        if self.anchored:
            # Means the panel is not draggable
            return False
        if self.is_in_rect(x,y):
            height = self.get_area_height()
            self.__is_drag = True
            self.__drag_offset_x = x - self.x_screen
            self.__drag_offset_y = y - (height - self.y_screen)
            return True
        else:
            return False

    # Overrides base class function
    def mouse_move(self, event, x, y):
        if self.__is_drag:
            area_height = self.get_area_height()
            y_screen_flip = area_height - y
            # Recalculate and update the new position on the viewport
            new_x = x - self.__drag_offset_x
            new_y = y_screen_flip + self.__drag_offset_y
            self.save_panel_coords(new_x, new_y)
            self.update(new_x, new_y)
            self.layout_widgets()
        return False

    # Overrides base class function
    def mouse_up(self, event, x, y):
        self.__is_drag = False
        self.__drag_offset_x = 0
        self.__drag_offset_y = 0
        return False
        