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
#Added: 'terminate_execution' function that can be overriden by programmer to command termination of the 'Remote Panel' widget.
#Added: New properties and functions in all widgets (check their corresponding modules for more information). 

#--- ### Imports

import bpy

from bpy.types import Operator

from ..bl_ui_widgets.bl_ui_patch import BL_UI_Patch
from ..bl_ui_widgets.bl_ui_button import BL_UI_Button
from ..bl_ui_widgets.bl_ui_tooltip import BL_UI_Tooltip
from ..bl_ui_widgets.bl_ui_draw_op import BL_UI_OT_draw_operator
from ..bl_ui_widgets.bl_ui_drag_panel import BL_UI_Drag_Panel

#from . reference_cameras import get_target   # <-- not needed anymore but left as example

#----- Diagnostic flag 
DEBUG = 0 # Set it to 0 in the production version; 1 to see diagnostic messages; 2 to enable PyDev debugger

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

        # Panel Layout:
           
        # |ZOOM||H ORB||V ORB||TILT||MOVE||ROLL||POV |   |Reset Target||Lock Position|   |M1|M2|M3| #
        # | GZ ||  RZ ||  RX || RY ||GXYZ|| RXY||GXYZ|   |Display Mesh||Lock Rotation|   |MSave|MC| #

        btnC = 0            # Element counter
        btnS = 4            # Button separation (for the smaller ones) 
        btnG = 0            # Button gap (for the bigger ones)
        btnW = 56           # Button width
        btnH = 40+btnS      # Button height (takes 2 small buttons plus their separation)
        
        marginX = 16        # Margin from left border
        marginY = 10        # Margin from top border 
        
        btnX = marginX + 1  # Button position X (for the very first button)
        btnY = marginY + 1  # Button position Y (for the very first button)

        # Camera Modes:
        # Zoom: Dolly moves only back and forth on camera's axis (G + ZZ + move mouse)
        self.button1 = BL_UI_Button(btnX, btnY, btnW, btnH)
        self.button1.style = 'RADIO'
        self.button1.text = "ZOOM"
        self.button1.textwo = "(GZ)"
        self.button1.text_size = 13
        self.button1.rounded_corners = (1,1,0,0)
        self.button1.set_mouse_up(self.button1_click)
        self.button1.set_button_pressed(self.button1_pressed)
        self.button1.description = "(GZ: Zoom) - Camera LOCAL mode; Pivot Point Active Element"
        self.button1.python_cmd = "bpy.ops.object.ref_camera_panelbutton_zoom()"
        if self.button1_pressed(self.button1): self.button1.state = 3
        btnC += 1 
        # Horizontal Orbit: Camera rotates around the target which stays in place (R + Z + move mouse)
        self.button2 = BL_UI_Button((btnX+((btnW-1+btnG)*btnC)), btnY, btnW, btnH)
        self.button2.style = 'RADIO'
        self.button2.text = "H ORB"
        self.button2.textwo = "(RZ)"
        self.button2.text_size = 13
        self.button2.rounded_corners = (0,0,0,0)
        self.button2.set_mouse_up(self.button2_click)
        self.button2.set_button_pressed(self.button2_pressed)
        self.button2.description = "(RZ: Horizontal Orbit) - Camera GLOBAL mode; Pivot Point 3D Cursor"
        self.button2.python_cmd = "bpy.ops.object.ref_camera_panelbutton_horb()"
        if self.button2_pressed(self.button2): self.button2.state = 3
        btnC += 1
        # Vertical Orbit: Camera rotates around the target which stays in place (R + XX + move mouse)
        self.button3 = BL_UI_Button((btnX+((btnW-1+btnG)*btnC)), btnY, btnW, btnH)
        self.button3.style = 'RADIO'
        self.button3.text = "V ORB"
        self.button3.textwo = "(RX)"
        self.button3.text_size = 13
        self.button3.rounded_corners = (0,0,0,0)
        self.button3.set_mouse_up(self.button3_click)
        self.button3.set_button_pressed(self.button3_pressed)
        self.button3.description = "(RX: Vertical Orbit) - Camera LOCAL mode; Pivot Point 3D Cursor"
        self.button3.python_cmd = "bpy.ops.object.ref_camera_panelbutton_vorb()"
        if self.button3_pressed(self.button3): self.button3.state = 3
        btnC += 1
        # Tilt: Camera stays still, moves from up and down (R + XX + move mouse)
        self.button4 = BL_UI_Button((btnX+((btnW-1+btnG)*btnC)), btnY, btnW, btnH)
        self.button4.style = 'RADIO'
        self.button4.text = "TILT"
        self.button4.textwo = "(RY)"
        self.button4.text_size = 13
        self.button4.rounded_corners = (0,0,0,0)
        self.button4.set_mouse_up(self.button4_click)
        self.button4.set_button_pressed(self.button4_pressed)
        self.button4.enabled = (not bpy.context.scene.var.OpState9)
        self.button4.description = "(RY: Tilt) - Target LOCAL mode; Pivot Point Active Element"
        self.button4.python_cmd = "bpy.ops.object.ref_camera_panelbutton_tilt()"
        if self.button4_pressed(self.button4): self.button4.state = 3
        btnC += 1
        # Translation: Truck/Pedestal moves only from left to right on camera's axis (G + XX/YY/ZZ + move mouse)
        self.button5 = BL_UI_Button((btnX+((btnW-1+btnG)*btnC)), btnY, btnW, btnH)
        self.button5.style = 'RADIO'
        self.button5.text = "MOVE"
        self.button5.textwo = "(GXYZ) "
        self.button5.text_size = 13
        self.button5.rounded_corners = (0,0,0,0)
        self.button5.set_mouse_up(self.button5_click)
        self.button5.set_button_pressed(self.button5_pressed)
        self.button5.description = "(GXYZ: Translation) - Camera+Target GLOBAL mode; Pivot Point Active Element"
        self.button5.python_cmd = "bpy.ops.object.ref_camera_panelbutton_move()"
        self.button5.enabled = (not bpy.context.scene.var.OpState8)
        if self.button5_pressed(self.button5): self.button5.state = 3
        btnC += 1
        # Roll: Camera stays still, lean from left to right (R + XX/YY + move mouse)
        self.button6 = BL_UI_Button((btnX+((btnW-1+btnG)*btnC)), btnY, btnW, btnH)
        self.button6.style = 'RADIO'
        self.button6.text = "ROLL"
        self.button6.textwo = "(RXY)"
        self.button6.text_size = 13
        self.button6.rounded_corners = (0,0,0,0)
        self.button6.set_mouse_up(self.button6_click)
        self.button6.set_button_pressed(self.button6_pressed)
        self.button6.enabled = (not bpy.context.scene.var.OpState9)
        self.button6.description = "(RXY: Rotation) - Camera+Target GLOBAL mode; Pivot Point Active Element"
        self.button6.python_cmd = "bpy.ops.object.ref_camera_panelbutton_roll()"
        if self.button6_pressed(self.button6): self.button6.state = 3
        btnC += 1
        # Perspective: combination of Camera's Translation with Elevation/Rotation
        self.button7 = BL_UI_Button((btnX+((btnW-1+btnG)*btnC)), btnY, btnW, btnH)
        self.button7.style = 'RADIO'
        self.button7.text = "POV"
        self.button7.textwo = "(GXYZ)"
        self.button7.text_size = 13
        self.button7.rounded_corners = (0,0,1,1)
        self.button7.set_mouse_up(self.button7_click)
        self.button7.set_button_pressed(self.button7_pressed)
        self.button7.description = "(GXYZ: Perspective) - Camera GLOBAL mode; Pivot Point Active Element"
        self.button7.python_cmd = "bpy.ops.object.ref_camera_panelbutton_pov()"
        if self.button7_pressed(self.button7): self.button7.state = 3
        btnC += 1
        newX = (btnX+((btnW-1+btnG)*btnC)) + marginX
        btnW = 96
        btnH = 20
        # Reset Target: Sets Target Location and Rotation to (0,0,0) and removes related locks
        self.buttonR = BL_UI_Button(newX, btnY, btnW, btnH)
        self.buttonR.style = 'TOOL'
        self.buttonR.text = "Reset Target"
        self.buttonR.set_mouse_up(self.buttonR_click)
        self.buttonR.description = "Sets Target Location and Rotation to (0,0,0) and removes related locks"
        self.buttonR.python_cmd = "bpy.ops.object.ref_camera_panelbutton_rset()"
        newY = btnY + btnH + btnS
        # Blink Mesh: Turns mesh visibility on/off
        preferences = bpy.context.preferences.addons[package].preferences
        blink_on = round(preferences.RC_BLINK_ON, 1)
        blink_off = round(preferences.RC_BLINK_OFF, 1)
        col_name = preferences.RC_MESHES
        self.buttonA_description = "Turns the visibility on/off for mesh(es) in collection '{0}'.\n" +\
                                   "Blinking frequency can be adjusted in the addon Preferences.\n" +\
                                   "Current settings are:  On ({1:.1f} sec), Off ({2:.1f} sec)"
        self.buttonA = BL_UI_Button(newX, newY, btnW, btnH)
        self.buttonA.style = 'TOOL'
        self.buttonA.text = "Blink Mesh(es)"
        self.buttonA.set_mouse_up(self.buttonA_click)
        self.buttonA.set_mouse_enter(self.buttonA_enter)
        self.buttonA.description = self.buttonA_description.format(col_name, blink_on, blink_off)
        self.buttonA.python_cmd = "bpy.ops.object.set_mesh_visibility()"
        self.buttonA.set_button_pressed(self.buttonA_pressed)
        if self.buttonA_pressed(self.buttonA): self.buttonA.state = 3
        newX = newX + btnW-1 + btnS
        # Lock Position: Locks Target Position fields and disables impacted buttons
        self.button8 = BL_UI_Button(newX, btnY, btnW, btnH)
        self.button8.style = 'TOGGLE'
        self.button8.text = "Lock Position"
        self.button8.set_mouse_up(self.button8_click)
        self.button8.set_button_pressed(self.button8_pressed)
        self.button8.description = "Locks Target Position properties and disables impacted buttons"        
        self.button8.python_cmd = "bpy.ops.object.ref_camera_panelbutton_lpos()"
        if self.button8_pressed(self.button8): self.button8.state = 3
        newY = btnY + btnH + btnS
        # Lock Rotation: Locks Target Rotation fields and disables impacted buttons
        self.button9 = BL_UI_Button(newX, newY, btnW, btnH)
        self.button9.style = 'TOGGLE'
        self.button9.text = "Lock Rotation"
        self.button9.set_mouse_up(self.button9_click)
        self.button9.set_button_pressed(self.button9_pressed)
        self.button9.description = "Locks Target Rotation properties and disables impacted buttons"        
        self.button9.python_cmd = "bpy.ops.object.ref_camera_panelbutton_lrot()"
        if self.button9_pressed(self.button9): self.button9.state = 3
        btnC = 0
        newX = newX + btnW-1 + btnS + marginX
        btnW = 22
        btnH = 20
        # Memory slots box
        self.slotbox = BL_UI_Patch((newX - btnS), (btnY - btnS), (btnW*3 + btnS*3), (btnH*2 + btnS*3))
        self.slotbox.style = 'BOX'
        self.slotbox.radius = 4
        # Memory switch first button
        self.memory1 = BL_UI_Button(newX, btnY, btnW, btnH)
        self.memory1.style = 'TOOL'
        self.memory1.text = "M1"
        self.memory1.set_mouse_up(self.memory1_click)
        self.memory1.set_timer_event(self.memory1_poll)
        self.memory1.description = "Switches the Camera+Target set configuration with memory slot 1"        
        self.memory1.python_cmd = "bpy.ops.object.ref_camera_panelbutton_m1()"
        newY = btnY + btnH + btnS
        # Memory save button
        self.memsave = BL_UI_Button(newX, newY, (btnW*2 + 2), btnH)
        self.memsave.style = 'TOOL'
        self.memsave.text = "MSave"
        self.memsave.set_mouse_up(self.memsave_click)
        self.memsave.set_timer_event(self.memsave_poll)
        self.memsave.description = "Saves the Camera+Target set configuration in the next available memory slot"        
        self.memsave.python_cmd = "bpy.ops.object.ref_camera_panelbutton_ms()"
        newX = newX + btnW + 2
        # Memory switch second button 
        self.memory2 = BL_UI_Button(newX, btnY, btnW, btnH)
        self.memory2.style = 'TOOL'
        self.memory2.text = "M2"
        self.memory2.set_mouse_up(self.memory2_click)
        self.memory2.set_timer_event(self.memory2_poll)
        self.memory2.description = "Switches the Camera+Target set configuration with memory slot 2"        
        self.memory2.python_cmd = "bpy.ops.object.ref_camera_panelbutton_m2()"
        newX = newX + btnW + 2
        # Memory switch third button
        self.memory3 = BL_UI_Button(newX, btnY, btnW, btnH)
        self.memory3.style = 'TOOL'
        self.memory3.text = "M3"
        self.memory3.set_mouse_up(self.memory3_click)
        self.memory3.set_timer_event(self.memory3_poll)
        self.memory3.description = "Switches the Camera+Target set configuration with memory slot 3"        
        self.memory3.python_cmd = "bpy.ops.object.ref_camera_panelbutton_m3()"
        newY = btnY + btnH + btnS
        # Memory clear button
        self.memtrim = BL_UI_Button(newX, newY, btnW, btnH)
        self.memtrim.style = 'TOOL'
        self.memtrim.text = "MC"
        self.memtrim.set_mouse_up(self.memtrim_click)
        self.memtrim.set_timer_event(self.memtrim_poll)
        self.memtrim.description = "Clears out all three memory slots"        
        self.memtrim.python_cmd = "bpy.ops.object.ref_camera_panelbutton_mc()"
        #-----------

        panW = newX+btnW+marginX+btnS  # Panel desired width  (beware: this math is good for my setup only)
        panH = newY+btnH+marginY       # Panel desired height (ditto)

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
        panY = panH + 40 - 1  # The '40' is just a spacing                         # Panel Y coordinate, for panel's top-left corner 

        self.panel = BL_UI_Drag_Panel(panX, panY, panW, panH) 
        self.panel.style = 'PANEL'         # Options are: {HEADER,PANEL,SUBPANEL,TOOLTIP,NONE}

        self.tooltip = BL_UI_Tooltip()     # This is for displaying the widgets tooltips. Only need one instance!

        #-----------
        if DEBUG:
            # Display an 'UNRegister' button on screen
            newX = marginX + panW
            newY = marginY + 1
            btnH = 40+btnS   
            self.buttonU = BL_UI_Button(newX, newY, btnH, btnH)
            self.buttonU.style = 'TOOL'
            self.buttonU.text = "UNR"
            self.buttonU.text_size = 12
            self.buttonU.bg_color = (0.5,0,0,1)
            self.buttonU.outline_color = (0.6,0.6,0.6,0.8)
            self.buttonU.corner_radius = panH/2 - 1
            self.buttonU.roundness = 1.0
            self.buttonU.set_mouse_up(self.buttonU_click)
            self.buttonU.description = "Unregisters the Remote Control panel object and closes it"        
            self.buttonU.python_cmd = "bpy.ops.object.set_remote_control()"

    def on_invoke(self, context, event):
        # Add your widgets here (TODO: perhaps a better, more automated solution?)
        # --------------------------------------------------------------------------------------------------
        widgets_panel = [
                         self.panel
                        ]
        widgets_items = [
                         self.button1, self.button2, self.button3, self.button4, self.button5, self.button6, 
                         self.button7, self.button8, self.button9, self.buttonA, self.buttonR, 
                         self.slotbox, self.memory1, self.memory2, self.memory3, self.memsave, self.memtrim, 
                         self.tooltip, # <-- If there is a tooltip object, it must be the last in this list
                        ]

        if DEBUG: widgets_items.append(self.buttonU)  #-- Added an 'Unregister' side button, for debugging.
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
        # ZOOM: Dolly moves only back and forth on camera's axis (G + ZZ + move mouse)
        # Good to adjust 'Distance/Size' 
        # Characteristics - Selected:Camera; Transformation:Local; Pivot:ActiveElement(=Camera)
        bpy.ops.object.ref_camera_panelbutton_zoom(mode='REMOTE')

    def button1_pressed(self, widget):
        return (bpy.context.scene.var.OpState1)

    def button2_click(self, widget, event, x, y):
        # Horizontal Orbit: The camera rotates around the target which stays in place (R + Z + move mouse)
        # Good to adjust 'Rotation'
        # Characteristics - Selected:Camera; Transformation:Global; Pivot:3DCursor (which is moved to 'Target' origin)
        bpy.ops.object.ref_camera_panelbutton_horb(mode='REMOTE')

    def button2_pressed(self, widget):
        return (bpy.context.scene.var.OpState2)

    def button3_click(self, widget, event, x, y):
        # Vertical Orbit: The camera rotates around the target which stays in place (R + XX + move mouse)
        # Good to adjust 'Elevation/Azimuth'
        # Characteristics - Selected:Camera; Transformation:Local; Pivot:3DCursor (which is moved to 'Target' origin)
        bpy.ops.object.ref_camera_panelbutton_vorb(mode='REMOTE')

    def button3_pressed(self, widget):
        return (bpy.context.scene.var.OpState3)

    def button4_click(self, widget, event, x, y):
        # TILT: Camera stays still, moves from up and down (R + YY + move mouse)
        # Good to adjust 'Inclination'
        # Characteristics - Selected:Target; Transformation:Local; Pivot:ActiveElement(=Target)
        bpy.ops.object.ref_camera_panelbutton_tilt(mode='REMOTE')

    def button4_pressed(self, widget):
        return (bpy.context.scene.var.OpState4)

    def button5_click(self, widget, event, x, y):
        # This one is same as button6 (not an error)
        # Translation: Truck/Pedestal moves only from left to right on camera's axis (G + X/Y/Z + move mouse)
        # Good to adjust 'Position'
        # Characteristics - Selected:Camera+Target; Transformation:Global; Pivot:ActiveElement(=Target)
        bpy.ops.object.ref_camera_panelbutton_move(mode='REMOTE')

    def button5_pressed(self, widget):
        return (bpy.context.scene.var.OpState5)

    def button6_click(self, widget, event, x, y):
        # This one is same as button5 (not an error)
        # Roll: Camera stays still, lean from left to right (R + X/Y + move mouse)
        # Good to adjust 'Angle'
        # Characteristics - Selected:Camera+Target; Transformation:Global; Pivot:ActiveElement(=Target)
        bpy.ops.object.ref_camera_panelbutton_roll(mode='REMOTE')

    def button6_pressed(self, widget):
        return (bpy.context.scene.var.OpState6)

    def button7_click(self, widget, event, x, y):
        # Perspective: combination of Camera's Translation with Elevation/Rotation (G + X/Y/Z + mouse move)
        # Good to adjust 'Point of View'
        # Characteristics - Selected:Camera; Transformation:Global; Pivot:ActiveElement(=Target)
        bpy.ops.object.ref_camera_panelbutton_pov(mode='REMOTE')

    def button7_pressed(self, widget):
        return (bpy.context.scene.var.OpState7)

    def button8_click(self, widget, event, x, y):
        # Lock Position: Locks Target Position properties and disables impacted buttons
        # Good to prevent accidental changes in target placement
        bpy.ops.object.ref_camera_panelbutton_lpos()
        self.button5.enabled = (not bpy.context.scene.var.OpState8)

    def button8_pressed(self, widget):
        return (bpy.context.scene.var.OpState8)

    def button9_click(self, widget, event, x, y):
        # Lock Rotation: Locks Target Rotation properties and disables impacted buttons
        # Good to prevent accidental changes in target placement
        bpy.ops.object.ref_camera_panelbutton_lrot()
        self.button4.enabled = (not bpy.context.scene.var.OpState9)
        self.button6.enabled = (not bpy.context.scene.var.OpState9)

    def button9_pressed(self, widget):
        return (bpy.context.scene.var.OpState9)

    def buttonA_click(self, widget, event, x, y):
        # Blink Mesh(es): Turns mesh visibility on/off
        # Good to precisely eyeball superposition of fine mesh details against the image background
        result = bpy.ops.object.ref_camera_panelbutton_flsh(mode='REMOTE')
        if result == {'CANCELLED'}:
            package = __package__[0:__package__.find(".")]
            collect = bpy.context.preferences.addons[package].preferences.RC_MESHES
            self.report(type={'ERROR'}, message="Collection '" + collect + "' not found or all meshes are hidden")

    def buttonA_enter(self, widget, event, x, y):
        package = __package__[0:__package__.find(".")]
        preferences = bpy.context.preferences.addons[package].preferences
        blink_on = round(preferences.RC_BLINK_ON, 1)
        blink_off = round(preferences.RC_BLINK_OFF, 1)
        col_name = preferences.RC_MESHES
        widget.description = self.buttonA_description.format(col_name, blink_on, blink_off)

    def buttonA_pressed(self, widget):
        return (bpy.context.scene.var.OpStateA)

    def buttonR_click(self, widget, event, x, y):
        # Reset Target: Sets Target Location and Rotation to (0,0,0) and removes related locks
        bpy.ops.object.ref_camera_panelbutton_rset()
        self.button4.enabled = True
        self.button5.enabled = True
        self.button6.enabled = True

    def buttonU_click(self, widget, event, x, y):
        self.finish()

    def memory1_click(self, widget, event, x, y):
        # Memory Switch 1: Switches the Camera+Target set configuration with memory slot 1"
        bpy.ops.object.ref_camera_panelbutton_m1()

    def memory1_poll(self, widget, event, x, y):
        widget.enabled = bpy.context.scene.var.OpStatM1
        return False
        
    def memory2_click(self, widget, event, x, y):
        # Memory Switch 2: Switches the Camera+Target set configuration with memory slot 2"
        bpy.ops.object.ref_camera_panelbutton_m2()
        
    def memory2_poll(self, widget, event, x, y):
        widget.enabled = bpy.context.scene.var.OpStatM2
        return False
        
    def memory3_click(self, widget, event, x, y):
        # Memory Switch 3: Switches the Camera+Target set configuration with memory slot 3"
        bpy.ops.object.ref_camera_panelbutton_m3()
        
    def memory3_poll(self, widget, event, x, y):
        widget.enabled = bpy.context.scene.var.OpStatM3
        return False
        
    def memsave_click(self, widget, event, x, y):
        # Memory Save: Saves the Camera+Target set configuration in the next available memory slot"
        bpy.ops.object.ref_camera_panelbutton_ms()
        
    def memsave_poll(self, widget, event, x, y):
        widget.enabled = (not bpy.context.scene.var.OpStatM3)
        return False
        
    def memtrim_click(self, widget, event, x, y):
        # Memory Clear: Clears out all three memory slots"
        bpy.ops.object.ref_camera_panelbutton_mc()
        
    def memtrim_poll(self, widget, event, x, y):
        widget.enabled = bpy.context.scene.var.OpStatM1
        return False
        

##-Register/unregister processes 
def register():
    bpy.utils.register_class(DP_OT_draw_operator)
 
def unregister():
    bpy.utils.unregister_class(DP_OT_draw_operator)           

if __name__ == '__main__':
    register()
    