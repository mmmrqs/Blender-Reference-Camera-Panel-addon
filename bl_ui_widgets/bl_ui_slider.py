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
#Added: Logic to scale the slider according to both Blender's ui scale configuration and this addon 'preferences' setup
#Added: 'outline_color' property to allow different color on the slider outline (value is standard color tuple). 
#Added: 'roundness' property to allow the slider to be painted with rounded corners,
#        same as that property available in Blender's user themes and it works together with 'rounded_corners' below.
#Added: 'corner_radius' property to allow a limit for the roundness curvature, more useful when 'roundness' property 
#        is not overriden by programmer and the one from Blender's user themes is used instead.
#Added: 'rounded_corners' property and coding to allow the slider to be painted with rounded corners (value is a 4 elements tuple).
#        Each elements is a boolean value (0 or 1) which indicates whether the corresponding corner is to be rounded or straight
#        in the following clockwise sequence: bottom left, top left, top right, bottom right. 
#Added: 'shadow' property and coding to allow the slider to be painted with a shadow (value is boolean).
#Added: Logic to allow a slider to be disabled (darkned out) and turned off to user interaction.
#Added: 'set_mouse_up' function to allow assignment of an external function to be called by internal 'mouse_up_func'.
#Added: Shadow and Kerning related properties that allow the text to be painted using these characteristics.
#Added: Size, Shadow and Kerning attributes default to values retrieved from user theme (may be overriden by programmer).
#Chang: Made it a subclass of 'BL_UI_Patch' instead of 'BL_UI_Widget' so that it can inherit the layout features from there.
#Chang: Instead of hardcoded logic it is now leveraging 'BL_UI_Label' to paint the slider text.
#Fixed: New call to verify_screen_position() so that object behaves alright when viewport is resized.
#Fixed: The calculation of vertical text centering because it was varying depending on which letters presented in the text.

#--- ### Imports
import bpy
import gpu
import bgl

from gpu_extras.batch import batch_for_shader

from . bl_ui_patch import BL_UI_Patch
from . bl_ui_label import BL_UI_Label
from . bl_ui_button import BL_UI_Button
from . bl_ui_textbox import BL_UI_Textbox

class BL_UI_Slider(BL_UI_Patch): 
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        
        # Note: '_style' value will always be ignored if the bg_color value is overriden after object initialization.

        self._text = ""
        self._text_color = None                 # Slider text color
        self._text_highlight = None             # Slider text editing color 
                                          
        self._style = 'NUMBER_SLIDE'            # Slider style options are: {'NUMBER_SLIDE','NUMBER_CLICK'}
        self._bg_color = None                   # Slider background color
        self._selected_color = None             # Slider selection percentage color
        self._outline_color = None              # Slider outline color
        self._carret_color = None               # Textbox carret color (when in edit mode)
        self._roundness = None                  # Slider corners roundness factor [0..1]
        self._radius = 8.5                      # Slider corners circular radius 
        self._rounded_corners = (1,1,1,1)       # 1=Round/0=Straight, coords:(bottomLeft,topLeft,topRight,bottomRight)
        self._has_shadow = True                 # Indicates whether a shadow must be drawn around the slider 
                                          
        self._text_size = None                  # Slider text size
        self._text_kerning = None               # Slider text kerning (True/False)
        self._text_shadow_size = None           # Slider text shadow size
        self._text_shadow_offset_x = None       # Slider text shadow offset x (positive goes right)
        self._text_shadow_offset_y = None       # Slider text shadow offset y (negative goes down)
        self._text_shadow_color = None          # Slider text shadow color [0..1] = gray tone, from dark to clear
        self._text_shadow_alpha = None          # Slider text shadow alpha value [0..1]

        self._value = 0                         # Current value on the slider
        self._min_value = None                  # Minimum value to be reached by the slider
        self._max_value = None                  # Maximum value to be reached by the slider
        self._precision = 3                     # Number of decimal places for the displayed value
        self._step = 1                          # Step size to increase/decrease the displayed value (in precision units)
        self._unit = "mm"                       # Unit indicator for the displayed value

        self.__is_drag = False
        self.__is_edit = False
        self.__mouse_moved = False
        self.__drag_start_x = 0
        
    # Overrides base class function
    def init(self, context):
        self.context = context

        #-- create sub element pieces that make the slider widget 

        if self._style == 'NUMBER_CLICK':
            side_width = int(round(16*self.height / 20))   # Proportionally dimensioned
            self.decrease = BL_UI_Button(self.x, self.y, side_width, self.height)
            self.increase = BL_UI_Button((self.x + self.width - side_width), self.y, side_width, self.height)
            self.slider = BL_UI_Button((self.x + side_width - 2), self.y, (self.width + 4 - 2*side_width), self.height)
        else:
            self.slider = BL_UI_Button(self.x, self.y, self.width, self.height)
 
        self.textbox = BL_UI_Textbox(self.x, self.y, self.width, self.height)

        #-- Left side small button piece --

        if self._style == 'NUMBER_CLICK':
            self.decrease.context = context

            self.decrease.text = ""
            self.decrease.text_color = self._text_color
            self.decrease.style = self._style             
            self.decrease.bg_color = self._bg_color              
            self.decrease.outline_color = self._outline_color         
            self.decrease.roundness = self._roundness
            self.decrease.radius = self._radius
            self.decrease.has_shadow = self._has_shadow        
            if self._rounded_corners is None:
                self.decrease.rounded_corners = (1,1,0,0)
            else:
                self.decrease.rounded_corners = (self._rounded_corners[0],self._rounded_corners[1],0,0)
                 
            self.decrease.text_size = self._text_size             
            self.decrease.text_kerning = self._text_kerning          
            self.decrease.text_shadow_size = self._text_shadow_size      
            self.decrease.text_shadow_offset_x = self._text_shadow_offset_x  
            self.decrease.text_shadow_offset_y = self._text_shadow_offset_y  
            self.decrease.text_shadow_color = self._text_shadow_color     
            self.decrease.text_shadow_alpha = self._text_shadow_alpha     
                 
            self.decrease.set_mouse_up(self.decrease_mouse_up_func)

        #-- Middle section button piece --
        
        self.slider.context = context
        self.slider._is_mslider = (self._style == 'NUMBER_CLICK') # Indicates this is the middle section of the slider 

        self.slider.text = self._text
        self.slider.textwo = self.update_self_value(self._value)
        self.slider.text_color = self._text_color
        self.slider.textwo_color = self._text_color

        self.slider.style = self._style
        self.slider.bg_color = self._bg_color              
        self.slider.selected_color = self._selected_color        
        self.slider.outline_color = self._outline_color         
        self.slider.roundness = 0 if self._style == 'NUMBER_CLICK' else self._roundness               
        self.slider.radius = 0 if self._style == 'NUMBER_CLICK' else self._radius               
        self.slider.rounded_corners = (0,0,0,0) if self._style == 'NUMBER_CLICK' else self._rounded_corners
        self.slider.has_shadow = self._has_shadow           

        self.slider.text_size = self._text_size             
        self.slider.textwo_size = self._text_size             
        self.slider.text_margin = 2 if self._style == 'NUMBER_CLICK' else 8
        self.slider.text_kerning = self._text_kerning          
        self.slider.text_shadow_size = self._text_shadow_size      
        self.slider.text_shadow_offset_x = self._text_shadow_offset_x  
        self.slider.text_shadow_offset_y = self._text_shadow_offset_y  
        self.slider.text_shadow_color = self._text_shadow_color     
        self.slider.text_shadow_alpha = self._text_shadow_alpha     

        self.slider.set_mouse_down(self.slider_mouse_down_func)
        self.slider.set_mouse_up(self.slider_mouse_up_func)

        #-- Right side small button piece --
        
        if self._style == 'NUMBER_CLICK':
            self.increase.context = context

            self.increase.text = ""
            self.increase.text_color = self._text_color
            self.increase.style = self._style             
            self.increase.bg_color = self._bg_color              
            self.increase.outline_color = self._outline_color         
            self.increase.roundness = self._roundness
            self.increase.radius = self._radius
            self.increase.has_shadow = self._has_shadow           
            if self._rounded_corners is None:
                self.increase.rounded_corners = (0,0,1,1)
            else:
                self.increase.rounded_corners = (0,0,self._rounded_corners[2],self._rounded_corners[3])
                 
            self.increase.text_size = self._text_size             
            self.increase.text_kerning = self._text_kerning          
            self.increase.text_shadow_size = self._text_shadow_size      
            self.increase.text_shadow_offset_x = self._text_shadow_offset_x  
            self.increase.text_shadow_offset_y = self._text_shadow_offset_y  
            self.increase.text_shadow_color = self._text_shadow_color     
            self.increase.text_shadow_alpha = self._text_shadow_alpha     
                 
            self.increase.set_mouse_up(self.increase_mouse_up_func)

        #-- Textbox editing overlay object --
        
        self.textbox.context = context

        self.textbox.text = str(self._value)
        self.textbox.text_color = self._text_color
        self.textbox.text_highlight = self._text_highlight
        self.textbox.style = self._style             
        self.textbox.bg_color = self._bg_color              
        self.textbox.selected_color = self._selected_color        
        self.textbox.outline_color = self._outline_color
        self.textbox.carret_color = self._carret_color 
        self.textbox.roundness = 0 if self._style == 'NUMBER_CLICK' else self._roundness               
        self.textbox.radius = 0 if self._style == 'NUMBER_CLICK' else self._radius               
        self.textbox.rounded_corners = (0,0,0,0) if self._style == 'NUMBER_CLICK' else self._rounded_corners
        self.textbox.has_shadow = self._has_shadow                        

        self.textbox.max_input_chars = 20
        self.textbox.is_numeric = True

        self.textbox.text_size = self._text_size             
        self.textbox.text_margin = 8
        self.textbox.text_kerning = self._text_kerning          
        self.textbox.text_shadow_size = self._text_shadow_size      
        self.textbox.text_shadow_offset_x = self._text_shadow_offset_x  
        self.textbox.text_shadow_offset_y = self._text_shadow_offset_y  
        self.textbox.text_shadow_color = self._text_shadow_color     
        self.textbox.text_shadow_alpha = self._text_shadow_alpha     

        self.textbox.set_mouse_down(self.textbox_mouse_down_func)
        self.textbox.set_mouse_up(self.textbox_mouse_up_func)

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
    def carret_color(self):
        return self._carret_color

    @carret_color.setter
    def carret_color(self, value):
        self._carret_color = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        min = value if self._min_value is None else self._min_value
        max = value if self._max_value is None else self._max_value
        if value < min:
            self._value = min
        elif value > max:
            self._value = max
        else:    
            self._value = value

    @property
    def min(self):
        return self._min_value

    @min.setter
    def min(self, value):
        self._min_value = value

    @property
    def max(self):
        return self._max_value

    @max.setter
    def max(self, value):
        self._max_value = value

    @property
    def precision(self):
        return self._precision

    @precision.setter
    def precision(self, value):
        self._precision = value

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, value):
        self._step = value

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, value):
        self._unit = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        
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

    def set_slider_updated(self, slider_updated_func):
        self.slider_updated_func = slider_updated_func   

    def slider_updated_func(self, widget, value):
        # This must return True when function is not overriden, 
        # so that the value updated by the slider is actually committed. 
        return True
                 
    def update_self_value(self, value):
        update_value = value
        if not self._min_value is None:
            update_value = self._min_value if update_value < self._min_value else update_value
        if not self._max_value is None:
            update_value = self._max_value if update_value > self._max_value else update_value
        if self.slider_updated_func(self, update_value):
            self._value = round(update_value, self._precision)
        str_value = str(round(self._value, self._precision))
        str_value = str_value[:len(str_value)-2] if str_value[-2:] == ".0" else str_value
        self.slider.textwo = str_value + " " + self._unit
        self.textbox.text = str_value
        return self.slider.textwo
 
    # Overrides base class function
    def update(self, x, y):      
        # Here we need to update the x position for the sub elements separately 
        # because those are sub parts that together compound a slider object. 
        widget_x = (x - self.x_screen)

        super().update(x, y)

        if self._style == 'NUMBER_CLICK':
            self.decrease.update(self.decrease.x_screen + widget_x, y)   
            self.increase.update(self.increase.x_screen + widget_x, y)   

        self.slider.update(self.slider.x_screen + widget_x, y)   
        self.textbox.update(self.textbox.x_screen + widget_x, y)   
        
    # Overrides base class function
    def draw(self):      
        if not self._is_visible:
            return
            
        # Enter edit mode and skip drawing the regular slider object pieces
        if self.__is_edit:
            self.textbox.draw()
            return

        # Draw slider's left and right click corners
        if self._style == 'NUMBER_CLICK':
            self.decrease.draw()
            self.increase.draw()
        
        self.slider.draw()

        # Draw slider's percentage overlay bar
        if self._style == 'NUMBER_SLIDE' and (not self._min_value is None) and (not self._max_value is None):
            if self._value < self._min_value or self._value > self._max_value:
                percentage = 0  # wrong values, get out and do not display bar
            elif self._min_value == self._max_value:    
                percentage = 1
            else:    
                dividend = self._value - self._min_value
                divisor = self._max_value - self._min_value
                percentage = abs(dividend) / abs(divisor)
                percentage = 0 if percentage < 0 else percentage
                percentage = 1 if percentage > 1 else percentage
                
            capped_width = int(round(self.slider.width * percentage))
            capped_pos_x = self.over_scale(self.slider.x_screen + capped_width - 1)

            if capped_width > 0: 
                if not (self._roundness is None):
                    roundness = self._roundness
                else:
                    # From Preferences/Themes/User Interface/<style>
                    theme = bpy.context.preferences.themes[0]
                    widget_style = getattr(theme.user_interface, self.my_style())
                    roundness = widget_style.roundness        

                scaled_radius = round(roundness * self.over_scale(self._radius))
                
                self.shader_slider = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

                if True: #scaled_radius > 10:  #was: scaled_radius == 0 or scaled_radius > 10 or self._rounded_corners == (0,0,0,0):
                    vertices = self.calc_corners_for_trifan(int(self.slider.x_screen), self.slider.y_screen, self.slider.width, self.slider.height, scaled_radius, 'FULL')
                    if capped_width < self.slider.width:
                        # Cap the vertices x coord at percentage of width size (that is, at capped_pos_x)
                        to_be_capped = vertices
                        vertices = []
                        for coord in to_be_capped:
                            if coord[0] <= capped_pos_x:
                                vertices.append(coord)
                            else:    
                                vertices.append((capped_pos_x, coord[1]))
                    self.batch_slider = batch_for_shader(self.shader_slider, 'TRI_FAN', {"pos" : vertices})
                else:
                    vertices = self.calc_corners_for_lines(int(self.slider.x_screen), self.slider.y_screen, self.slider.width, self.slider.height, scaled_radius, 'FULL')
                    if capped_width < self.slider.width:
                        # Cap the vertices x coord at percentage of width size (that is, at capped_pos_x)
                        to_be_capped = vertices
                        vertices = []
                        i = 0      
                        while i < len(to_be_capped):
                            if to_be_capped[i][0] <= capped_pos_x:
                                vertices.append(to_be_capped[i])
                                if to_be_capped[i+1][0] <= capped_pos_x:
                                    vertices.append(to_be_capped[i+1])
                                else:
                                    vertices.append((capped_pos_x, to_be_capped[i+1][1]))
                            i = i + 2
                    self.batch_slider = batch_for_shader(self.shader_slider, 'LINES', {"pos" : vertices})

                self.shader_slider.bind()
                
                self.set_slide_color()
                
                bgl.glEnable(bgl.GL_BLEND)

                self.batch_slider.draw(self.shader_slider) 

                bgl.glEnable(bgl.GL_LINE_SMOOTH)

                self.slider.draw_outline()
                
                bgl.glDisable(bgl.GL_LINE_SMOOTH)

                self.slider.draw_text()

                bgl.glDisable(bgl.GL_BLEND)      

    def set_slide_color(self):
        if not self._is_enabled:
            if self._bg_color is None:
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.user_interface, self.my_style())
                color = widget_style.inner
            else:
                color = self._bg_color  
            # When slider is disabled dark the "state 0" background color by scaling it up 40%
            color = self.shade_color(color,0.4)
        else:    
            if self._selected_color is None:
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.user_interface, self.my_style())
                color = widget_style.item
            else:
                color = self._selected_color 

        self.shader_slider.uniform_float("color", color)

    def equalize_states(self, widget):
        if self._style == 'NUMBER_CLICK': 
            self.decrease.state = widget.state
            self.increase.state = widget.state
        self.slider.state = widget.state
        
    def stop_editing(self):
        self.update_self_value(float(self.textbox.text))
#        self.set_editing_widget(None)  # Indicates that textbox editing mode has finished
        self.__is_edit = False

    # Overrides base class function
    def get_input_keys(self):
        return self.textbox.get_input_keys()

    # Overrides base class function
    def keyboard_press(self, event):
        if self.__is_edit:
            self.textbox.keyboard_press(event)
            if event.type in ['RET','ESC']:
                # Note: the keyboard_press() function above would have executed also 
                # the textbox's stop_editing() function for the 'RET' and 'ESC' events.
                self.stop_editing()
        return True
        
    # Overrides base class function
    def mouse_down(self, event, x, y):    
        if self.is_in_rect(x,y):
            # When slider is disabled, just ignore the click
            if not self._is_enabled: 
                # Consume the mouse event to avoid the camera/target be unselected
                return True
            self.__is_drag = True
            self.__drag_start_x = x
            self.__mouse_moved = False
            if self._style == 'NUMBER_CLICK':
                if self.decrease.mouse_down(event, x, y):
                    self.equalize_states(self.decrease)
                    return True
                if self.increase.mouse_down(event, x, y):
                    self.equalize_states(self.increase)
                    return True
            if self.slider.mouse_down(event, x, y):
                self.equalize_states(self.slider)
                return True
        else:
            self.__is_edit = False
        return False
    
    # Overrides base class function
    def mouse_up(self, event, x, y):    
        # When slider is disabled, just ignore the click
        if not self._is_enabled: 
            # Consume the mouse event to avoid the camera/target be unselected
            return True
        self.__is_drag = False
        self.set_editing_widget(None)       # Indicates that sliding mode has finished
        if self._style == 'NUMBER_CLICK': 
            if self.decrease.mouse_up(event, x, y):
                self.equalize_states(self.decrease)
                return True
            if self.increase.mouse_up(event, x, y):
                self.equalize_states(self.increase)
                return True
        if self.slider.mouse_up(event, x, y):
            self.equalize_states(self.slider)
            return True
        return False

    # Overrides base class function
    def mouse_move(self, event, x, y):    
        # When slider is disabled, just ignore the hover
        if not self._is_enabled: 
            return False

        if self.__is_edit:
            return False

        if self.__is_drag:
            # Update the value according to direction of x_drag
            drag_offset_x = x - self.__drag_start_x
            if drag_offset_x != 0:
                if self._style == 'NUMBER_CLICK':
                    # Proportionally change to the step coeficient
                    new_value = self._value + (drag_offset_x * self._step)
                else:    
                    # Proportionally change to the size-range coeficient
                    new_value = self._value + ((drag_offset_x / self.width) * (self._max_value - self._min_value)) 
                #--    
                self.update_self_value(new_value)
                self.__drag_start_x = x
                self.__mouse_moved = True
            return True

        if self._style == 'NUMBER_CLICK':
            if self.is_in_rect(x,y):
                self.decrease.text = "<"
                self.increase.text = ">"
            else:
                self.decrease.text = ""
                self.increase.text = ""

            self.button_mouse_move(self.decrease, event, x, y)
            self.button_mouse_move(self.increase, event, x, y)

        self.button_mouse_move(self.slider, event, x, y)
        return False

    # Overrides base class function
    def mouse_up_over(self):
        pass

    # Emulates the mouse_move function of 'BL_UI_Button' class
    def button_mouse_move(self, widget, event, x, y):
        if widget.is_in_rect(x,y):
            if widget.state != 1:
                # Hover state
                widget.state = 2
        else:
            if widget.state == 2:
                # Up state
                widget.state = 0
 
    def decrease_mouse_up_func(self, widget, event, x, y):    
        if not self.__mouse_moved:
            self.update_self_value(self._value - self._step)
        return True

    def increase_mouse_up_func(self, widget, event, x, y):  
        if not self.__mouse_moved:
            self.update_self_value(self._value + self._step)
        return True

    def slider_mouse_down_func(self, widget, event, x, y):    
        if self.__is_edit:
            if not self.textbox.is_in_rect(x,y):
                self.textbox.stop_editing()
                self.stop_editing()
        else:
            # Indicates that sliding mode has started
            self.set_editing_widget(self)
        return True
    
    def slider_mouse_up_func(self, widget, event, x, y):
        if self.__mouse_moved:
            # Indicates that sliding mode has finished
            self.set_editing_widget(None)
        else:
            if self.__is_edit:
                if not self.textbox.mouse_up(event, x, y):
                    # Note: this mouse_up() function will execute also the textbox's stop_editing() function
                    self.stop_editing()
            else:
                if self.textbox.mouse_down(event, x, y):
                    # Indicates that textbox editing mode has started
                    self.set_editing_widget(self)
                    self.__is_edit = True
        return True

    def textbox_mouse_down_func(self, widget, event, x, y):    
        return True

    def textbox_mouse_up_func(self, widget, event, x, y):    
        return True
