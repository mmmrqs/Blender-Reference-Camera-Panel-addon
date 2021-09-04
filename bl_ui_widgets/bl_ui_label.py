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

#--- ### Header
bl_info = {
    "name": "BL UI Widgets",
    "description": "UI Widgets to draw in the 3D view",
    "author": "Marcelo M. Marques (fork of Jayanam's original project)",
    "version": (1, 0, 0),
    "blender": (2, 80, 75),
    "location": "View3D > viewport area",
    "support": "COMMUNITY",
    "category": "3D View",
    "warning": "Version numbering diverges from Jayanam's original project",
    "doc_url": "https://github.com/mmmrqs/bl_ui_widgets",
    "tracker_url": "https://github.com/mmmrqs/bl_ui_widgets/issues"
    }    
    
#--- ### Change log

#v1.0.0 (09.01.2021) - by Marcelo M. Marques 
#Added: Logic to scale the label's text according to both Blender's ui scale configuration and this addon 'preferences' setup
#Added: 'style' property that allows the text to take different style colors per Blender's user themes.
#Added: 'text_title' property that allows the highlight color to be overriden by code.
#Added: 'text_kerning' property that allows the text kerning to be adjusted accordingly.
#Added: 'text_rotation' property that allows the text to be painted in any direction (value must be in radians).
#Added: 'clip' property that allows the text to be clipped (value must be a 4_coordinates tuple)
#Added: Shadow and Kerning related properties that allow the text to be painted using these characteristics.
#Added: Colors, Size, Shadow and Kerning attributes default to values retrieved from user theme (can be overriden).
#Fixed: New call to verify_screen_position() so that object behaves alright when viewport is resized.

#--- ### Imports
import bpy
import blf

from . bl_ui_widget import BL_UI_Widget

class BL_UI_Label(BL_UI_Widget): 
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

        self._text = "Label"
        self._style = 'REGULAR'                 # Label color style options are: {REGULAR,TITLE,BOX,BUTTON,CHECKBOX,TOOLTIP}
        self._text_color = None                 # Label normal color 
        self._text_title = None                 # Label titles color 
        
        self._text_size = None                  # Label size in points (pixels)
        self._text_kerning = None               # Label kerning (True/False)
        self._text_rotation = 0.0               # Angle value in radians (90 is vertical)

        self._shadow_size = None                # Label shadow size
        self._shadow_offset_x = None            # Label shadow offset x (positive goes right)
        self._shadow_offset_y = None            # Label shadow offset y (negative goes down)
        self._shadow_color = None               # Label shadow color [0..1] = gray tone, from dark to clear
        self._shadow_alpha = None               # Label shadow alpha value [0..1]
        
        self._clip = None                       # Clipping coordinates (populated only by BL_UI_Button class)
        
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def text_color(self):
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value

    @property
    def text_title(self):
        return self._text_title

    @text_title.setter
    def text_title(self, value):
        self._text_title = value

    @property
    def text_size(self):
        return self._text_size

    @text_size.setter
    def text_size(self, value):
        self._text_size = value
            
    @property
    def text_kerning(self):
        return self._text_kerning

    @text_kerning.setter
    def text_kerning(self, value):
        self._text_kerning = value

    @property
    def text_rotation(self):
        return self._text_rotation

    @text_rotation.setter
    def text_rotation(self, value):
        self._text_rotation = value

    @property
    def shadow_size(self):
        return self._shadow_size

    @shadow_size.setter
    def shadow_size(self, value):
        self._shadow_size = value
            
    @property
    def shadow_offset_x(self):
        return self._shadow_offset_x

    @shadow_offset_x.setter
    def shadow_offset_x(self, value):
        self._shadow_offset_x = value
            
    @property
    def shadow_offset_y(self):
        return self._shadow_offset_y

    @shadow_offset_y.setter
    def shadow_offset_y(self, value):
        self._shadow_offset_y = value
            
    @property
    def shadow_color(self):
        return self._shadow_color

    @shadow_color.setter
    def shadow_color(self, value):
        self._shadow_color = value

    @property
    def shadow_alpha(self):
        return self._shadow_alpha

    @shadow_alpha.setter
    def shadow_alpha(self, value):
        self._shadow_alpha = value
            
    @property
    def clip(self):
        return self._clip

    @clip.setter
    def clip(self, value):
        self._clip = value

    # Overrides base class function
    def my_style(self):
        if self._style == 'TITLE':
            style = "panel_title"
        elif self._style == 'REGULAR' or self._style == 'BOX':
            style = "widget_label"
        elif self._style == 'BUTTON' or self._style == 'CHECKBOX' or self._style == 'TOOLTIP':
            style = "widget"
        else:    
            style = "widget_label"
        return style

    # Overrides base class function
    def is_in_rect(self, x, y):
        # This type of object must not react to mouse events
        return False
        
    # Overrides base class function
    def update(self, x, y):        
        self.x_screen = x
        self.y_screen = y
        
    # Overrides base class function
    def draw(self):
        if not self._is_visible:
            area_height = self.get_area_height()
            self.verify_screen_position(area_height)
            return

        if self._style == 'REGULAR' or self._style == 'TOOLTIP':
            if self._text_color is None:
                # From Preferences/Themes/3D Viewport/"Theme Space"
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.view_3d, "space")               
                text_color = tuple(widget_style.button_text) + (1.0,)
            else:
                text_color = self._text_color 
                
        elif self._style == 'TITLE':
            if self._text_title is None:
                # From Preferences/Themes/3D Viewport/"Theme Space"
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.view_3d, "space")               
                text_color = tuple(widget_style.button_title) + (1.0,)
            else:
                text_color = self._text_title

        elif self._style == 'BOX':
            if self._text_color is None:
                # From Preferences/Themes/User Interface/"Box"
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.user_interface, "wcol_box")               
                text_color = tuple(widget_style.text) + (1.0,)
            else:
                text_color = self._text_color
        else:
            if self._text_color is None:
                # Warning error out color :-)
                text_color = (1,0,0,1)
            else:
                text_color = self._text_color 
                
        if not self._is_enabled:
            if text_color[0] > 0.5:
                # Take the text color and "dark" it by 30%
                text_color = self.shade_color(text_color, 0.3)
            else:    
                # Take the text color and "tint" it by 30%
                text_color = self.tint_color(text_color, 0.3)

        theme = bpy.context.preferences.ui_styles[0]
        widget_style = getattr(theme, self.my_style())
        if self._text_size is None:
            text_size = widget_style.points 
        else:
            text_size = self.leverage_text_size(self._text_size, self.my_style())

        if self._style == 'TOOLTIP':
            text_size = int(self.ui_scale(text_size))
        else:
            text_size = int(self.over_scale(text_size))
            
        text_kerning = (widget_style.font_kerning_style == 'FITTED') if self._text_kerning is None else self._text_kerning

        shadow_size  = widget_style.shadow if self._shadow_size is None else self._shadow_size   
        shadow_offset_x = widget_style.shadow_offset_x if self._shadow_offset_x is None else self._shadow_offset_x 
        shadow_offset_y = widget_style.shadow_offset_y if self._shadow_offset_y is None else self._shadow_offset_y 
        shadow_color = widget_style.shadow_value if self._shadow_color is None else self._shadow_color 
        shadow_alpha = widget_style.shadow_alpha if self._shadow_alpha is None else self._shadow_alpha 

        # These few statements below to fix the shadow size into a valid value otherwise blf() errors out
        if shadow_size == 0:
            pass
        else:
            if shadow_size < 0:
                shadow_size = 0 
            else:
                shadow_size = 3 if (shadow_size < 3) else shadow_size
                shadow_size = 5 if (shadow_size > 3) else shadow_size

        # DOCUMENTATION:
        # blf.shadow(fontid, level, r, g, b, a)
        # Shadow options, enable/disable using SHADOW
        # Parameters:
        # fontid (int) – The id of the typeface as returned by blf.load(), for default font use 0.
        # level (int) – The blur level, can be 3, 5 or 0.
        # r (float) – Shadow color (red   channel 0.0 - 1.0)
        # g (float) – Shadow color (green channel 0.0 - 1.0)
        # b (float) – Shadow color (blue  channel 0.0 - 1.0)
        # a (float) – Shadow color (alpha channel 0.0 - 1.0)

        # blf.shadow_offset(fontid, x, y)
        # Set the offset for shadow text.
        # Parameters:
        # fontid (int) – The id of the typeface as returned by blf.load(), for default font use 0.
        # x (float) – Horizontal shadow offset value in pixels (positive is right, negative is left)
        # y (float) – Vertical shadow offset value in pixels  (positive is up, negative is down)

        if shadow_size:
            blf.enable(0, blf.SHADOW)
            blf.shadow(0, shadow_size, shadow_color, shadow_color, shadow_color, shadow_alpha)
            blf.shadow_offset(0, shadow_offset_x, shadow_offset_y)
        if self._text_rotation:
            blf.enable(0, blf.ROTATION)
            blf.rotation(0, self._text_rotation)
        if text_kerning:
            blf.enable(0, blf.KERNING_DEFAULT)
        if not self._clip is None:
            blf.enable(0, blf.CLIPPING)
            x_min = self.over_scale(self._clip[0])
            y_max = self.over_scale(self._clip[1])
            x_max = x_min + self.over_scale(self._clip[2])
            y_min = y_max - self.over_scale(self._clip[3])
            blf.clipping(0, x_min, y_min, x_max, y_max)

        area_height = self.get_area_height()
        
        self.verify_screen_position(area_height)

        blf.size(0, text_size, 72)

        blf.position(0, self.over_scale(self.x_screen), self.over_scale(self.y_screen), 0)
            
        r, g, b, a = text_color

        blf.color(0, r, g, b, a)
        
        blf.draw(0, self._text)
        
        if shadow_size:
            blf.disable(0, blf.SHADOW)
        if self._text_rotation:
            blf.disable(0, blf.ROTATION)
        if text_kerning:
            blf.disable(0, blf.KERNING_DEFAULT)
        if not self._clip is None:
            blf.disable(0, blf.CLIPPING)
