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

# --- ### Header
bl_info = {"name": "BL UI Widgets",
           "description": "UI Widgets to draw in the 3D view",
           "author": "Marcelo M. Marques (fork of Jayanam's original project)",
           "version": (1, 0, 1),
           "blender": (2, 80, 75),
           "location": "View3D > viewport area",
           "support": "COMMUNITY",
           "category": "3D View",
           "warning": "Version numbering diverges from Jayanam's original project",
           "doc_url": "https://github.com/mmmrqs/bl_ui_widgets",
           "tracker_url": "https://github.com/mmmrqs/bl_ui_widgets/issues"
           }

# --- ### Change log

# v1.0.1 (09.20.2021) - by Marcelo M. Marques
# Chang: just some pep8 code formatting

# v1.0.0 (09.01.2021) - by Marcelo M. Marques
# Added: Logic to scale the checkbox according to both Blender's ui scale configuration and this addon 'preferences' setup
# Added: 'text_highlight' property to allow different text color on the selected checkbox.
# Added: 'outline_color' property to allow different color on the checkbox outline (value is standard color tuple).
# Added: 'mark_color' property to allow different color on the check mark tick.
# Added: 'roundness' property to allow the checkbox to be painted with rounded corners,
#         same as that property available in Blender's user themes and it works together with 'rounded_corners' below.
# Added: 'corner_radius' property to allow a limit for the roundness curvature, more useful when 'roundness' property
#         is not overriden by programmer and the one from Blender's user themes is used instead.
# Added: 'rounded_corners' property and coding to allow the checkbox to be painted with rounded corners (value is a 4 elements tuple).
#         Each elements is a boolean value (0 or 1) which indicates whether the corresponding corner is to be rounded or straight
#         in the following clockwise sequence: bottom left, top left, top right, bottom right.
# Added: 'shadow' property and coding to allow the checkbox to be painted with a shadow (value is boolean).
# Added: Logic to allow a checkbox to be disabled (darkned out) and turned off to user interaction.
# Added: 'set_value_changed' function to allow assignment of an external function to be called by mouse_down function.
# Added: Shadow and Kerning related properties that allow the text to be painted using these characteristics.
# Added: Size, Shadow and Kerning attributes default to values retrieved from user theme (may be overriden by programmer).
# Chang: Design of the checkmark changed from 'cross' to a 'tick' symbol.
# Chang: Made it a subclass of 'BL_UI_Patch' instead of 'BL_UI_Widget' so that it can inherit the layout features from there.
# Chang: Instead of hardcoded logic it is now leveraging 'BL_UI_Label' to paint the checkbox text.
# Chang: Mouse over detection changed to cover the area that includes the checkbox label text.
# Fixed: New call to verify_screen_position() so that object behaves alright when viewport is resized.

# --- ### Imports
import bpy
import gpu
import bgl
import blf

from gpu_extras.batch import batch_for_shader

from . bl_ui_patch import BL_UI_Patch
from . bl_ui_label import BL_UI_Label


class BL_UI_Checkbox(BL_UI_Patch):

    def __init__(self, x, y, width, height):

        width = 15      # <-- Fixed-size attempt to match Blender's ui at 1.0 resolution scale
        height = width

        super().__init__(x, y, width, height)

        self._text = "Checkbox"                  # Checkbox text
        self._text_color = None                  # Checkbox text color
        self._text_highlight = None              # Checkbox high color
        self._mark_color = None                  # Checkmark color

        self._style = 'CHECKBOX'                 # Checkbox style indicator (fixed value)
        self._bg_color = None                    # Checkbox face color (when pressed state == 0)
        self._selected_color = None              # Checkbox face color (when pressed state == 3)
        self._outline_color = None               # Checkbox outline color
        self._roundness = None                   # Checkbox corners roundness factor [0..1]
        self._radius = round((width - 1) / 2) - 1  # Checkbox corners circular radius (adjusted for better fitting)
        self._rounded_corners = (1, 1, 1, 1)     # 1=Round/0=Straight, coords:(bottomLeft,topLeft,topRight,bottomRight)
        self._has_shadow = True                  # Indicates whether a shadow must be drawn around the Checkbox

        self._text_size = None                   # Checkbox text size
        self._text_kerning = None                # Checkbox text kerning (True/False)
        self._text_shadow_size = None            # Checkbox text shadow size
        self._text_shadow_offset_x = None        # Checkbox text shadow offset x (positive goes right)
        self._text_shadow_offset_y = None        # Checkbox text shadow offset y (negative goes down)
        self._text_shadow_color = None           # Checkbox text shadow color [0..1] = gray tone, from dark to clear
        self._text_shadow_alpha = None           # Checkbox text shadow alpha value [0..1]

        self.__state = 0                         # 0 is UP; 1 is Selected; 2 is Hover when not selected
        self.__label_width = 0                   # Additional information to compute the full widget area

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
    def text_highlight(self):
        return self._text_highlight

    @text_highlight.setter
    def text_highlight(self, value):
        self._text_highlight = value

    @property
    def mark_color(self):
        return self._mark_color

    @mark_color.setter
    def mark_color(self, value):
        self._mark_color = value

    @property
    def selected_color(self):
        return self._selected_color

    @selected_color.setter
    def selected_color(self, value):
        self._selected_color = value

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
    def is_checked(self):
        return (self.__state == 1)

    @is_checked.setter
    def is_checked(self, value):
        self.__state = 1 if value else 0

    def set_value_changed(self, value_changed_func):
        self.value_changed_func = value_changed_func

    def value_changed_func(self, widget, event, x, y):
        # This must return False when function is not overriden, so that checkbox
        # turns into pressed mode everytime the user clicks over it.
        return True

    # Overrides base class function
    def is_in_rect(self, x, y):
        extra_width = self.width + self.__label_width  # Extended width to include label size
        widget_x = self.over_scale(self.x_screen)
        widget_y = self.over_scale(self.y_screen)
        if (
            (widget_x <= x <= self.over_scale(self.x_screen + extra_width)) and
            (widget_y >= y >= self.over_scale(self.y_screen - self.height))
            ):
            return True

        return False

    # Overrides base class function
    def set_colors(self):
        # Up
        if self.__state == 0:
            if self._bg_color is None:
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.user_interface, "wcol_option")
                color = widget_style.inner
            else:
                color = self._bg_color
        # Down
        elif self.__state == 1:
            if self._selected_color is None:
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.user_interface, "wcol_option")
                color = widget_style.inner_sel
            else:
                color = self._selected_color
        # Hover
        elif self.__state == 2:
            if self._bg_color is None:
                theme = bpy.context.preferences.themes[0]
                widget_style = getattr(theme.user_interface, "wcol_option")
                color = widget_style.inner
            else:
                color = self._bg_color
            # Take the "state 0" background color and "tint" it by either 20% or 10%
            color = self.tint_color(color, (0.2 if color[0] < 0.5 else 0.1))

        if not self._is_enabled:
            # Take the resulting state background color and "dark" it by either 40% or 20%
            color = self.shade_color(color, (0.4 if color[0] > 0.5 else 0.2))

        self.shader.uniform_float("color", color)

    # Overrides base class function
    def draw(self):

        super().draw()

        if not self._is_visible:
            return

        if self.__state != 1:
            return None

        if self._mark_color is None:
            theme = bpy.context.preferences.themes[0]
            widget_style = getattr(theme.user_interface, "wcol_option")
            color = widget_style.item
        else:
            color = self._mark_color

        if not self._is_enabled:
            # Take the checkmark color and "dark" it by either 40% or 20%
            color = self.shade_color(color, (0.4 if color[0] > 0.5 else 0.2))

        self.shader_mark = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

        self.shader_mark.bind()
        self.shader_mark.uniform_float("color", color)

        # Applying UI Scale:
        x_screen = self.over_scale(self.x_screen)
        y_screen = self.over_scale(self.y_screen)
        width = self.over_scale(self.width)
        height = self.over_scale(self.height)

        vertices = ((x_screen + (3 / self.width * width), y_screen - (7 / self.height * height)),
                    (x_screen + (6 / self.width * width), y_screen - (10 / self.height * height)),
                    (x_screen + (11 / self.width * width), y_screen - (3 / self.height * height)))

        self.batch_mark = batch_for_shader(self.shader_mark, 'LINE_STRIP', {"pos": vertices})

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)

        bgl.glLineWidth(self.over_scale(1.5))
        self.batch_mark.draw(self.shader_mark)

        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        bgl.glDisable(bgl.GL_BLEND)

    # Overrides base class function
    def draw_text(self):
        if not (self._is_visible and self._text != ""):
            return

        theme = bpy.context.preferences.themes[0]
        widget_style = getattr(theme.user_interface, "wcol_option")

        if self.__state == 0:
            text_color = tuple(widget_style.text) + (1.0,) if self._text_color is None else self._text_color
        elif self.__state == 1:
            text_color = tuple(widget_style.text_sel) + (1.0,) if self._text_highlight is None else self._text_highlight
        elif self.__state == 2:
            text_color = tuple(widget_style.text) + (1.0,) if self._text_color is None else self._text_color
            # Take the "state 0" text color and "tint" it by either 20% or 10%
            text_color = self.tint_color(text_color, (0.2 if text_color[0] < 0.5 else 0.1))

        theme = bpy.context.preferences.ui_styles[0]
        widget_style = getattr(theme, "widget")

        if self._text_size is None:
            text_size = widget_style.points
            leveraged_text_size = text_size
        else:
            text_size = self._text_size
            leveraged_text_size = self.leverage_text_size(text_size, "widget")
        scaled_size = int(self.over_scale(leveraged_text_size))

        if bpy.app.version >= (3, 0, 0):  # 3.00 issue: 'font_kerning_style' has become extinct
            text_kerning = False
        else:
            text_kerning = (widget_style.font_kerning_style == 'FITTED') if self._text_kerning is None else self._text_kerning
            if text_kerning:
                blf.enable(0, blf.KERNING_DEFAULT)

        rounded_scale = int(round(self.over_scale(1)))
        margin_space = (" " * rounded_scale) if rounded_scale > 0 else " "
        spaced_text = margin_space + self._text + margin_space

        blf.size(0, leveraged_text_size, 72)
        normal = blf.dimensions(0, "W")[1]  # This is to keep a regular pattern since letters differ in height

        blf.size(0, scaled_size, 72)
        length = blf.dimensions(0, spaced_text)[0]
        height = blf.dimensions(0, "W")[1]

        self.__label_width = length

        if text_kerning:
            blf.disable(0, blf.KERNING_DEFAULT)

        textpos_x = self.x_screen + self.width

        top_margin = int((self.height - int(round(normal + 0.499))) / 2.0)

        textpos_y = self.y_screen - top_margin - int(round(normal + 0.499)) + 1

        label = BL_UI_Label(textpos_x, textpos_y, length, height)
        label.style = 'CHECKBOX'

        label.text = spaced_text
        label.text_kerning = text_kerning

        if self._text_size is None:
            # Do not populate the text_size property to avoid it being leveraged and scaled twice
            pass
        else:
            # Send the original programmer's overriding value and let it be leveraged and scaled by BL_UI_Label class
            label.text_size = text_size

        label.shadow_size = widget_style.shadow if self._text_shadow_size is None else self._text_shadow_size
        label.shadow_offset_x = widget_style.shadow_offset_x if self._text_shadow_offset_x is None else self._text_shadow_offset_x
        label.shadow_offset_y = widget_style.shadow_offset_y if self._text_shadow_offset_y is None else self._text_shadow_offset_y
        label.shadow_color = widget_style.shadow_value if self._text_shadow_color is None else self._text_shadow_color
        label.shadow_alpha = widget_style.shadow_alpha if self._text_shadow_alpha is None else self._text_shadow_alpha

        if self._is_enabled:
            label.text_color = text_color
        else:
            if text_color[0] > 0.5:
                # Take the text color and "dark" it by 30%
                label.text_color = self.shade_color(text_color, 0.3)
            else:
                # Take the text color and "tint" it by 30%
                label.text_color = self.tint_color(text_color, 0.3)

        label.context_it(self.context)
        label.draw()

    # Overrides base class function
    def mouse_down(self, event, x, y):
        if self.is_in_rect(x, y):
            # When checkbox is disabled, just ignore the click
            if not self._is_enabled:
                # Consume the mouse event to avoid the camera/target be unselected
                return True
            if not self.value_changed_func(self, event, x, y):
                # Consume the mouse event to avoid the camera/target be unselected
                return True
            # Invert state
            if self.__state != 1:
                # Marked state
                self.__state = 1
            else:
                # Hover state
                self.__state = 2
            return True
        else:
            return False

    # Overrides base class function
    def mouse_move(self, event, x, y):
        if self.is_in_rect(x, y):
            # When checkbox is disabled, just ignore the hover
            if not self._is_enabled:
                return False
            # When checkbox is marked, just ignore the hover
            if self.__state != 1:
                # Hover state
                self.__state = 2
        else:
            if self.__state != 1:
                # Up state
                self.__state = 0
        return False

    # Overrides base class function
    def mouse_up(self, event, x, y):
        if self.is_in_rect(x, y):
            # When checkbox is disabled, just ignore the click
            if not self._is_enabled:
                return True
            else:
                if self.__state != 1:
                    # Hover state
                    self.__state = 2
        return False
