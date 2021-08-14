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
#Chang: Renamed function 'text_input' to 'keyboard_press'.


#--- ### Imports
import bpy
import gpu
import bgl
import blf

from gpu_extras.batch import batch_for_shader

from . bl_ui_button import BL_UI_Button
from . bl_ui_label import BL_UI_Label

class BL_UI_Textbox(BL_UI_Button):

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

        # Note: '_style' value will always be ignored if the bg_color value is overriden after object initialization.

        self._text = "Textbox"
        self._text_color = None                 # Textbox normal color 
        self._text_highlight = None             # Textbox high color (first row) 

        self._style = 'TEXTBOX'                 # Textbox background color style
        self._bg_color = None                   # Textbox background color 
        self._selected_color = None             # Textbox background color (when in edit mode)
        self._outline_color = None              # Textbox outline color 
        self._cursor_color = None               # Textbox cursor color (when in edit mode)
        self._roundness = None                  # Textbox corners roundness factor [0..1]
        self._radius = 8.5                      # Textbox corners circular radius
        self._rounded_corners = (1,1,1,1)       # 1=Round/0=Straight, coords:(bottomLeft,topLeft,topRight,bottomRight)
        self._has_shadow = True                 # Indicates whether a shadow must be drawn around the textbox 

        self._max_input_chars = 100             # Maximum number of characters to be input by the textbox
        self._is_numeric = False                # Indicates whether the input text must restrict to numeric values

        self._text_margin = 8                   # Textbox text left margin 
        self._text_size = None                  # Textbox text line 1 size
        self._text_kerning = None               # Textbox text kerning (True/False)
        self._text_shadow_size = None           # Textbox text shadow size
        self._text_shadow_offset_x = None       # Textbox text shadow offset x (positive goes right)
        self._text_shadow_offset_y = None       # Textbox text shadow offset y (negative goes down)
        self._text_shadow_color = None          # Textbox text shadow color [0..1] = gray tone, from dark to clear
        self._text_shadow_alpha = None          # Textbox text shadow alpha value [0..1]

        self.__ui_scale = 0
        # self.__cursor_pos = [0,0]
        self.__cursor_pos = 0
        self.__cached_text = ""
        self.__is_editing = False
        self.__input_keys = ['ESC','RET','NUMPAD_ENTER','BACK_SPACE','HOME','END','LEFT_ARROW','RIGHT_ARROW','DEL']

    @property
    def cursor_color(self):
        return self._cursor_color

    @cursor_color.setter
    def cursor_color(self, value):
        self._cursor_color = value

    @property
    def max_input_chars(self):
        return self._max_input_chars

    @max_input_chars.setter
    def max_input_chars(self, value):
        self._max_input_chars = value

    @property
    def is_numeric(self):
        return self._is_numeric

    @is_numeric.setter
    def is_numeric(self, value):
        self._is_numeric = value   

    def set_text_updated(self, text_updated_func):
        self.text_updated_func = text_updated_func

    def text_updated_func(self, widget, context, event, former_text, updated_text):
        # This must return True when function is not overriden, so that text editing is accepted
        return True            

    # Overrides base class function
    def button_pressed_func(self, widget):
        return self.__is_editing
                 
    def start_editing(self):
        if not self.__is_editing:
            # Edit state
            self.state = 3
            self.__is_editing = True
            self.__cached_text = self._text
            self.__cursor_pos = len(self._text)
            # self.__cursor_pos = [0, len(self._text)]
            self.__ui_scale = self.over_scale(1)
            self.update_cursor()
            self.set_exclusive_mode(self)

    def stop_editing(self):
        if self.__is_editing:
            if self.clean_up_text():
                # Up state
                self.state = 0
                self.__is_editing = False
                self.set_exclusive_mode(None)
            else:    
                # Up state                      # Left this redundancy here just to show that we could have taken
                self.state = 0                  # a different action in the case of failing to clean up the text.
                self.__is_editing = False       # Even when failing we are exiting the edit mode, but in that case 
                self.set_exclusive_mode(None)   # the clean_up_text() function will have restored the original text.

    def clean_up_text(self):
        if self._text != self.__cached_text:
            # Logic to clean up numeric strings
            if self._is_numeric:
                clean_text = self._text
                negative = (clean_text.find('-') == 0)
                if negative:
                    clean_text = clean_text[1:]                                   # Temporarily removes the negative symbol
                if len(clean_text) > 0: 
                    if clean_text[ 0] in ['.', ',']:                               
                        clean_text = "0" + clean_text[0:self._max_input_chars-1]  # Add a missing leading zero
                while len(clean_text) > 1:
                    if clean_text[0] == "0" and not clean_text[1] in ['.', ',']:
                        clean_text = clean_text[1:]                               # Discard all extra leading zeroes
                    else:
                        break
                decimal = clean_text.find('.') + clean_text.find(',') + 1
                while len(clean_text) > 1 and decimal != -1:
                    if clean_text[-1] in ['0', '.', ',']:
                        clean_text = clean_text[0:len(clean_text)-1]              # Discard all extra trailing zeroes
                    else:                                                         # or trailing decimal points/commas 
                        break
                if len(clean_text) == 0:
                    self._text = "0"                                              # Fill out an empty numeric value
                else:
                    clean_text = ("-" + clean_text) if negative else clean_text   # Adds back the negative symbol
                    try:
                        float(clean_text)
                        self._text = clean_text
                    except:
                        self._text = self.__cached_text
                        return False
            else:
                # Here would go any logic to clean up non numeric strings
                pass
                
        return True

    def get_cursor_pos_px(self):
        theme = bpy.context.preferences.ui_styles[0]
        widget_style = getattr(theme, "widget")
        
        if self._text_size is None:
            text_size = widget_style.points
            leveraged_text_size = text_size
        else:
            text_size = self._text_size
            leveraged_text_size = self.leverage_text_size(text_size,"widget")
        scaled_size = int(round(self.over_scale(leveraged_text_size)))

        text_kerning = (widget_style.font_kerning_style == 'FITTED') if self._text_kerning is None else self._text_kerning
        if text_kerning:
            blf.enable(0, blf.KERNING_DEFAULT)
        blf.size(0, scaled_size, 72)

        # if self.__cursor_pos[0] == 0:
            # start = 0
        # else:    
            # text_to_cursor = self._text[:self.__cursor_pos[0]]
            # start = blf.dimensions(0, text_to_cursor)[0]  
        text_to_cursor = self._text[:self.__cursor_pos]    

        # text_to_cursor = self._text[self.__cursor_pos[0] : self.__cursor_pos[1]]
        length = blf.dimensions(0, text_to_cursor)[0]  

        if text_kerning:
            blf.disable(0, blf.KERNING_DEFAULT)

        # return [start, length]
        return length

    def update_cursor(self):
        x_screen = self.over_scale(self.x_screen + self._text_margin) + self.get_cursor_pos_px()
        vertices = ((x_screen, self.over_scale(self.y_screen - 1)),
                    (x_screen, self.over_scale(self.y_screen - self.height + 2))
                    )
        self.batch_cursor = batch_for_shader(self.shader_cursor, 'LINES', {"pos": vertices})

    # Overrides base class function
    def update(self, x, y):        
        super().update(x, y)

        self.shader_cursor = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            
        self.update_cursor()
        
    # Overrides base class function
    def draw(self):
        if not self._is_visible:
            return
            
        super().draw()

        # Get out of edit mode if user has changed the ui_scaling in the meantime
        if self.__ui_scale != self.over_scale(1):
            self.__ui_scale = self.over_scale(1)
            self.__is_editing = False

        # Draw cursor
        if self.__is_editing:
            if self._cursor_color is None:
                # From Preferences/Themes/User Interface/"Styles"
                theme = bpy.context.preferences.themes[0]
                widget_style = theme.user_interface              
                color = tuple(widget_style.widget_text_cursor) + (1.0,) 
            else:
                color = self._cursor_color

            self.shader_cursor.bind()
            
            self.shader_cursor.uniform_float("color", color)
            
            bgl.glEnable(bgl.GL_LINE_SMOOTH)
            
            bgl.glLineWidth(self.over_scale(1))
            
            self.batch_cursor.draw(self.shader_cursor)

            bgl.glDisable(bgl.GL_LINE_SMOOTH)

    # Overrides base class function
    def get_input_keys(self):
        return self.__input_keys

    # Overrides base class function
    def keyboard_press(self, event):
        if not (self._is_enabled and self.__is_editing):
            return False

        index = self.__cursor_pos
        former_text = self._text
        former_pos  = self.__cursor_pos
        
        if event.ascii != '' and len(self._text) < self._max_input_chars:
            digits = ['0','1','2','3','4','5','6','7','8','9']              # <-- This to avoid any funny business 
            value = self._text[:index] + event.ascii + self._text[index:]
            if (not self._is_numeric) \
            or (event.ascii == '-' and not ('-' in self._text or index > 0)) \
            or (event.ascii == '.' and not ('.' in self._text or ',' in self._text)) \
            or (event.ascii == ',' and not (',' in self._text or '.' in self._text)) \
            or (event.ascii in digits and not (index == 0 and '-' in self._text)):
                self._text = value
                self.__cursor_pos += 1

        elif event.type == 'BACK_SPACE':
            if index > 0:
                if event.ctrl:
                    self._text = ""
                    self.__cursor_pos = 0
                else:    
                    self._text = self._text[:index-1] + self._text[index:]
                    self.__cursor_pos -= 1

        elif event.type == 'DEL':
            if index < len(self._text):
                if event.ctrl:
                    self._text = self._text[:index]
                else:    
                    self._text = self._text[:index] + self._text[index+1:]

        elif event.type == 'LEFT_ARROW':
            if index > 0:
                if event.ctrl:
                    self.__cursor_pos = 0
                else:
                    self.__cursor_pos -= 1

        elif event.type == 'RIGHT_ARROW':
            if index < len(self._text):
                if event.ctrl:
                    self.__cursor_pos = len(self._text)
                else:
                    self.__cursor_pos += 1

        elif event.type == 'HOME':
            self.__cursor_pos = 0

        elif event.type == 'END':
            self.__cursor_pos = len(self._text)

        elif event.type == 'RET' or event.type == 'NUMPAD_ENTER':
            self.stop_editing()

        elif event.type == 'ESC':
            self._text = self.__cached_text
            self.stop_editing()

        if self._text != former_text and event.type != 'ESC':
            if not self.text_updated_func(self, self.context, event, former_text, self._text):
                self._text = former_text
                self.__cursor_pos = former_pos
                
        self.update_cursor()
        return True

    # Overrides base class function
    def mouse_down(self, event, x, y):
        if self.is_in_rect(x,y):
            # When textbox is disabled, just ignore the click
            if not self._is_enabled: 
                # Consume the mouse event to avoid the camera/target be unselected
                return True
            if self.mouse_down_func(self, event, x, y):
                if self.__is_editing:
                    # Here new logic to start highlight text
                    pass
                else:
                    self.start_editing()
                return True
            else:    
                return False
        else:    
            self.stop_editing()
            return False
            
    # Overrides base class function
    def mouse_up(self, event, x, y):
        if self.is_in_rect(x,y): 
            # When textbox is disabled, just ignore the click
            if not self._is_enabled: 
                # Consume the mouse event to avoid the camera/target be unselected
                return True
            if self.mouse_up_func(self, event, x, y):
                if self.__is_editing:
                    # Here new logic to finish highlight text
                    pass
                else:
                    pass
                return True
            else:    
                return False
        else:    
            self.stop_editing()
            return False

    # Overrides base class function
    def mouse_up_over(self):
        pass
