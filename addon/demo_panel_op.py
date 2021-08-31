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

#v0.6.5 (08.01.2021) - by Marcelo M. Marques 
#Added: 'terminate_execution' function that can be overriden by programmer to command termination of the 'Remote Panel'.
#Added: New properties and functions to all widgets (check their corresponding modules for more information). 

#--- ### Imports

import bpy
import os

from bpy.types import Operator

from ..bl_ui_widgets.bl_ui_label import BL_UI_Label  
from ..bl_ui_widgets.bl_ui_patch import BL_UI_Patch  
from ..bl_ui_widgets.bl_ui_checkbox import BL_UI_Checkbox  
from ..bl_ui_widgets.bl_ui_slider import BL_UI_Slider      
from ..bl_ui_widgets.bl_ui_textbox import BL_UI_Textbox    
from ..bl_ui_widgets.bl_ui_button import BL_UI_Button
from ..bl_ui_widgets.bl_ui_tooltip import BL_UI_Tooltip
from ..bl_ui_widgets.bl_ui_draw_op import BL_UI_OT_draw_operator
from ..bl_ui_widgets.bl_ui_drag_panel import BL_UI_Drag_Panel

class DP_OT_draw_operator(BL_UI_OT_draw_operator): ## in: bl_ui_draw_op.py ##
    
    bl_idname = "object.dp_ot_draw_operator"
    bl_label = "bl ui widgets custom operator"
    bl_description = "Operator for bl ui widgets" 
    bl_options = {'REGISTER'}
    	
    #--- Blender interface methods quick documentation
    # def poll: checked before running the operator, which will never run when poll fails. 
    #           used to check if an operator can run, menu items will be greyed out and if key bindings should be ignored.
    #
    # def invoke: called by default when accessed from a key binding and menu, this takes the current context - mouse location.
    #             used for interactive operations such as dragging & drawing.  (hint: think of this as "run by a person") 
    #
    # def description: allows a dynamic tooltip that changes based on the context and operator parameters.
    # 
    # def draw: called to draw options, giving  control over the layout. Without this, options will draw in the order they are defined. 
    #
    # def modal: handles events which would normally access other operators, they keep running until they return FINISHED.
    #            used for operators which continuously run, eg: fly mode, knife tool, circle select are all examples of modal operators. 
    #
    # def execute: runs the operator, assuming values are set by the caller (else use defaults).
    #              used for undo/redo, and executing operators from Python.
    #
    # def cancel: called when Blender cancels a modal operator, not used often. Internal cleanup can be done here if needed.
    
    #--- methods    
    @classmethod
    def poll(cls, context):
        # Show this panel in View_3D only:
        return (context.space_data.type == 'VIEW_3D' and context.mode == 'OBJECT')

    def __init__(self):

        super().__init__()

        package = __package__[0:__package__.find(".")]

        # From Preferences/Themes/"Text Style"
        theme = bpy.context.preferences.themes[0]
        ui = theme.user_interface
        widget_style = getattr(ui, "wcol_state")
        status_color = tuple(widget_style.inner_changed) + (0.3,)

        btnC = 0            # Element counter
        btnS = 4            # Button separation (for the smaller ones) 
        btnG = 0            # Button gap (for the bigger ones)
        btnW = 56           # Button width
        btnH = 40+btnS      # Button height (takes 2 small buttons plus their separation)
        
        marginX = 16
        marginY = 27
        
        btnX = marginX + 1  # Button position X (for the very first button)
        btnY = marginY + 1  # Button position Y (for the very first button)

        self.button1 = BL_UI_Button(btnX, btnY, btnW, btnH)
        self.button1.style = 'RADIO'
        self.button1.text = "PUSH"
        self.button1.textwo = "-ME-"
        self.button1.text_size = 13
        self.button1.textwo_size = 10
        self.button1.rounded_corners = (1,1,0,0)
        self.button1.set_mouse_up(self.button1_click)
        self.button1.set_button_pressed(self.button1_pressed)
        self.button1.description = "Press this button to unlock its brothers. {Let me type a very large description here "+\
                                   "so that the tooltip text ends up being wrapped around very hard causing the entire "+\
                                   "text to be ellipsised (that is, to be dot-dot-dotted) when it flows over the hardcoded "+\
                                   "limit of 3 maximum lines}"
        self.button1.shortcut = "Shortcut: None"
        self.button1.python_cmd = "bpy.ops.object.dp_ot_draw_operator.button1_click()"
        if self.button1_pressed(self.button1): self.button1.state = 3
        btnC += 1 
        # 
        self.button2 = BL_UI_Button((btnX+((btnW-1+btnG)*btnC)), btnY, btnW, btnH)
        self.button2.style = 'RADIO'
        self.button2.text = "HELP"
        self.button2.textwo = "(Go)"
        self.button2.text_size = 13
        self.button2.textwo_size = 10
        self.button2.rounded_corners = (0,0,0,0)
        self.button2.set_mouse_up(self.button2_click)
        self.button2.set_button_pressed(self.button2_pressed)
        self.button2.description = "You can help me by doing as follows:\n" +\
                                   " -Press button 4 to Disable Me\n" +\
                                   " -Press button 1 to Enable Me"
        self.button2.python_cmd = "bpy.ops.object.dp_ot_draw_operator.button2_click()"
        if self.button2_pressed(self.button2): self.button2.state = 3
        btnC += 1
        # 
        self.button3 = BL_UI_Button((btnX+((btnW-1+btnG)*btnC)), btnY, btnW, btnH)
        self.button3.style = 'RADIO'
        self.button3.text = "ADD"
        self.button3.text_size = 13
        self.button3.rounded_corners = (0,0,0,0)
        self.button3.set_mouse_up(self.button3_click)
        self.button3.set_button_pressed(self.button3_pressed)
        self.button3.description = "Adds one Monkey object to 3d View area"
        self.button3.python_cmd = "bpy.ops.object.dp_ot_draw_operator.button3_click()"
        if self.button3_pressed(self.button3): self.button3.state = 3
        btnC += 1
        # 
        self.button4 = BL_UI_Button((btnX+((btnW-1+btnG)*btnC)), btnY, btnW, btnH)
        self.button4.style = 'RADIO'
        self.button4.text = "LOCK"
        self.button4.textwo = "(CTRL-L)"
        self.button4.text_size = 13
        self.button4.textwo_size = 10
        self.button4.rounded_corners = (0,0,1,1)
        self.button4.set_mouse_up(self.button4_click)
        self.button4.set_button_pressed(self.button4_pressed)
        self.button4.enabled = (not bpy.context.scene.var.OpState6)
        self.button4.description = "This button does nothing more than to disable 2 and 3"
        if self.button4_pressed(self.button4): self.button4.state = 3
        btnC += 1
        oldX = (btnX+((btnW-1+btnG)*btnC))
        oldH = btnH
        oldW = btnW
        newX = oldX + marginX + btnW-1 + btnS
        btnW = 96
        btnH = 20
        # 
        self.button5 = BL_UI_Button(newX, btnY, btnW, btnH)
        self.button5.text = "Do Nothing"
        newY = btnY + btnH +btnS
        # 
        self.button6 = BL_UI_Button(newX, newY, btnW, btnH)
        self.button6.selected_color = status_color
        self.button6.text = "Switch Btn 4"
        self.button6.set_mouse_up(self.button6_click)
        self.button6.set_button_pressed(self.button6_pressed)
        self.button6.description = "Switches button 4's state"        
        if self.button6_pressed(self.button6): self.button6.state = 3
        # 
        newX = newX + btnW-1 + btnS 
        btnW = 120
        #
        self.number1 = BL_UI_Slider(newX, btnY, btnW, btnH)
        self.number1.style = 'NUMBER_CLICK'
        self.number1.value = 500
        self.number1.step = 100
        self.number1.unit = "m"
        self.number1.precision = 0
        self.number1.description = "This is my click slider tooltip"        
        self.number1.set_value_updated(self.number1_update)
        # 
        self.slider1 = BL_UI_Slider(newX, newY, btnW, btnH)
        self.slider1.style = 'NUMBER_SLIDE'
        self.slider1.text = "Z Rot"
        self.slider1.value = 1800
        self.slider1.min = 0
        self.slider1.max = 3600
        self.slider1.description = "This is my standard slider tooltip.\nYou can use it to rotate the object"
        self.slider1.set_value_updated(self.slider1_update)
        self.slider1.set_value_display(self.slider1_display)
        #    
        self.objname = "<Press the ADD button so you can edit here>"
        self.textbox1 = BL_UI_Textbox(btnX, newY+35, 350, btnH)
        self.textbox1.text = self.objname
        self.textbox1.max_input_chars = 50
        self.textbox1.description = "Textbox editing entry field"
        self.textbox1.set_value_changed(self.textbox1_changed)
        self.textbox1.enabled = False
        #
        self.check1 = BL_UI_Checkbox(newX, newY+37, btnW, btnH)
        self.check1.text = "Unregit"
        self.check1.set_value_changed(self.check1_changed)
        self.check1.description = "This is my checkbox tooltip"        
        self.check1.python_cmd = "bpy.ops.object.checkbox()"
        self.check1.is_checked = False
        #-----------

        panW = newX+btnW+2+marginX  # Panel desired width  (beware: this math is good for my setup only)
        panH = newY+btnH+0+10+35    # Panel desired height (ditto)

        # Save the panel's size to preferences properties to be used in there
        bpy.context.preferences.addons[package].preferences.RC_PAN_W = panW
        bpy.context.preferences.addons[package].preferences.RC_PAN_H = panH

        # Need this just because I want the panel to be centered
        if bpy.context.preferences.addons[package].preferences.RC_UI_BIND:
            # From Preferences/Interface/"Display"
            ui_scale = bpy.context.preferences.view.ui_scale  
        else:
            ui_scale = 1
        over_scale = bpy.context.preferences.addons[package].preferences.RC_SCALE

        # The panel X and Y coords are in relation to the bottom-left corner of the 3D viewport area
        panX = int((bpy.context.area.width - panW*ui_scale*over_scale) / 2.0) + 1  # Panel X coordinate, for panel's top-left corner 
        panY = panH + 100 - 1  # The '100' is just a spacing                       # Panel Y coordinate, for panel's top-left corner 

        self.panel = BL_UI_Drag_Panel(panX, panY, panW, panH)  
        self.panel.style = 'PANEL'         # Options are: {HEADER,PANEL,SUBPANEL,TOOLTIP,NONE}

        self.tooltip = BL_UI_Tooltip()     # This is for displaying any tooltips

        self.patch1 = BL_UI_Patch(0,0,panW,17)
        self.patch1.style = 'HEADER'
        self.patch1.set_mouse_move(self.patch1_mouse_move)
        
        self.label1 = BL_UI_Label(5,12,panW,17)
        self.label1.style = "TITLE"
        self.label1.text = "Panel Title For Example"
        self.label1.size = 12
        
        self.label2 = BL_UI_Label(panW-100,12,100,17)
        self.label2.text = ""

        self.patch2 = BL_UI_Patch(oldX+10,btnY,oldW,oldH)
        self.patch2.bg_color = (0,0,0,0)
        self.patch2.outline_color = (1,1,1,0.4)
        self.patch2.roundness = 0.4
        self.patch2.corner_radius = 10
        self.patch2.shadow = True
        self.patch2.rounded_corners = (1,1,1,1)
        self.patch2.description = "There is an issue I have not figured out yet,\n" + \
                                  "which causes the image to black out after a while"  
        
        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)
        imagePath = directory + "\\..\\img\\rotate.png" 
        self.patch2.set_image(imagePath)
        self.patch2.set_image_size((32,32))
        self.patch2.set_image_position((11,5))
        
        #-----------
        # Display an 'UNRegister' button on screen
        # ==================================================================
        # -- This is just for demonstration, not to be used in production
        # ==================================================================
        btnH = 32
        newX = panW - marginX - btnH - 2
        newY = panH - btnH - 6
        self.buttonU = BL_UI_Button(newX, newY, btnH, btnH)
        self.buttonU.text = "UNR"
        self.buttonU.text_size = 12
        self.buttonU.text_color = (1,1,1,1)
        self.buttonU.bg_color = (0.5,0,0,1)
        self.buttonU.outline_color = (0.6,0.6,0.6,0.8)
        self.buttonU.corner_radius = btnH/2 - 1
        self.buttonU.roundness = 1.0
        self.buttonU.set_mouse_up(self.buttonU_click)
        self.buttonU.description = "Unregisters the Remote Control panel object and closes it"        
        self.buttonU.python_cmd = "bpy.ops.object.set_remote_control()"
        self.buttonU.visible = False

    def on_invoke(self, context, event):
        # Add your widgets here (TODO: perhaps a better, more automated solution?)
        # --------------------------------------------------------------------------------------------------
        widgets_panel = [
                         self.panel
                        ]
        widgets_items = [self.patch1, self.patch2, self.label1, self.label2,
                         self.button1, self.button2, self.button3, self.button4, self.button5, self.button6, 
                         self.buttonU, self.slider1, self.number1, self.check1, self.textbox1, 
                         self.tooltip, # <-- If there is a tooltip object, it must be the last in this list
                        ]
        # --------------------------------------------------------------------------------------------------

        widgets = widgets_panel + widgets_items

        self.init_widgets(context, widgets)
        
        self.panel.add_widgets(widgets_items)

        self.panel.set_location(self.panel.x, self.panel.y)


    #-- Helper function
    
    def terminate_execution(self):
        '''
            This is a special case 'overriding function' to allow subclass control for terminating/closing the panel.
            Function is defined in class BL_UI_OT_draw_operator (bl_ui_draw_op.py) and available to be inherited here. 
            If not included here the function in the super class just returns 'False' and no termination is executed.
            When 'True" is returned below the execution is auto terminated and the 'Remote Control' panel closes itself.
        '''    
        return (bpy.context.scene.var.RemoVisible == False)


    #-- Button press handlers    
    
    def button1_click(self, widget, event, x, y):
        self.button2.enabled = True
        self.button3.enabled = True
        self.press_only(1)

    def button2_click(self, widget, event, x, y):
        self.press_only(2)

    def button3_click(self, widget, event, x, y):
        bpy.ops.mesh.primitive_monkey_add()
        self.objname = bpy.context.object.name
        self.textbox1.text = "'" + self.objname + "' is her name, but you can edit it here!"
        self.textbox1.enabled = True
        self.press_only(3)

    def button4_click(self, widget, event, x, y):
        self.button2.enabled = False
        self.button3.enabled = False
        self.press_only(4)

# I am not even obligated to create any of these functions, see?
# button5 does not have an active function tied to it at all.
#    def button5_click(self, widget, event, x, y):
#        # Miss Me

    def button6_click(self, widget, event, x, y):
        var = bpy.context.scene.var
        var.OpState6 = (not var.OpState6)
        self.button4.enabled = (not self.button4.enabled)

    def buttonU_click(self, widget, event, x, y):
        self.finish()

    def button1_pressed(self, widget):
        return (bpy.context.scene.var.OpState1)

    def button2_pressed(self, widget):
        return (bpy.context.scene.var.OpState2)

    def button3_pressed(self, widget):
        return (bpy.context.scene.var.OpState3)

    def button4_pressed(self, widget):
        return (bpy.context.scene.var.OpState4)
        
# I am not even obligated to create any of these functions, see?
# button5 does not have an active function tied to it at all.
#    def button5_pressed(self, widget):
#        return (bpy.context.scene.var.OpState5)
        
    def button6_pressed(self, widget):
        return (bpy.context.scene.var.OpState6)
        
    def patch1_mouse_move(self, widget, event, x, y):
        self.label2.text = "x: " + str(x) + "  y: " + str(y)
        return False

    def number1_update(self, widget, value):
        # Example of a dynamic unit conversion with dynamic min/max limits
        converted = False
        if widget.unit == "mm" and value >= 1000:
            # Upscale to meters
            value = value / 1000
            widget.unit = "m" 
            widget.step = 10
            widget.precision = 0
            converted = True
        if widget.unit == "m" and value >= 1000:
            # Upscale to kilometers
            value = value / 1000
            widget.unit = "km" 
            widget.step = 0.1
            widget.precision = 1
            converted = True
        if widget.unit == "km" and value >= 10:
            # I want my hardcoded max limit to be 10 km
            value = 10
            converted = True
        if widget.unit == "km" and value < 1:
            # Downscale to meters
            value = value * 1000
            widget.unit = "m"
            widget.step = 10
            widget.precision = 0
            converted = True
        if widget.unit == "m" and value < 1:
            # Downscale to millimeters
            value = value * 1000
            widget.unit = "mm"
            widget.step = 10
            widget.precision = 0
            converted = True
        if widget.unit == "mm" and value < 1:
            # I want my hardcoded min limit to be 1 mm
            value = 1
            converted = True

        if converted:
            widget.value = round(value, widget.precision)
            return False
        else:
            # By returning True the 'value' argument will be committed to the widget.value property
            return True

    def slider1_update(self, widget, value):
        import math
        try:
            rc = bpy.context.scene.collection
            for obj in rc.objects:
                if obj.type == 'MESH': 
                    obj.rotation_euler[2] = math.radians(value/10)
                    break
        except:
            pass
        return True
    
    def slider1_display(self, widget, value):
        return str(int(round(value/10)))
    
    def textbox1_changed(self, widget, context, former_text, updated_text):
        if updated_text != self.objname:
            if updated_text.strip() == "":
                self.objname = "<Why have you tried to blank her name?>"
                widget.text = self.objname
                return True
            try:
                rc = context.scene.collection
                for obj in rc.objects:
                    if obj.type == 'MESH' and obj.name == self.objname: 
                        obj.name = updated_text
                        self.objname = obj.name
                        break
            except:
                self.objname = "<Error trying to assign this name to object>"
                widget.text = self.objname
        return True
        
    def check1_changed(self, widget, event, x, y):
        self.buttonU.visible = not self.check1.is_checked
        return True


    #-- Helper functions 

    def press_only(self, button):     
        var = bpy.context.scene.var
        var.OpState1 = (button == 1)
        var.OpState2 = (button == 2)
        var.OpState3 = (button == 3)
        var.OpState4 = (button == 4)


##-Register/unregister processes 
def register():
    bpy.utils.register_class(DP_OT_draw_operator)
 
def unregister():
    bpy.utils.unregister_class(DP_OT_draw_operator)            
