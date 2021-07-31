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
#Added: code to retrieve the color setup values from user preferences theme. These values to be used as default values for all widgets.
#Added: 'style' property that allows the panel to be painted in one of four options per user theme (may be overriden by programmer).
#Added: 'enabled' property to allow external control of enable/disable state (value is boolean). Currently used by the BL_UI_Button class.
#Added: 'anchored' property to allow the panel to be dragged by the user or stay locked in position. The control logic is in BL_UI_Drag_Panel class.
#Added: 'rounded_corners' property and coding to allow the button to be painted with rounded corners (value is a 4 elements tuple).
#        Each elements is a boolean value and indicates whether the corresponding corner is to be rounded or straight
#        in the following sequence: bottomLeft, topLeft, topRight, bottomRight. 
#Added: 'corner_radius' property 
#Added: 'roundness' property 
#Added: 'calc_corners_for_trifan' internal function to calculate the vertices coordinates for a rounded corner widget. 
#Added: 'calc_corners_for_lines' internal function to calculate the vertices coordinates for a rounded corner widget. 
#Added: 'handle_event_finalize' function to call the new 'mouse_up_over' function when the widget is in a enabled state and after polling through the
#        regular handle_event function of all widgets. The complementary function is called in the BL_UI_OT_draw_operator class (bl_ui_draw_op.py).
#Chang: Modified the 'update' function to use 'TRI_FAN' instead of 'TRIS' when painting the widgets on screen with batch_for_shader function.


#--- ### Imports
import bpy
import gpu
import bgl
import blf
import time

from gpu_extras.batch import batch_for_shader
from math import pi, cos, sin

class BL_UI_Widget():

    g_tooltip_widget = None   # Widget object which mouse pointer is currently over (e.g. a given button)
    
    def __init__(self, x, y, width, height):

        self.x = x
        self.y = y
        self.x_screen = x
        self.y_screen = y
        self.width = width
        self.height = height
        self.context = None   
        
        self._tooltip_text = ""        # Text for the tooltip
        self._tooltip_shortcut = ""    # Shortcut for the tooltip
        self._tooltip_python = ""      # Python command for the tooltip

        self._is_visible = True        # Indicates whether the object's draw function must be executed or not
        self._is_enabled = True        # Indicates whether the object is enabled or not (useful for button states)
        self._is_tooltip = False       # Indicates whether the object instance is of 'Tooltip' type

        self.__ui_scale = 0            # Saves the last ui_scale value used
        self.__area_height = 0         # Saves the last area height value
        self.__area_width = 0          # Saves the last area width value
        
        self.__tooltip_gotimer = 0     # Last time when mouse entered widget area
        self.__tooltip_current = False # Indicates whether the tooltip is updated with the current widget data
        self.__tooltip_shifted = False # Indicates whether the container panel has been dragged to another position

        self.__update_shaders = True   # Indicates whether all other shaders need to be updated for the next draw
        self.__mouse_down = False      # Indicates whether mouse button is currently pressed by user
        self.__inrect = False          # Indicates whether mouse pointer is currently over the widget area

    @property
    def visible(self):
        return self._is_visible

    @visible.setter
    def visible(self, value):
        self._is_visible = value

    @property
    def enabled(self):
        return self._is_enabled

    @enabled.setter
    def enabled(self, value):
        self._is_enabled = value

    @property
    def description(self):
        return self._tooltip_text

    @description.setter
    def description(self, value):
        self._tooltip_text = value.rstrip()

    @property
    def shortcut(self):
        return self._tooltip_shortcut

    @shortcut.setter
    def shortcut(self, value):
        self._tooltip_shortcut = value.rstrip()

    @property
    def python_cmd(self):
        return self._tooltip_python

    @python_cmd.setter
    def python_cmd(self, value):
        self._tooltip_python = value.rstrip()

    @property
    def tooltip_moved(self):
        return self.__tooltip_shifted

    @tooltip_moved.setter
    def tooltip_moved(self, value):
        self.__tooltip_shifted = value

    def RC_PINNED(self):
        """ Keep Remote Control pinned when resizing viewport. 
            If (ON): remote panel stays in place regardless of viewport resizing; 
            If (OFF): remote panel slides together with viewport's bottom border.
        """
        package = __package__[0:__package__.find(".")]
        return (bpy.context.preferences.addons[package].preferences.RC_PINNED)

    def RC_SCALE(self):
        """ Scaling to be applied on the Remote Control panel  
            over (in addition to) the interface ui_scale.
        """
        package = __package__[0:__package__.find(".")]
        return (bpy.context.preferences.addons[package].preferences.RC_SCALE)

    def ui_scale(self, value):
        # From Preferences/Interface/"Display"
        return int(round(value * bpy.context.preferences.view.ui_scale))
        
    def over_scale(self, value):
        # Applies the over scale as configured in the addon preferences
        return int(round(self.ui_scale(value) * self.RC_SCALE()))
        
    def leverage_text_size(self, text_size, style):
        # Re-size the programmer's informed text size in relation to Blender's standard font types.
        # Depending on the selectd theme, these numbers below may have a little discrepancy, sorry.
        theme = bpy.context.preferences.ui_styles[0]
        widget_style = getattr(theme, style)
        style_size = widget_style.points
        if style == "panel_title":
            factor = (style_size - 12) / 12  # Would be 11 for 'Deep Gray', 'Minimal Dark' and 'Modo' v2.93 themes
        elif style == "widget":
            factor = (style_size - 11) / 11  # Would be 10 for 'Minimal Dark' and 'Modo' v2.93 themes
        elif style == "widget_label":
            factor = (style_size - 11) / 11  # Would be 10 for 'Minimal Dark' v2.93 theme
        return int(round(text_size*(1 + factor)))

    def tooltip_start(self, x, y):
        base_class = super().__thisclass__.__mro__[-2]  # This stunt only to avoid hard coding the Base class name
        base_class.g_tooltip_widget = self    
        self.__tooltip_gotimer = time.time()
        self.__tooltip_current = False
        
    def tooltip_clear(self):
        self.__tooltip_gotimer = 0
        self.__tooltip_current = False
    
    def set_location(self, x, y):
        self.x = x
        self.y = y
        self.x_screen = x
        self.y_screen = y
        if self.__area_height == 0 and self.__area_width == 0: 
            self.__area_height = self.context.area.height
            self.__area_width = self.context.area.width
        self.update(x,y)

    def init(self, context):
        self.context = context
        self.update(self.x, self.y)
    
    def context_it(self, context):
        self.context = context

    def update(self, x, y):
        """ Logic is not calling this function at every draw pass so as to save runtime processing.
            The only impact is that the background rectangle of buttons, patches, and panels will
            not get their rounded corners adjusted in real time when user plays with the roundness 
            values under Preferences/Themes, but eventually it will catch up and get updated. 
        """
        area_height = self.get_area_height()
            
        if self._is_tooltip:
            base_class = super().__thisclass__.__mro__[-2]  
            widget = base_class.g_tooltip_widget
            if not self.prepare_tooltip_data(widget):  # This function in: bl_ui_tooltip.py 
                return None
        else:
            self.x_screen = int(x)
            self.y_screen = int(y)
        
        y_screen_flip = area_height - self.y_screen
        
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            
        if self._radius > 10:  #was: self._radius == 0 or self._radius > 10 or self._rounded_corners == (0,0,0,0):
            vertices = self.calc_corners_for_trifan(self.x_screen, y_screen_flip, self.width, self.height, self._radius, 'FULL')
            self.batch_panel = batch_for_shader(self.shader, 'TRI_FAN', {"pos" : vertices})
        else:
            vertices = self.calc_corners_for_lines(self.x_screen, y_screen_flip, self.width, self.height, self._radius, 'FULL')
            self.batch_panel = batch_for_shader(self.shader, 'LINES', {"pos" : vertices})

        self.__update_shaders = True
    
    def verify_screen_position(self, area_height):        
        if self._is_tooltip:
            # Trying to save some runtime by not executing an update action if not necessary
            base_class = super().__thisclass__.__mro__[-2]  
            widget = base_class.g_tooltip_widget
            if self.__tooltip_shifted or not widget.__tooltip_current:
                self.update(0,0)
                widget.__tooltip_shifted = False
                widget.__tooltip_current = True
        else:
            # Trying to save some runtime by not executing an update action if not necessary
            if self.__area_height != area_height or self.__ui_scale != self.over_scale(10000):
                former_area_height = self.__area_height
                self.__area_height = area_height 
                self.__ui_scale = self.over_scale(10000)
                if self.RC_PINNED():
                    # This is to prevent the panel to slide when user resizes screen viewport
                    drag_offset_x = 0   # Want to keep same x_pos
                    drag_offset_y = 0   # Want to keep same y_pos
                    self.update(self.x_screen - drag_offset_x, self.y_screen - drag_offset_y)
                else:
                    if former_area_height > 0:
                        drag_offset_x = 0   # Want to keep same x_pos (placeholder for future enhancements)
                        drag_offset_y = former_area_height - area_height
                        self.update(self.x_screen - drag_offset_x, self.y_screen - drag_offset_y)
        
    def halt_tooltip(self):
        # Check whether it is time to show the tooltip or not; delay is hard coded below as 1 (one) second
        base_class = super().__thisclass__.__mro__[-2]  
        widget = base_class.g_tooltip_widget
        # From Preferences/Interface/"Display"
        prefs = bpy.context.preferences.view    
        if not prefs.show_tooltips:
            # Tooltip display is turned off in Blender preferences
            return True
        if widget is None:
            # Widget has no tooltip initialized
            return True
        if widget.__tooltip_gotimer == 0:
            # Timer has not been started
            return True
        if widget._tooltip_text == "" and widget._tooltip_shortcut == "" and \
           (widget._tooltip_python == "" or not prefs.show_tooltips_python): 
            # Widget has no tooltip message to display
            return True
        if time.time() - widget.__tooltip_gotimer < 1:
            # Timer has not reached the threshold yet
            return True

        return False
        
    def draw(self):
        ''' Note: 
            This function is used by BL_UI_Drag_Panel, BL_UI_Patch, BL_UI_Button and BL_UI_Tooltip classes.
            All other classes do have an overriding draw function in their own module coding.  
        '''
        if not self.visible:
            return
            
        if self._is_tooltip:
            if self.halt_tooltip():
                return

        area_height = self.get_area_height()
        
        self.verify_screen_position(area_height)

        self.shader.bind()
        
        self.set_colors()
        
        bgl.glEnable(bgl.GL_BLEND)

        # The following statements make the contour nicer but causes the background to be translucid, 
        # so I've disabled them till I figure out a better work around 
        # if self._radius > 10:  #was: self._radius == 0 or self._radius > 10 or self._rounded_corners == (0,0,0,0):
            # bgl.glEnable(bgl.GL_POLYGON_SMOOTH)
        # else:
            # bgl.glEnable(bgl.GL_LINE_SMOOTH)

        self.batch_panel.draw(self.shader) 
        
        # if self._radius > 10:  #was: self._radius == 0 or self._radius > 10 or self._rounded_corners == (0,0,0,0):
            # bgl.glDisable(bgl.GL_POLYGON_SMOOTH)
            # bgl.glEnable(bgl.GL_LINE_SMOOTH)

        bgl.glEnable(bgl.GL_LINE_SMOOTH)

        self.draw_outline()
        
        self.draw_shadow()
        
        bgl.glDisable(bgl.GL_LINE_SMOOTH)

        self.draw_image()

        self.draw_text()  
        
        bgl.glDisable(bgl.GL_BLEND)
        
        self.__update_shaders = False

    def set_colors(self):
        if not (self._bg_color is None):
            bgColor = self._bg_color 
        elif self._bg_style == 'NONE':
            # Invisible (good as placeholder for icons and images)
            bgColor = (0,0,0,0) 
        elif self._bg_style == 'TOOLTIP':
            # From Preferences/User Interface/"Tooltip"
            theme = bpy.context.preferences.themes[0]
            widget_style = getattr(theme.user_interface, "wcol_tooltip")
            bgColor = widget_style.inner
        else:
            # From Preferences/3D Viewport/"Panel Colors"
            theme = bpy.context.preferences.themes[0]
            widget_style = getattr(theme.view_3d.space, "panelcolors")               
            if self._bg_style == 'HEADER':
                bgColor = widget_style.header
            elif self._bg_style == 'PANEL':
                bgColor = widget_style.back
            elif self._bg_style == 'SUBPANEL':
                bgColor = widget_style.sub_back
            else:
                # Warning error out color :-)
                bgColor = (1,0,0,1)
        self.shader.uniform_float("color", bgColor)

    def tint_color(self, input_color, amount):
        # Turns the input color into a tinted tone per some percent amount
        if amount <= 0:
            output_color = input_color  # No changes
        elif amount >= 1:
            output_color = (1,1,1,input_color[3])  # Turn it into white
        else:
            r = 1 - ((1 - amount) * (1 - input_color[0]))
            g = 1 - ((1 - amount) * (1 - input_color[1]))
            b = 1 - ((1 - amount) * (1 - input_color[2]))
            output_color = (r,g,b,input_color[3])
        return output_color    

    def shade_color(self, input_color, amount):
        # Turns the input color into a shaded tone per some percent amount
        if amount <= 0:
            output_color = input_color  # No changes
        elif amount >= 1:
            output_color = (0,0,0,input_color[3])  # Turn it into black
        else:
            r = (1 - amount) * input_color[0]
            g = (1 - amount) * input_color[1]
            b = (1 - amount) * input_color[2]
            output_color = (r,g,b,input_color[3])
        return output_color    

    def draw_outline(self):
        if not (self._outline_color is None):
            color = self._outline_color 
            if color[3] == 0:
                # Means that the drawing will be invisible, so get out of here
                return None
        elif self._bg_style == 'TOOLTIP':
            theme = bpy.context.preferences.themes[0]
            widget_style = getattr(theme.user_interface, "wcol_tooltip")
            color = tuple(widget_style.outline) + (1.0,)
        else:
            theme = bpy.context.preferences.themes[0]
            widget_style = getattr(theme.user_interface, "wcol_tool")
            color = tuple(widget_style.outline) + (1.0,)

        if self.__update_shaders:
            area_height = self.get_area_height()
            y_screen_flip = area_height - int(self.y_screen)
            self.shader_outline = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            
        self.shader_outline.uniform_float("color", color)
        
        if self._radius > 10: #was: self._radius == 0 or self._radius > 10 or self._rounded_corners == (0,0,0,0):
            bgl.glLineWidth(1)
            if self.__update_shaders:
                vertices = self.calc_corners_for_trifan(int(self.x_screen), y_screen_flip, self.width, self.height, self._radius, 'FULL')
                self.batch_outline = batch_for_shader(self.shader_outline, 'LINE_LOOP', {"pos" : vertices})
            self.batch_outline.draw(self.shader_outline) 
        else:
            # bgl.glPointSize(1)
            # vertices = self.calc_corners_for_lines(int(self.x_screen), y_screen_flip, self.width, self.height, self._radius, 'OUTLINE-A')
            # self.batch_outline = batch_for_shader(self.shader_outline, 'POINTS', {"pos" : vertices})
            # self.batch_outline.draw(self.shader_outline) 
            # bgl.glLineWidth(1)
            # vertices = self.calc_corners_for_lines(int(self.x_screen), y_screen_flip, self.width, self.height, self._radius, 'OUTLINE-B')
            # self.batch_outline = batch_for_shader(self.shader_outline, 'LINES', {"pos" : vertices})
            # self.batch_outline.draw(self.shader_outline) 
            bgl.glLineWidth(1)
            if self.__update_shaders:
                vertices = self.calc_corners_for_lines(int(self.x_screen), y_screen_flip, self.width, self.height, self._radius, 'OUTLINE-A')
                self.batch_outline = batch_for_shader(self.shader_outline, 'LINE_LOOP', {"pos" : vertices})
            self.batch_outline.draw(self.shader_outline) 

    def draw_shadow(self):
        if not self.shadow:
            return None

        # Paint shadow
        if self.__update_shaders:
            area_height = self.get_area_height()
            y_screen_flip = area_height - int(self.y_screen)
            self.shader_shadow1 = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            self.shader_shadow2 = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

        self.shader_shadow1.uniform_float("color", (0,0,0,0.35))
        self.shader_shadow2.uniform_float("color", (0,0,0,0.35))
        
        if self._radius > 10: #was: self._radius == 0 or self._radius > 10 or self._rounded_corners == (0,0,0,0):
            bgl.glLineWidth(1)
            if self.__update_shaders:
                vertices = self.calc_corners_for_trifan(int(self.x_screen), y_screen_flip, self.width, self.height, self._radius, 'SHADOW')
                self.batch_shadow1 = batch_for_shader(self.shader_shadow1, 'LINE_STRIP', {"pos" : vertices})
            self.batch_shadow1.draw(self.shader_shadow1) 
        else:
            bgl.glPointSize(1)
            if self.__update_shaders:
                vertices = self.calc_corners_for_lines(int(self.x_screen), y_screen_flip, self.width, self.height, self._radius, 'SHADOW-A')
                self.batch_shadow1 = batch_for_shader(self.shader_shadow1, 'POINTS', {"pos" : vertices})
            self.batch_shadow1.draw(self.shader_shadow1) 
            bgl.glLineWidth(1)
            if self.__update_shaders:
                vertices = self.calc_corners_for_lines(int(self.x_screen), y_screen_flip, self.width, self.height, self._radius, 'SHADOW-B')
                self.batch_shadow2 = batch_for_shader(self.shader_shadow2, 'LINES', {"pos" : vertices})
            self.batch_shadow2.draw(self.shader_shadow2) 
            # bgl.glLineWidth(1)
            # vertices = self.calc_corners_for_lines(int(self.x_screen), y_screen_flip, self.width, self.height, self._radius, 'SHADOW')
            # self.batch_shadow = batch_for_shader(self.shader_shadow, 'LINE_STRIP', {"pos" : vertices})
            # self.batch_shadow.draw(self.shader_shadow) 

    def draw_text(self):
        # This one applies only to objects of BL_UI_Button and BL_UI_Tooltip classes, 
        # so the full overriding functions are in their py module
        pass

    def draw_image(self):
        if self._image is not None:
            try:
                area_height = self.get_area_height()

                y_screen_flip = area_height - self.over_scale(self.y_screen)
        
                off_x, off_y =  self.over_scale(self._image_position)
                sx, sy = self.over_scale(self._image_size)
                
                # Bottom left, top left, top right, bottom right
                vertices = ((self.over_scale(self.x_screen) + off_x, y_screen_flip - off_y), 
                            (self.over_scale(self.x_screen) + off_x, y_screen_flip - sy - off_y), 
                            (self.over_scale(self.x_screen) + off_x + sx, y_screen_flip - sy - off_y),
                            (self.over_scale(self.x_screen) + off_x + sx, y_screen_flip - off_y))
                
                self.shader_img = gpu.shader.from_builtin('2D_IMAGE')
                self.batch_img = batch_for_shader(self.shader_img, 'TRI_FAN', 
                {
                    "pos": vertices,
                    "texCoord": ((0, 1), (0, 0), (1, 0), (1, 1)), 
                },)

                bgl.glActiveTexture(bgl.GL_TEXTURE0)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, self._image.bindcode)

                self.shader_img.bind()
                self.shader_img.uniform_int("image", 0)
                self.batch_img.draw(self.shader_img) 
            except:
                pass

    def handle_event(self, event):
        x = event.mouse_region_x
        y = event.mouse_region_y

        ##-- personalized criteria for the Reference Cameras addon --
        # This is an ugly workaround till I figure out how to signal to the N-panel coding that this remote control panel has been finished.
        # This is to detect when user changed workspace
        try:
            if not (self.context.space_data.type == 'VIEW_3D'):
                bpy.context.scene.var.RemoVisible = False
                return False
        except: 
            bpy.context.scene.var.RemoVisible = False
            return False
        ##-- end of the personalized criteria for the given addon --

        if(event.type == 'LEFTMOUSE'):
            if(event.value == 'PRESS'):
                self.tooltip_clear()
                self.__mouse_down = True
                return self.mouse_down(event, x, y)
            else:
                self.tooltip_clear()
                if self.enabled:
                    self.__mouse_down = False
                    return self.mouse_up(event, x, y)
                else:
                    ##-- personalized criteria for the Reference Cameras addon --
                    # This prevents the user to unselect camera/target by clicking on a disabled widget
                    return self.is_in_rect(x, y)
                    ##-- end of the personalized criteria for the given addon --
        
        elif(event.type == 'MOUSEMOVE'):
            inrect = self.is_in_rect(x, y)
            if not self.__inrect and inrect:
                # We've just entered the rect
                self.__inrect = True
                self.tooltip_start(x, y)
                return self.mouse_enter(event, x, y)
            elif self.__inrect and not inrect:
                # We've just left the rect
                self.__inrect = False
                self.tooltip_clear()
                return self.mouse_exit(event, x, y)
            else:    
                # We've been moving around
                return self.mouse_move(event, x, y)

        elif(event.value == 'PRESS' and (event.ascii != '' or event.type in self.get_input_keys() )):
            self.tooltip_clear()
            return self.text_input(event)

        elif('MOUSE' in event.type):
            self.tooltip_clear()

        return False    

    def handle_event_finalize(self, event):
        if self.enabled:
            # Want to run it just for the mouse_up event
            if(event.type == 'LEFTMOUSE'):
                if(event.value != 'PRESS'):
                    self.mouse_up_over()
        return False

    def get_input_keys(self):
        return []

    def get_area_height(self):
        return self.context.area.height

    def get_area_width(self):
        return self.context.area.width

    def is_in_rect(self, x, y):
        area_height = self.get_area_height()
        widget_y = area_height - self.y_screen
        if (
            (self.over_scale(self.x_screen) <= x <= self.over_scale(self.x_screen + self.width)) and 
            (self.over_scale(widget_y) >= y >= self.over_scale(widget_y - self.height))
            ):
            return True
          
        return False      

    def text_input(self, event):       
        return False

    # Mouse down handler functions
    def set_mouse_down(self, mouse_down_func):
        self.mouse_down_func = mouse_down_func  
 
    def mouse_down_func(self, widget, event, x, y):
        return False 
 
    def mouse_down(self, event, x, y):       
        return self.mouse_down_func(self, event, x, y)

    # Mouse up handler functions
    def set_mouse_up(self, mouse_up_func):
        self.mouse_up_func = mouse_up_func  
 
    def mouse_up_func(self, widget, event, x, y):
        return False 
 
    def mouse_up(self, event, x, y):
        self.mouse_up_func(self, event, x, y)
        
    def mouse_up_over(self):
        pass

    # Mouse enter handler functions
    def set_mouse_enter(self, mouse_enter_func):
        self.mouse_enter_func = mouse_enter_func  
 
    def mouse_enter_func(self, widget, event, x, y):
        return False 
 
    def mouse_enter(self, event, x, y):
        self.mouse_enter_func(self, event, x, y)

    # Mouse exit handler functions
    def set_mouse_exit(self, mouse_exit_func):
        self.mouse_exit_func = mouse_exit_func  
 
    def mouse_exit_func(self, widget, event, x, y):
        return False 
 
    def mouse_exit(self, event, x, y):
        self.mouse_exit_func(self, event, x, y)

    # Mouse move handler functions
    def set_mouse_move(self, mouse_move_func):
        self.mouse_move_func = mouse_move_func  
 
    def mouse_move_func(self, widget, event, x, y):
        return False 
 
    def mouse_move(self, event, x, y):
        self.mouse_move_func(self, event, x, y)
        
    #-- Helper functions ---------------------------------------------------------------
        
    def calc_corners_for_trifan(self, x_screen, y_screen, width, height, radius, selection):
        ''' 
            Clockwise coordinates: (bottom left, top left, top right, bottom right)
            Argument selection: value can be 'FULL' or 'SHADOW': 
             - If 'FULL', returns coordinates for all 4 corners
             - If 'SHADOW', returns only coordinates to draw a shadow
        '''
        # Applying UI Scale:
        x_screen = self.over_scale(x_screen)
        y_screen = self.over_scale(y_screen)
        width = self.ui_scale(width) if self._is_tooltip else self.over_scale(width)
        height = self.ui_scale(height) if self._is_tooltip else self.over_scale(height)
        
        if not (self._roundness is None):
            roundness = self._roundness
            #
        elif self._bg_style == 'TOOLTIP':
            # From Preferences/User Interface/"Tooltip"
            theme = bpy.context.preferences.themes[0]
            widget_style = getattr(theme.user_interface, "wcol_tooltip")
            roundness = widget_style.roundness        
        else:
            # From Preferences/User Interface/"Tool"
            theme = bpy.context.preferences.themes[0]
            widget_style = getattr(theme.user_interface, "wcol_tool")
            roundness = widget_style.roundness        

        r = round(roundness*radius) 
        if r > int(height/2.0):
            r = int(height/2.0)
            
        if r <= 0:
            r = 0
            use_rounded_corners = (0,0,0,0)
        else:    
            use_rounded_corners = self._rounded_corners

        w = width  - 1
        h = height - 1
        
        coords = []
        
        if use_rounded_corners != (0,0,0,0):
            # Traditional Method 
            newco = []
            segments = r + 1
            m = (1.0 / (4*r - 1)) * (pi * 2)
            for p in range(segments):
                x = cos(m * p) * r
                y = sin(m * p) * r
                newco.append((round(x), round(y)))
            newco = sorted(newco, key=lambda c: (c[0],-c[1]))    

            # Alternative Method (not much good; kept for documentation)
            # x = 0
            # y = r
            # d = int(3 - 2*r)

            # coords.append((x, y))
            # coords.append((y, x))
            # while y >= x:
                # x = x + 1
                # if d > 0:
                    # y = y - 1
                    # d = d + 4*(x-y) + 10
                # else:
                    # d = d + 4*x + 6
                # coords.append((x, y))
                # coords.append((y, x))
            # newco = list(set(coords))
            # newco = sorted(newco, key=lambda c: (c[0],-c[1]))
            # coords.clear()

        if selection == 'FULL':
            # Top Left corners
            if use_rounded_corners[1] == 0: 
                coords.append((x_screen, y_screen))
            else:
                corner_center = (x_screen + r, y_screen - r)
                for c in reversed(newco):
                    coords.append((corner_center[0] - c[0], corner_center[1] + c[1]))

            # Top Right corners
            if use_rounded_corners[2] == 0: 
                coords.append((x_screen + w, y_screen))
            else:
                corner_center = (x_screen + w - r, y_screen - r)
                for c in newco:
                    coords.append((corner_center[0] + c[0], corner_center[1] + c[1]))

        # Shadow right border starting point 
        if selection == 'SHADOW':
            coords.append((x_screen + w + 1, y_screen - int(h/2)))

        # Bottom Right corners
        if use_rounded_corners[3] == 0: 
            if selection == 'SHADOW':
                # Apply an offset of some pixels
                coords.append((x_screen + w + 1, y_screen - h - 1))
            else:
                coords.append((x_screen + w, y_screen - h))
        else:
            corner_center = (x_screen + w - r, y_screen - h + r)
            for c in reversed(newco):
                if selection == 'SHADOW':
                    # Apply an offset of some pixels
                    coords.append((corner_center[0] + c[0] + 1, corner_center[1] - c[1] - 1))
                else:
                    coords.append((corner_center[0] + c[0], corner_center[1] - c[1]))

        # Bottom Left corners
        if use_rounded_corners[0] == 0 or selection == 'SHADOW':
            if selection == 'SHADOW':
                # Apply an offset of some pixels
                k = 0 if use_rounded_corners[0] == 0 else r
                coords.append((x_screen + k + 1, y_screen - h - 1))
            else:
                coords.append((x_screen, y_screen - h))
        else:
            corner_center = (x_screen + r, y_screen - h + r)
            for c in newco:
                coords.append((corner_center[0] - c[0], corner_center[1] - c[1]))

        return coords
        
    def calc_corners_for_lines(self, x_screen, y_screen, width, height, radius, selection):
        ''' 
            Clockwise coordinates: (bottom left, top left, top right, bottom right).
            Argument selection: value can be 'FULL','OUTLINE-A','OUTLINE-B','SHADOW','SHADOW-A','SHADOW-B': 
             - If 'FULL', returns coordinates for raster lines covering the entire background
             - If 'OUTLINE-A', returns only coordinates to draw the outline rounded corner points
             - If 'OUTLINE-B', returns only coordinates to draw the outline straight border lines
             - If 'SHADOW', returns full coordinates to draw a shadow (includes corner and two borders)
             - If 'SHADOW-A', returns only coordinates to draw a shadow for the rounded corner points
             - If 'SHADOW-B', returns only coordinates to draw a shadow for the straight border lines
        '''
        # Applying UI Scale:
        x_screen = self.over_scale(x_screen)
        y_screen = self.over_scale(y_screen)
        width = self.ui_scale(width) if self._is_tooltip else self.over_scale(width)
        height = self.ui_scale(height) if self._is_tooltip else self.over_scale(height)

        if not (self._roundness is None):
            roundness = self._roundness
            #
        elif self._bg_style == 'TOOLTIP':
            # From Preferences/User Interface/"Tooltip"
            theme = bpy.context.preferences.themes[0]
            widget_style = getattr(theme.user_interface, "wcol_tooltip")
            roundness = widget_style.roundness        
        else:
            # From Preferences/User Interface/"Tool"
            theme = bpy.context.preferences.themes[0]
            widget_style = getattr(theme.user_interface, "wcol_tool")
            roundness = widget_style.roundness        

        r = round(roundness*radius) 
        if r > int(height/2.0):
            r = int(height/2.0)

        x = x_screen
        y = y_screen
        
        w = width  - 1
        h = height - 1

        coords = self._get_mapped_coords(r)
        
        if selection != 'FULL':
            # Building the contour coordinates by determining points in the 4 corners
            if selection != 'SHADOW-A':
                o0 = [] 
                o2 = [] 
                for c in coords:
                    # Bottom Left corners
                    offset = 0 if self._rounded_corners[0] == 0 else c[0]
                    o0.append((x + 0 + offset, y - h + c[1]))   
                    # Top Right corners
                    offset = 0 if self._rounded_corners[2] == 0 else c[0]
                    o2.append((x + w - offset, y - 0 - c[1]))   
            o1 = [] 
            o3 = []
            for c in reversed(coords):
                # Top Left corners
                offset = 0 if self._rounded_corners[1] == 0 else c[0]
                o1.append((x + 0 + offset, y - 0 - c[1]))   
                # Bottom Right corners
                offset = 0 if self._rounded_corners[3] == 0 else c[0]
                o3.append((x + w - offset, y - h + c[1]))   

        if selection == 'OUTLINE-A':
            # Building a list with only the contour corners
            outline = o0 + o1 + o2 + o3
            return outline

        if selection == 'OUTLINE-B':
            # Determining the 4 borders lines to use with outline contour corners
            borders = []
            if o0[-1] != o1[ 0]:
                borders.append(o0[-1])
                borders.append(o1[ 0])
            if o1[-1] != o2[ 0]:
                borders.append(o1[-1])
                borders.append(o2[ 0])
            if o2[-1] != o3[ 0]:
                borders.append(o2[-1])
                borders.append(o3[ 0])
            if o3[-1] != o0[ 0]:
                borders.append(o3[-1])
                borders.append(o0[ 0])
            return borders

        if selection == 'SHADOW':
            # Building shadow entire profile 
            shadow = []
            shadow.append((o0[ 0][0] + 0, o0[ 0][1] - 1)) 
            for c in reversed(o3):
                shadow.append((c[0] + 1, c[1] - 1))
            shadow.append((o2[-1][0] + 1, y - (h/2) - 0))
            return shadow

        if selection == 'SHADOW-A':
            # Building shadow corner
            shadow_curve = []
            for c in o3:
                shadow_curve.append((c[0] + 1, c[1] - 1))
            return shadow_curve

        if selection == 'SHADOW-B':
            # Determining the 2 borders lines to use with shadow contour corner 
            shadow_lines = []
            shadow_lines.append((o0[ 0][0] + 0, o0[ 0][1] - 1)) 
            shadow_lines.append((o3[-1][0] + 1, o3[-1][1] - 1))
            shadow_lines.append((o3[ 0][0] + 1, o3[ 0][1] - 0))
            shadow_lines.append((o2[-1][0] + 1, y - (h/2) - 0))
            return shadow_lines

        if selection == 'FULL':
            # Building array of horizontal lines for entire background
            lines = []
            #- Top section
            prior = coords[0]
            for c in coords:
                if c[1] != prior[1]:
                    cy = y - prior[1]
                    offset = 0 if self._rounded_corners[1] == 0 else prior[0]  # Top Left corners
                    lines.append((x + 0 + offset, cy))
                    offset = 0 if self._rounded_corners[2] == 0 else prior[0]  # Top Right corners
                    lines.append((x + w - offset, cy))
                prior = c
            cy = y - prior[1]
            offset = 0 if self._rounded_corners[1] == 0 else prior[0]  # Top Left corners
            lines.append((x + 0 + offset, cy))
            offset = 0 if self._rounded_corners[2] == 0 else prior[0]  # Top Right corners
            lines.append((x + w - offset, cy))
            #- Middle section
            next_y = cy - 1
            last_y = y - h + coords[-1][1] 
            while next_y > last_y:
                lines.append((x + 0, next_y))
                lines.append((x + w, next_y))
                next_y -= 1
            #- Bottom section
            prior = (-1,-1)
            for c in reversed(coords):
                if c[1] != prior[1]:
                    cy = y - h + c[1]
                    offset = 0 if self._rounded_corners[0] == 0 else c[0]  # Bottom Left corners
                    lines.append((x + 0 + offset, cy))
                    offset = 0 if self._rounded_corners[3] == 0 else c[0]  # Bottom Right corners
                    lines.append((x + w - offset, cy))
                prior = c
            return lines
            
    def _get_mapped_coords(self, radius):
        ''' 
            Disclaimer:  I decided to use a combination of LINES and POINTS shaders instead of TRIS
            because the BGL was making some funny business with the rounded corners by not respecting
            the set of informed points, thus causing ugly assymetric results. The maps in here were
            manually created by me and they should always give a nice contour. 
            May the GOD of I.T. forgive me!
        '''
        map = [( 0,),
               ( 1,0),
               ( 2,0,1),
               ( 3,0,2,1,1),
               ( 4,0,3,1,2,1),
               ( 5,0,4,1,3,1,2),
               ( 6,0,5,1,4,1,3,2,2),
               ( 7,0,6,1,5,1,4,2,3,2),
               ( 8,0,7,1,6,1,5,2,4,2,3),
               ( 9,0,8,1,7,1,6,2,5,2,4,3),
               (10,0,9,1,8,1,7,1,6,2,5,2,4,3),
               ]
        i = 0      
        coords = []
        pointset = map[radius] + tuple(reversed(map[radius]))
        while i < len(pointset):
            coords.append((pointset[i],pointset[i+1]))
            i = i + 2
        return coords