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
    "version": (0, 6, 5, 0),
    "blender": (2, 80, 3),
    "location": "View3D",
    "support": "COMMUNITY",
    "category": "3D View",
    "warning": ""
    }
    
#--- ### Change log

#v0.6.5 (08.01.2021) - by Marcelo M. Marques 
#Added: This new class to display tooltips for each widget. If design properties are not overriden by programmer 
#       then those will be inherited from Blender's user themes.

#--- ### Imports
import bpy
import blf

from . bl_ui_patch import BL_UI_Patch
from . bl_ui_label import BL_UI_Label

class BL_UI_Tooltip(BL_UI_Patch): 
    
    def __init__(self):
        super().__init__(0,0,0,0)  # These arguments have no use in the case of a tooltip object

        self._text_color = None                                # Tooltip text color
        self._shortcut_color = (185/255, 185/255, 185/255, 1)  # Tooltip shortcut color medium gray (seems to be fixed)
        self._python_color = (122/255, 122/255, 122/255, 1)    # Tooltip python cmd color dark gray (seems to be fixed)

        # Note: '_style' value will always be ignored if the bg_color value is overriden after object initialization.

        self._style = 'TOOLTIP'                 # Tooltip background color styles are: {HEADER,PANEL,SUBPANEL,TOOLTIP,NONE}
        self._bg_color = None                   # Tooltip background color (defaults to 'TOOLTIP')
        self._outline_color = None              # Tooltip outline color (defaults to 'TOOLTIP')
        self._roundness = None                  # Tooltip corners roundness factor [0..1]
        self._radius = 8.5                      # Tooltip corners circular radius
        self._rounded_corners = (1,1,1,1)       # 1=Round/0=Straight, coords:(bottomLeft,topLeft,topRight,bottomRight)
        self._has_shadow = True                 # Indicates whether a shadow must be drawn around the tooltip 

        self._text_size = None                  # Tooltip text line 1 size
        self._text_kerning = None               # Tooltip text kerning (True/False)
        self._text_shadow_size = None           # Tooltip text shadow size
        self._text_shadow_offset_x = None       # Tooltip text shadow offset x (positive goes right)
        self._text_shadow_offset_y = None       # Tooltip text shadow offset y (negative goes down)
        self._text_shadow_color = None          # Tooltip text shadow color [0..1] = gray tone, from dark to clear
        self._text_shadow_alpha = None          # Tooltip text shadow alpha value [0..1]

        self._is_tooltip = True                 # Indicates that object generated by this class is a Tooltip type

        self.__over_scale = 0                   # Saves the last scaling value used
        self.__area_height = 0                  # Saves the last area height value
        self.__area_width = 0                   # Saves the last area width value
        
        self.__tooltip_widget = None            # Identifies the widget object to have tooltip displayed 
        self.__tooltip_textsize = None          # Text size used on drawing the tooltip last time
        self.__tooltip_textkern = None          # Text kerning used on drawing the tooltip last time
        self.__tooltip_showpyth = None          # Former setup for displaying python commands
        self.__tooltip_text_lines = []          # Tooltip text lines to be prepared by internal function
        self.__tooltip_shortcut_lines = []      # Tooltip shortcut text lines to be prepared by internal function
        self.__tooltip_python_lines = []        # Tooltip python text lines to be prepared by internal function
        
        self.__line_space = 6                   # Standard vertical spacing between tooltip text lines (units in pixels)
        self.__text_margin = 12                 # Standard margin size for tooltip text arrangement (units in pixels)

        self.__max_lines_text = 3               # Limit of 3 text lines for the main tooltip
        self.__max_lines_shortcut = 1           # Limit of 1 text line for the shortcut
        self.__max_lines_python = 2             # Limit of 2 text lines for the python command
        self.__max_tooltip_width = 450          # Limit of 450px for the tooltip box width (which is variable)

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

    @property
    def max_lines_description(self):
        return self.__max_lines_text

    @max_lines_description.setter
    def max_lines_description(self, value):
        self.__max_lines_text = value

    @property
    def max_lines_shortcut(self):
        return self.__max_lines_shortcut

    @max_lines_shortcut.setter
    def max_lines_shortcut(self, value):
        self.__max_lines_shortcut = value

    @property
    def max_lines_python(self):
        return self.__max_lines_python

    @max_lines_python.setter
    def max_lines_python(self, value):
        self.__max_lines_python = value

    @property
    def max_width(self):
        return self.__max_tooltip_width

    @max_width.setter
    def max_width(self, value):
        self.__max_tooltip_width = value

    # Overrides base class function
    def is_in_rect(self, x, y):
        return False
        
    def prepare_tooltip_data(self, widget):
        base_class = super().__thisclass__.__mro__[-2]  # This stunt only to avoid hard coding the Base class name
        if base_class.g_tooltip_widget is None:
            return False

        # These many checks below is to try saving runtime by skipping unnecessary text processing
        if not self.__tooltip_widget is widget:
            self.__tooltip_widget = widget

        elif not widget.tooltip_moved:
            area_height = self.get_area_height()
            if self.__area_height != area_height or self.__over_scale != self.over_scale(1):
                self.__area_height = area_height 
                self.__over_scale = self.over_scale(1)
            else:
                theme = bpy.context.preferences.ui_styles[0]
                widget_style = getattr(theme, "widget")
                text_size = widget_style.points if self._text_size is None else self._text_size
                text_kerning = (widget_style.font_kerning_style == 'FITTED') if self._text_kerning is None else self._text_kerning
                if self.__tooltip_textsize != text_size or self.__tooltip_textkern != text_kerning:
                    self.__tooltip_textsize = text_size 
                    self.__tooltip_textkern = text_kerning
                else:
                    prefs = bpy.context.preferences.view   
                    display_python = bpy.context.preferences.view.show_tooltips_python
                    if self.__tooltip_showpyth != display_python:
                        self.__tooltip_showpyth = display_python
                    else:    
                        return False
            
        measurements = self.get_tooltip_measurements()
        self.x = measurements['x']
        self.y = measurements['y']
        self.x_screen = self.x
        self.y_screen = self.y
        self.width = measurements['width']
        self.height = measurements['height']
        return True

    def get_tooltip_measurements(self):
        widget = self.__tooltip_widget

        self.__tooltip_text_lines = []
        self.__tooltip_shortcut_lines = []
        self.__tooltip_python_lines = []
        
        if widget.description == "" and widget.shortcut == "" and widget.python_cmd == "":
            measurements = {'x' : 0, 
                            'y' : 0, 
                            'width' : 0, 
                            'height' : 0, 
                            }
            return (measurements)
        
        if self._text_size is None:
            theme = bpy.context.preferences.ui_styles[0]
            widget_style = getattr(theme, "widget")
            text_size = widget_style.points
        else:
            text_size = self.leverage_text_size(self._text_size,"widget")
        text_kerning = (widget_style.font_kerning_style == 'FITTED') if self._text_kerning is None else self._text_kerning

        # Will send these scaled values to text_wrap function to get a more precise measurement for the widest 
        # text line because the font characters do not scale so well proportionally to the supplied factor.
        scaled_text_size = int(self.ui_scale(text_size))
        scaled_max_width = self.ui_scale(self.__max_tooltip_width)
        
        if text_kerning:
            blf.enable(0, blf.KERNING_DEFAULT)
        blf.size(0,text_size,72)
        text_normal = blf.dimensions(0, "W")[1]  # This is to keep a regular pattern since letters differ in height
        blf.size(0,scaled_text_size,72)
        text_height = blf.dimensions(0, "W")[1]  
        if text_kerning:
            blf.disable(0, blf.KERNING_DEFAULT)

        # From Preferences/Interface/"Display"
        prefs = bpy.context.preferences.view   
        display_python = bpy.context.preferences.view.show_tooltips_python

        line_spacing = self.ui_scale(self.__line_space)

        widest_line = 0
        total_height = 0
        
        if widget.description != "":
            line_count = 0
            self.__tooltip_text_lines = self.text_wrap(widget.description, scaled_text_size, text_kerning, scaled_max_width, self.__max_lines_text)
            for line in self.__tooltip_text_lines:
                if line_count == self.__max_lines_text:  
                    break
                widest_line = line[1][0] if line[1][0] > widest_line else widest_line
                total_height += round(text_height+0.499) + line_spacing
                line_count += 1
        if widget.shortcut != "":
            line_count = 0
            self.__tooltip_shortcut_lines = self.text_wrap(widget.shortcut, scaled_text_size, text_kerning, scaled_max_width, self.__max_lines_shortcut)
            for line in self.__tooltip_shortcut_lines:
                if line_count == self.__max_lines_shortcut:  
                    break
                widest_line = line[1][0] if line[1][0] > widest_line else widest_line
                total_height += round(text_height+0.499) + line_spacing
                line_count += 1
        if widget.python_cmd != "" and display_python:
            line_count = 0
            self.__tooltip_python_lines = self.text_wrap(widget.python_cmd, scaled_text_size, text_kerning, scaled_max_width, self.__max_lines_python)
            for line in self.__tooltip_python_lines:
                if line_count == self.__max_lines_python:  
                    break
                widest_line = line[1][0] if line[1][0] > widest_line else widest_line
                total_height += round(text_height+0.499) + line_spacing
                line_count += 1

        if widget.description != "" and widget.shortcut != "":
            total_height += line_spacing
        if (widget.description != "" or widget.shortcut != "") and widget.python_cmd != "" and display_python:
            total_height += line_spacing

        # Now that we have got the text precisely wrapped, we can un-scale back the numbers before returning 
        # them to the calling function. This is desired because they will be scaled up again during drawing.
        widest_line = round(widest_line+0.499) / self.ui_scale(1)    
        total_height = total_height / self.ui_scale(1)    
        
        total_width = widest_line + 3*self.__text_margin
        total_height = total_height + 2*self.__text_margin

        tooltip_x = widget.x_screen - 6
        tooltip_y = widget.y_screen - widget.height - 12
        
        area_width = self.get_area_width()

        # Back off tooltip box placement in the X axis if it does not fit the space between the panel and viewport right border
        if self.over_scale(tooltip_x) + self.ui_scale(total_width) > area_width - 50:
            tooltip_x = (area_width - self.ui_scale(total_width) - 50) / self.over_scale(1)

        # Invert tooltip box placement in the Y axis if it does not fit the space between the panel and viewport bottom border
        if self.over_scale(tooltip_y) - self.ui_scale(total_height) < 12:
            tooltip_y = (self.over_scale(widget.y_screen) + self.ui_scale(total_height) + 12) / self.over_scale(1)

        measurements = {'x' : tooltip_x,
                        'y' : tooltip_y,
                        'width' : total_width, 
                        'height' : total_height, 
                        }
        return (measurements)

    def text_wrap(self, text, text_size, text_kerning, max_width_px, max_lines_count):
        line_break = "\n"
        text = text.rstrip()

        blf.size(0,text_size,72)
        if text_kerning:
            blf.enable(0, blf.KERNING_DEFAULT)
        
        # Note: the '3*self.__text_margin' below came from 'get_tooltip_measurements' function
        # where it is added as margins to the total_width of the tooltip box, so it has to be discounted here.
        split_point = max_width_px - 3*self.__text_margin

        line_array = []

        cr = len(line_break)
        lstrip_it = False
        text_lenght = len(text)
        text_line = ""
        char_pos = 0
        
        while char_pos < text_lenght and len(line_array) < max_lines_count:
            next_chars = text[char_pos:(char_pos+cr)]
            if next_chars == line_break:
                text_line = text_line.lstrip() if lstrip_it else text_line
                dimensions = blf.dimensions(0,text_line)
                line_array.append((text_line, dimensions))
                char_pos += len(line_break)
                lstrip_it = False
                text_line = ""
            else:
                text_line += next_chars[0]
                dimensions = blf.dimensions(0,text_line)
                if dimensions[0] > split_point:
                    last_space = text_line.rfind(" ")
                    if last_space == -1:
                        # Have to break the one-word-sentence wherever it is
                        sub_line = text_line[0:(len(text_line)-1)]
                        text_line = text_line[-1]
                    else:
                        # Cut the sentence at its closest space character
                        sub_line = text_line[0:last_space]
                        text_line = text_line[(last_space+1):]
                    sub_line = sub_line.lstrip() if lstrip_it else sub_line
                    dimensions = blf.dimensions(0,sub_line)
                    line_array.append((sub_line, dimensions))
                    lstrip_it = True
                char_pos += 1
                if char_pos == text_lenght:
                    text_line = text_line.lstrip() if lstrip_it else text_line
                    dimensions = blf.dimensions(0,text_line)
                    line_array.append((text_line, dimensions))
                    break
        if text_kerning:
            blf.disable(0, blf.KERNING_DEFAULT)
        return line_array    

    # Overrides base class function
    def draw_text(self):
        if not self._is_visible:
            return
            
        if len(self.__tooltip_text_lines) == 0:
            if len(self.__tooltip_shortcut_lines) == 0 and len(self.__tooltip_python_lines) == 0:
                return 
        else:    
            if self._text_color is None:     
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.user_interface, "wcol_tooltip")
                text_color = tuple(widget_style.text) + (1.0,)
            else:
                text_color = self._text_color

        theme = bpy.context.preferences.ui_styles[0]
        widget_style = getattr(theme, "widget")

        if self._text_size is None:
            text_size = widget_style.points
            leveraged_text_size = text_size
        else:
            text_size = self._text_size
            leveraged_text_size = self.leverage_text_size(text_size,"widget")
        text_kerning = (widget_style.font_kerning_style == 'FITTED') if self._text_kerning is None else self._text_kerning

        # Will send this scaled value to text_wrap function to get a more precise measurement for the widest 
        # text line because the font characters do not scale so well proportionally to the supplied factor.
        scaled_text_size = int(self.ui_scale(leveraged_text_size))

        if text_kerning:
            blf.enable(0, blf.KERNING_DEFAULT)
        blf.size(0,leveraged_text_size,72)
        text_normal = blf.dimensions(0, "W")[1]  # This is to keep a regular pattern since letters differ in height
        blf.size(0,scaled_text_size,72)
        text_height = blf.dimensions(0, "W")[1]  # This is to keep a regular pattern since letters differ in height
        if text_kerning:
            blf.disable(0, blf.KERNING_DEFAULT)

        # Need to unapply the over scale to compensate for posterior calculations. 
        # This way when BL_UI_Label applies self.over_scale() function to the entire text, 
        # the result will be that only the scale regarding the ui_scale factor will effect.
        over_scale = self.over_scale(1)
        textpos_x = self.x + (self.ui_scale(self.__text_margin) / over_scale) - 1
        textpos_y = self.y - (self.ui_scale(self.__text_margin + round(text_normal+0.499)) / over_scale) + 1

        label = BL_UI_Label(textpos_x, textpos_y, self.width, text_height)
        label.context_it(self.context)
        label.style = 'TOOLTIP'
        
        if self._text_size is None:
            # Do not populate the text_size property to avoid it being leveraged and scaled twice
            pass                          
        else:    
            # Send the original programmer's overriding value and let it be leveraged and scaled by BL_UI_Label class
            label.text_size = text_size    

        label.text_kerning = text_kerning
        label.shadow_size  = widget_style.shadow if self._text_shadow_size is None else self._text_shadow_size 
        label.shadow_offset_x = widget_style.shadow_offset_x if self._text_shadow_offset_x is None else self._text_shadow_offset_x
        label.shadow_offset_y = widget_style.shadow_offset_y if self._text_shadow_offset_y is None else self._text_shadow_offset_y
        label.shadow_color = widget_style.shadow_value if self._text_shadow_color is None else self._text_shadow_color
        label.shadow_alpha = widget_style.shadow_alpha if self._text_shadow_alpha is None else self._text_shadow_alpha

        line_spacing = self.ui_scale(self.__line_space)
        line_count = 0

        if len(self.__tooltip_text_lines) > 0:
            label.text_color = text_color
            for line in self.__tooltip_text_lines:
                label.text = line[0]
                label.draw()
                line_count += 1
                # Need to unapply the over scale to compensate for posterior calculations
                textpos_y -= (round(text_height+0.499) + line_spacing) / over_scale
                label.y_screen = textpos_y
                if line_count >= self.__max_lines_text:  
                    break

        if len(self.__tooltip_shortcut_lines) > 0:
            label.text_color = self._shortcut_color   
            textpos_y -= line_spacing if line_count > 0 else 0 
            label.y_screen = textpos_y
            line_count = 0
            for line in self.__tooltip_shortcut_lines:
                label.text = line[0]
                label.draw()
                line_count += 1
                # Need to unapply the over scale to compensate for posterior calculations
                textpos_y -= (round(text_height+0.499) + line_spacing) / over_scale
                label.y_screen = textpos_y
                if line_count >= self.__max_lines_shortcut:  
                    break

        if len(self.__tooltip_python_lines) > 0:
            label.text_color = self._python_color     
            textpos_y -= line_spacing if line_count > 0 else 0 
            label.y_screen = textpos_y
            line_count = 0
            for line in self.__tooltip_python_lines:
                label.text = line[0]
                label.draw()
                line_count += 1
                # Need to unapply the over scale to compensate for posterior calculations
                textpos_y -= (round(text_height+0.499) + line_spacing) / over_scale
                label.y_screen = textpos_y
                if line_count >= self.__max_lines_python:  
                    break

    # This piece of logic below would be used to merge/abbreviate the latest line to the "greatest" one
    # when going over the configured max lines count, however it needed to take into account the actual
    # pixel-lenght of the strings instead of characters count, so it has been left out for now.

    # def abbreviate_text(self, limit_chars, this_line, last_line):
        # this_line = this_line.rstrip()
        # last_line = last_line.strip()
        # last_save = last_line

        # half_size = round(limit_chars / 2.0) - 1

        # if len(last_line) >= half_size: 
            # last_line = last_line[(len(last_line) - half_size + 2):].lstrip()

        # comb_size = len(this_line) + len(last_line)

        # if comb_size >= limit_chars:
            # over_size = comb_size - limit_chars
            # this_line = this_line[0:(len(this_line) - over_size - 2)].rstrip()
        # else:
            # over_size = limit_chars - len(this_line) - 2
            # if over_size <= len(last_save):
                # last_line = last_save[(len(last_save) - over_size):].lstrip()

        # return (this_line + " ... " + last_line)
