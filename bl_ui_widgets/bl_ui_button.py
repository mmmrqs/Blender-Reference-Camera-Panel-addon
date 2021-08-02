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
#Added: Logic to scale the button according to both Blender's ui scale configuration and this addon 'preferences' setup
#Added: 'textwo' property and coding to allow a second line of text in the button's caption (value is string). 
#        The 1 line or 2 lines are always centered both in horizontal and vertical dimensions.
#Added: 'textwo_size' property to allow different size from the other text line (value is integer). 
#Added: 'textwo_color' property to allow different color from the other text line (value is standard color tuple). 
#Added: 'text_highlight' and 'textwo_highlight' properties to allow different text colors on the selected button.
#Added: 'outline_color' property to allow different color on the button outline (value is standard color tuple). 
#Added: 'roundness' property to allow the button to be painted with rounded corners,
#        same as that property available in Blender's user themes and it works together with 'rounded_corners' below.
#Added: 'corner_radius' property to allow a limit for the roundness curvature, more useful when 'roundness' property 
#        is not overriden by programmer and the one from Blender's user themes is used instead.
#Added: 'rounded_corners' property and coding to allow the button to be painted with rounded corners (value is a 4 elements tuple).
#        Each elements is a boolean value (0 or 1) which indicates whether the corresponding corner is to be rounded or straight
#        in the following clockwise sequence: bottom left, top left, top right, bottom right. 
#Added: 'shadow' property and coding to allow the button to be painted with a shadow (value is boolean).
#Added: Logic to allow a button to be disabled (darkned out) and turned off to user interaction.
#Added: An internal third state for the button to allow it to stay in a state of 'pressed' (similar to a radio button).
#Added: 'mouse_up_over' internal function to control the button 'pressed' state. It is called by BL_UI_Widget class 
#        and allows the wrap up of events when the user finishes clicking a button.
#Added: 'set_button_pressed' function to allow assignment of an external function to be called by 'mouse_up_func' and 'mouse_up_over'.
#Added: 'set_mouse_up' function to allow assignment of an external function to be called by internal 'mouse_up_func'.
#Added: Shadow and Kerning related properties that allow the text to be painted using these characteristics.
#Added: Size, Shadow and Kerning attributes default to values retrieved from user theme (may be overriden by programmer).
#Fixed: New call to verify_screen_position() so that object behaves alright when viewport is resized.
#Chang: Made it a subclass of 'BL_UI_Patch' instead of 'BL_UI_Widget' so that it can inherit the layout features from there.
#Chang: Instead of hardcoded logic it is now leveraging 'BL_UI_Label' to paint the button text lines.
#Fixed: The calculation of vertical text centering because it was varying depending on which letters presented in the text.

#--- ### Imports
import bpy
import blf

from . bl_ui_patch import BL_UI_Patch
from . bl_ui_label import BL_UI_Label

class BL_UI_Button(BL_UI_Patch): 
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

        # Note: bg_style value will always be ignored if the bg_color value is overriden after object initialization.

        self._text = "Button"
        self._textwo = ""
        self._text_color = None                 # Button text color (added missing alpha value) 
        self._text_highlight = None             # Button high color (added missing alpha value) 
        self._textwo_color = None               # Button text color (added missing alpha value) 
        self._textwo_highlight = None           # Button high color (added missing alpha value) 

        self._bg_style = None                   # (Not used for this object type)
        self._bg_color = None                   # Button face color (when pressed state == 0)
        self._selected_color = None             # Button face color (when pressed state == 3)
        self._outline_color = None              # Button outline color
        self._roundness = None                  # Button corners roundness factor [0..1]
        self._radius = 10                       # Button corners circular radius 
        self._rounded_corners = (1,1,1,1)       # 1=Round/0=Straight, coords:(bottomLeft,topLeft,topRight,bottomRight)
        self._has_shadow = True                 # Indicates whether a shadow must be drawn around the button 

        self._text_size = None                  # Button text line 1 size
        self._textwo_size = None                # Button text line 2 size
        
        self._text_kerning = None               # Button text kerning (True/False)
        self._text_shadow_size = None           # Button text shadow size
        self._text_shadow_offset_x = None       # Button text shadow offset x (potitive goes right)
        self._text_shadow_offset_y = None       # Button text shadow offset y (negative goes down)
        self._text_shadow_color = None          # Button text shadow color [0..1] = gray tone, from dark to clear
        self._text_shadow_alpha = None          # Button text shadow alpha value [0..1]

        self._textpos = (x, y)

        self.__state = 0

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, value):
        self.__state = value

    @property
    def selected_color(self):
        return self._selected_color

    @selected_color.setter
    def selected_color(self, value):
        self._selected_color = value 
        
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value.strip()
                
    @property
    def text_size(self):
        return self._text_size

    @text_size.setter
    def text_size(self, value):
        self._text_size = value

    @property
    def text_color(self):
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value

    @property
    def text_highlight(self):
        return self._text_highlight

    @text_highlight.setter
    def text_highlight(self, value):
        self._text_highlight = value

    @property
    def textwo(self):
        return self._textwo

    @textwo.setter
    def textwo(self, value):
        self._textwo = value.strip()
                
    @property
    def textwo_size(self):
        return self._textwo_size

    @textwo_size.setter
    def textwo_size(self, value):
        self._textwo_size = value

    @property
    def textwo_color(self):
        return self._textwo_color

    @textwo_color.setter
    def textwo_color(self, value):
        self._textwo_color = value

    @property
    def textwo_highlight(self):
        return self._textwo_highlight

    @textwo_highlight.setter
    def textwo_highlight(self, value):
        self._textwo_highlight = value

    @property
    def text_kerning(self):
        return self._text_kerning

    @text_kerning.setter
    def text_kerning(self, value):
        self._text_kerning = value

    @property
    def text_shadow_size(self):
        return self._text_shadow_size

    @text_shadow_size.setter
    def text_shadow_size(self, value):
        self._text_shadow_size = value

    @property
    def text_shadow_offset_x(self):
        return self._text_shadow_offset_x

    @text_shadow_offset_x.setter
    def text_shadow_offset_x(self, value):
        self._text_shadow_offset_x = value

    @property
    def text_shadow_offset_y(self):
        return self._text_shadow_offset_y

    @text_shadow_offset_y.setter
    def text_shadow_offset_y(self, value):
        self._text_shadow_offset_y = value

    @property
    def text_shadow_color(self):
        return self._text_shadow_color

    @text_shadow_color.setter
    def text_shadow_color(self, value):
        self._text_shadow_color = value

    @property
    def text_shadow_alpha(self):
        return self._text_shadow_alpha

    @text_shadow_alpha.setter
    def text_shadow_alpha(self, value):
        self._text_shadow_alpha = value

    def set_button_pressed(self, button_pressed_func):
        self.button_pressed_func = button_pressed_func   

    def button_pressed_func(self, widget):
        # This must return False when function is not overriden, so that button does 
        # not turn into pressed mode everytime the user clicks over it. 
        return False
                 
    # Overrides base class function
    def set_mouse_down(self, mouse_down_func):
        self.mouse_down_func = mouse_down_func   
                 
    # Overrides base class function
    def mouse_down_func(self, widget, event, x, y):
        # This must return True when function is not overriden, so that button action 
        # only works while mouse is over the button (that is while it is_in_rect(x,y)).
        return True

    # Overrides base class function
    def set_mouse_up(self, mouse_up_func):
        self.mouse_up_func = mouse_up_func   
                 
    # Overrides base class function
    def mouse_up_func(self, widget, event, x, y):
        # This must return True when function is not overriden, so that button action 
        # only works while mouse is over the button (that is while it is_in_rect(x,y)).
        return True

    # Overrides base class function
    def update(self, x, y):        
        super().update(x, y)
        self._textpos = [x, y]
        
    # Overrides base class function
    def set_colors(self):
        if not self.enabled:
            if self._bg_color is None:
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.user_interface, "wcol_tool")
                color = widget_style.inner
            else:
                color = self._bg_color 
            # When button is disabled dark the "state 0" background color by scaling it up 20%
            color = self.shade_color(color,0.2)
        else:    
            # Up
            if self.__state == 0:
                if self._bg_color is None:
                    theme = bpy.context.preferences.themes[0]
                    widget_style = getattr(theme.user_interface, "wcol_tool")
                    color = widget_style.inner
                else:
                    color = self._bg_color 
            # Down
            elif self.__state == 1:
                if self._selected_color is None:
                    theme = bpy.context.preferences.themes[0]
                    widget_style = getattr(theme.user_interface, "wcol_tool")
                    color = widget_style.inner_sel
                else:
                    color = self._selected_color 
            # Hover
            elif self.__state == 2:
                if self._bg_color is None:
                    theme = bpy.context.preferences.themes[0]
                    widget_style = getattr(theme.user_interface, "wcol_tool")
                    color = widget_style.inner
                else:
                    color = self._bg_color 
                # Light the "state 0" background color by scaling it down 10%
                color = self.tint_color(color,0.1)
            # Pressed
            elif self.__state == 3:
                if self._selected_color is None:
                    theme = bpy.context.preferences.themes[0]
                    widget_style = getattr(theme.user_interface, "wcol_tool")
                    color = widget_style.inner_sel
                else:
                    color = self._selected_color 

        self.shader.uniform_float("color", color)

    # Overrides base class function
    def draw_text(self):
        if self._text == "" and self._textwo == "":
            return None
            
        theme = bpy.context.preferences.themes[0]
        widget_style = getattr(theme.user_interface, "wcol_tool")

        if self.button_pressed_func(self):
            text_color = tuple(widget_style.text_sel) + (1.0,) if self._text_highlight is None else self._text_highlight
            textwo_color = tuple(widget_style.text_sel) + (1.0,) if self._textwo_highlight is None else self._textwo_highlight
        else:
            text_color = tuple(widget_style.text) + (1.0,) if self._text_color is None else self._text_color
            textwo_color = tuple(widget_style.text) + (1.0,) if self._textwo_color is None else self._textwo_color

        theme = bpy.context.preferences.ui_styles[0]
        widget_style = getattr(theme, "widget")
        
        if self._text_size is None:
            text_size = widget_style.points
            leveraged_text_size = text_size
        else:
            text_size = self._text_size
            leveraged_text_size = self.leverage_text_size(text_size,"widget")
        scaled_size = self.over_scale(leveraged_text_size)

        text_kerning = (widget_style.font_kerning_style == 'FITTED') if self._text_kerning is None else self._text_kerning
        if text_kerning:
            blf.enable(0, blf.KERNING_DEFAULT)
            
        blf.size(0, scaled_size, 72)
        length1 = blf.dimensions(0, self._text)[0]
        height1 = blf.dimensions(0, "W")[1]  # This is to keep a regular pattern since letters differ in height

        if self._textwo != "":
            if self._textwo_size is None:
                textwo_size = widget_style.points
                leveraged_text_size = textwo_size
            else:
                textwo_size = self._textwo_size
                leveraged_text_size = self.leverage_text_size(textwo_size,"widget")
            scaled_size = self.over_scale(leveraged_text_size)
            blf.size(0, scaled_size, 72)
            length2 = blf.dimensions(0, self._textwo)[0]
            height2 = blf.dimensions(0, "W")[1]  # This is to keep a regular pattern since letters differ in height
        else:
            length2 = 0
            height2 = 0

        if text_kerning:
            blf.disable(0, blf.KERNING_DEFAULT)
            
        if self._text == "" or self._textwo == "":
            middle_gap = 0
        else:
            middle_gap = 4

        over_scale = self.over_scale(10000)/10000 # This to get the raw factors without being rounded or integered

        top_margin = int((self.height - round( (height1 + height2) / over_scale ) - middle_gap) / 2.0)

        textpos_y = self.y_screen + top_margin + round((height1+0.499) / over_scale ) - 1

        shadow_size  = widget_style.shadow if self._text_shadow_size is None else self._text_shadow_size 
        shadow_offset_x = widget_style.shadow_offset_x if self._text_shadow_offset_x is None else self._text_shadow_offset_x
        shadow_offset_y = widget_style.shadow_offset_y if self._text_shadow_offset_y is None else self._text_shadow_offset_y
        shadow_color = widget_style.shadow_value if self._text_shadow_color is None else self._text_shadow_color
        shadow_alpha = widget_style.shadow_alpha if self._text_shadow_alpha is None else self._text_shadow_alpha

        if self._text != "":
            textpos_x = self.x_screen + int((self.width - round(length1 / over_scale)) / 2.0) - 1

            label = BL_UI_Label(textpos_x, textpos_y, length1, height1)
            label.style = 'BUTTON'
            label.text = self._text
            
            if self._text_size is None:
                # Do not populate the text_size property to avoid it being leveraged and scaled twice
                pass                          
            else:    
                # Send the original programmer's overriding value and let it be leveraged and scaled by BL_UI_Label class
                label.text_size = text_size    

            label.text_kerning = text_kerning
            label.shadow_size  = shadow_size 
            label.shadow_offset_x = shadow_offset_x
            label.shadow_offset_y = shadow_offset_y
            label.shadow_color = shadow_color
            label.shadow_alpha = shadow_alpha

            if self.enabled:
                label.text_color = text_color
            else:
                # When button is disabled dark the text color by scaling it up 40%
                label.text_color = self.shade_color(text_color,0.4)

            label.context_it(self.context)
            label.draw()

            textpos_y = textpos_y + middle_gap + round((height2+0.499) / over_scale )

        if self._textwo != "":
            textpos_x = self.x_screen + int((self.width - round(length2 / over_scale)) / 2.0) - 1

            label = BL_UI_Label(textpos_x, textpos_y, length2, height2)
            label.style = 'BUTTON'
            label.text = self._textwo
            
            if self._textwo_size is None:
                # Do not populate the text_size property to avoid it being leveraged and scaled twice
                pass                          
            else:    
                # Send the original programmer's overriding value and let it be leveraged and scaled by BL_UI_Label class
                label.text_size = textwo_size    

            label.text_kerning = text_kerning
            label.text_kerning = text_kerning

            label.shadow_size  = shadow_size 
            label.shadow_offset_x = shadow_offset_x
            label.shadow_offset_y = shadow_offset_y
            label.shadow_color = shadow_color
            label.shadow_alpha = shadow_alpha

            if self.enabled:
                label.text_color = textwo_color
            else:
                # When button is disabled dark the textwo color by scaling it up 40%
                label.text_color = self.shade_color(textwo_color,0.4)

            label.context_it(self.context)
            label.draw()

    # Overrides base class function
    def mouse_down(self, event, x, y):
        if self.is_in_rect(x,y):
            # When button is disabled, just ignore the click
            if not self.enabled: 
                # Consume þhe mouse event to avoid the camera/target be unselected
                return True
            # Down state
            self.__state = 1
            return self.mouse_down_func(self, event, x, y) 
        else:    
            return False
    
    # Overrides base class function
    def mouse_move(self, event, x, y):
        if self.is_in_rect(x,y):
            # When button is disabled, just ignore the hover
            if not self.enabled: 
                return True
            # When button is pressed, just ignore the hover
            if self.__state == 3: 
                return True
            if self.__state != 1:
                # Hover state
                self.__state = 2
                return False 
        else:
            if self.__state == 2:
                # Up state
                self.__state = 0
        return False 
 
    # Overrides base class function
    def mouse_up(self, event, x, y):
        result = False
        if self.is_in_rect(x,y): 
            # When button is disabled, just ignore the click
            if not self.enabled: 
                return True
            if self.__state == 1:
                result = self.mouse_up_func(self, event, x, y) 
        if self.button_pressed_func(self):
            # Pressed state
            self.__state = 3
        else:
            # Up state
            self.__state = 0
        return result 

    # Overrides base class function
    def mouse_up_over(self):
        if self.button_pressed_func(self):
            # Pressed state
            self.__state = 3
        else:
            # Up state
            self.__state = 0
