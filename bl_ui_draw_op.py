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
#Added: 'terminate_execution' function that can be overriden by programmer in a child class to command termination of the panel widget.
#Added: A call to a new 'handle_event_finalize' function in the widgets so that after finishing processing of all the widgets primary 'handle_event' 
#       function, a final pass is done one more time to wrap up any pending change of state for prior buttons already on the widgets list. Without 
#       this additional pass it was not possible to make buttons that keep a 'pressed' state to work alright.
#Added: Custom logic to finish execution of the widget whenever the user moves out of the 3D VIEW display mode (example: going into Sculpt editor).
#Added: Custom logic to only allow paint onto the screen if the user is in the 3D VIEW display mode.
#Chang: Disabled code to finish execution by pressing the ESC key, since the addon has control to finish it by a 'terminate_execution' function.
#Chang: Renamed some local variables so that those become restricted to this class only.

#--- ### Imports
import bpy

from bpy.types import Operator

class BL_UI_OT_draw_operator(Operator):
    bl_idname = "object.bl_ui_ot_draw_operator"
    bl_label = "bl ui widgets operator"
    bl_description = "Operator for bl ui widgets" 
    bl_options = {'REGISTER'}
    	
    def __init__(self):
    
        self.widgets = []

        self.__draw_handle = None
        self.__draw_events = None
        self.__finished = False

    def init_widgets(self, context, widgets):
        self.widgets = widgets
        for widget in self.widgets:
            widget.init(context)

    def on_invoke(self, context, event):
        pass

    def on_finish(self, context):
        self.__finished = True

    def invoke(self, context, event):

        self.on_invoke(context, event)

        args = (self, context)
                   
        self.register_handlers(args, context)
                   
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def register_handlers(self, args, context):
        self.__draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, "WINDOW", "POST_PIXEL")
        self.__draw_events = context.window_manager.event_timer_add(0.1, window=context.window)
        
    def unregister_handlers(self, context):
        
        context.window_manager.event_timer_remove(self.__draw_events)
        
        bpy.types.SpaceView3D.draw_handler_remove(self.__draw_handle, "WINDOW")
        
        self.__draw_handle = None
        self.__draw_events = None
        
    def handle_widget_events(self, event):
        result = False
        for widget in self.widgets:
            if widget.handle_event(event):
                result = True
        for widget in self.widgets:
            # Need to repass one more time to wrap up any pending change of state for prior buttons already on the widgets list
            widget.handle_event_finalize(event)
        return result
          
    def terminate_execution(self):
        # This can be overriden by same named function on child class
        return False
    
    def modal(self, context, event):
        if self.__finished:
            return {'FINISHED'}

        ##-- personalized criteria for the Reference Cameras addon --
        # This is an ugly workaround till I figure out how to signal to main panel that remote control panel has been finished.
        # This is to detect when user changed workspace
        try: testing = context.space_data.type
        except: self.finish()

        try:
            if not (context.space_data.type == 'VIEW_3D'):
                self.finish()
            if self.terminate_execution():
                self.finish()
        except:
            pass
        ##-- end of the personalized criteria for the given addon --

        if context.area:
            context.area.tag_redraw()
        
        if self.handle_widget_events(event):
            return {'RUNNING_MODAL'}   
        
        # Not using this escape option but left here for documentation purpose
        # if event.type in {"ESC"}:
            # self.finish()
                    
        return {'PASS_THROUGH'}
                                
    def finish(self):
        ##-- personalized criteria for the Reference Cameras addon --
        # This is an ugly workaround till I figure out how to signal to main panel that remote control panel has been finished.
        # This is to detect when user changed workspace
        try: testing = context.space_data.type  
        except:    
            bpy.context.scene.var.RemoVisible = False
            bpy.context.scene.var.btnRemoText = "Open Remote Control"
        ##-- end of the personalized criteria for the given addon --
            
        self.unregister_handlers(bpy.context)
        self.on_finish(bpy.context)
		
	# Draw handler to paint onto the screen
    def draw_callback_px(self, op, context):
        ##-- personalized criteria for the Reference Cameras addon --
        # This is an ugly workaround till I figure out how to signal to main panel that remote control panel has been finished.
        # This is to detect when user changed workspace
        try: testing = context.space_data.type  
        except: self.finish()
        ##-- end of the personalized criteria for the given addon --

        success = False
        try:
            if context.space_data.type == 'VIEW_3D' and context.mode == 'OBJECT':
                if context.region_data.view_perspective == 'CAMERA':
                    success = True
        except:
            pass
            
        if success:
            for widget in self.widgets:
                widget.draw()                