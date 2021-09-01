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
    "author": "Marcelo M. Marques",
    "version": (1, 0, 0),
    "blender": (2, 80, 75),
    "location": "View3D > viewport area",
    "support": "COMMUNITY",
    "category": "3D View",
    "warning": "",
    "doc_url": "https://github.com/mmmrqs/bl_ui_widgets",
    "tracker_url": "https://github.com/mmmrqs/bl_ui_widgets/issues"
    }    
    
#--- ### Change log

#v1.0.0 (09.01.2021) - by Marcelo M. Marques 
#Added: This new class to paint custom rectangles on screen. Useful for creating header and subpanel areas.
#       It is used as a base class for the following widgets:
#       :BL_UI_Drag_Panel, BL_UI_Button, BL_UI_Slider, BL_UI_Checkbox and BL_UI_Tooltip.

#--- ### Imports
import bpy
import time

from . bl_ui_widget import BL_UI_Widget

class BL_UI_Patch(BL_UI_Widget): 

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
 
        # Note: '_style' value will always be ignored if the bg_color value is overriden after object initialization.

        self._style = 'NONE'                    # Patch background color styles are: {HEADER,PANEL,SUBPANEL,BOX,TOOLTIP,NONE}
        self._bg_color = None                   # Patch background color (defaults to invisible)
        self._shadow_color = None               # Panel shadow color (defaults to invisible)
        self._outline_color = None              # Panel outline color (defaults to invisible)
        self._roundness = 0                     # Patch corners roundness factor [0..1]
        self._radius = 0                        # Patch corners circular radius
        self._rounded_corners = (0,0,0,0)       # 1=Round/0=Straight, coords:(bottomLeft,topLeft,topRight,bottomRight)
        self._has_shadow = False                # Indicates whether a shadow must be drawn around the patch 
        
        self._image = None                      # Image file to be loaded
        self._image_size = (24, 24)             # Image size in pixels; values are (width, height)
        self._image_position = (4, 2)           # Image position inside the patch area; values are (x, y)
        
        self.__image_file = None
        self.__image_time = 0

    @property
    def bg_color(self):
        return self._bg_color

    @bg_color.setter
    def bg_color(self, value):
        self._bg_color = value

    @property
    def shadow_color(self):
        return self._shadow_color

    @shadow_color.setter
    def shadow_color(self, value):
        self._shadow_color = value

    @property
    def outline_color(self):
        return self._outline_color

    @outline_color.setter
    def outline_color(self, value):
        self._outline_color = value 
        
    @property
    def roundness(self):
        return self._roundness

    @roundness.setter
    def roundness(self, value):
        if value is None:
            self._roundness = None
        elif value < 0:
            self._roundness = 0.0
        elif value > 1:
            self._roundness = 1.0
        else:
            self._roundness = value
        
    @property
    def corner_radius(self):
        return self._radius

    @corner_radius.setter
    def corner_radius(self, value):
        self._radius = value 
        
    @property
    def rounded_corners(self):
        return self._rounded_corners

    @rounded_corners.setter
    def rounded_corners(self, value):
        self._rounded_corners = value

    @property
    def shadow(self):
        return self._has_shadow

    @shadow.setter
    def shadow(self, value):
        self._has_shadow = value

    def set_image_size(self, image_size):
        self._image_size = image_size

    def set_image_position(self, image_position):
        self._image_position = image_position

    def set_image(self, rel_filepath):
        self.__image_file = rel_filepath
        self.__image_time = time.time()
        try:
            self._image = bpy.data.images.load(self.__image_file, check_existing=True)   
            self._image.gl_load()
            self._image.pack(as_png=True)
        except:
            pass

    # Overrides base class function
    def is_in_rect(self, x, y):
        """
           The statement with super() is equivalent to writing either one of the following,
           but with the advantage of not having the class name hard coded.
            - if type(self).__name__ == "BL_UI_Patch": 
            - if type(self) is BL_UI_Patch:
        """    
        # This distincts whether it is the Base or a Derived class
        if super().__self_class__ is super().__thisclass__:    
            # This object type must not react to mouse events
            return False
        else:
            return super().is_in_rect(x,y)

    # Overrides base class function
    def draw(self):      

        super().draw()

        if not self._is_visible:
            return
            
        # Attempt to refresh the image because it has an issue that causes it to black out after a while
        if self._image is not None:
            if time.time() - self.__image_time >= 10:
                self.set_image(self.__image_file)
        