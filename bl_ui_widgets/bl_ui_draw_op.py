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
#Added: 'terminate_execution' function that can be overriden by programmer in its subclass to command termination of the panel widget.
#Added: A call to a new 'handle_event_finalize' function in the widgets so that after finishing processing of all the widgets primary 'handle_event' 
#       function, a final pass is done one more time to wrap up any pending change of state for prior widgets already on the widgets list. Without 
#       this additional pass it was not possible to make widgets that keep a 'pressed' state in relation to others, to work alright.
#Added: New logic to finish execution of the widget whenever the user moves out of the 3D VIEW display mode (e.g. going into Sculpt editor).
#Added: New logic to only allow paint onto the screen if the user is in the 3D VIEW display mode.
#Added: New logic to detect when drawback handler gets lost (e.g. after opening other blender file) so that it can finish the operator without crashing.
#Chang: Disabled code that finished execution by pressing the ESC key, since the addon has control to finish it by a 'terminate_execution' function.
#Chang: Renamed some local variables so that those become restricted to this class only.

#--- ### Imports
import bpy

from bpy.types import Operator

class BL_UI_OT_draw_operator(Operator):
    bl_idname = "object.bl_ui_ot_draw_operator"
    bl_label = "bl ui widgets operator"
    bl_description = "Operator for bl ui widgets" 
    bl_options = {'REGISTER'}
    handlers = []
    
    def __init__(self):
        self.widgets = []
        #self.__draw_handle = None
        #self.__draw_events = None
        self.__finished = False

    @classmethod
    def validate(cls):
        """ A draw callback belonging to the space is persistent when another file is opened, whereas a modal operator is not. 
            Solution below removes the draw callback if the operator becomes invalid. The RNA is how Blender objects store their 
            properties under the hood. When the instance of the Blender operator is no longer required its RNA is trashed. 
            Using 'repr()' avoids using a try catch clause. Would be keen to find out if there is a nicer way to check for this.
        """
        invalids = [(type, op, context, handler) for type, op, context, handler in cls.handlers if repr(op).endswith("invalid>")]
        valid = not(invalids)
        while invalids:
            type, op, context, handler = invalids.pop()
            if type == 'H':
                bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
            if type == 'T':
                context.window_manager.event_timer_remove(handler)
            cls.handlers.remove((type, op, context, handler))
        return valid
    	
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
        BL_UI_OT_draw_operator.handlers = []
        BL_UI_OT_draw_operator.handlers.append(('H', self, context, bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')))
        BL_UI_OT_draw_operator.handlers.append(('T', self, context, context.window_manager.event_timer_add(0.1, window=context.window)))
        #Was as below before implementing the 'lost handler detection logic'
        #self.__draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, "WINDOW", "POST_PIXEL")
        #self.__draw_events = context.window_manager.event_timer_add(0.1, window=context.window)
        
    def unregister_handlers(self, context):
        for handler in BL_UI_OT_draw_operator.handlers:
            if handler[0] == 'H':
                bpy.types.SpaceView3D.draw_handler_remove(handler[3], 'WINDOW')
            if handler[0] == 'T':
                context.window_manager.event_timer_remove(handler[3])
        BL_UI_OT_draw_operator.handlers = []
        #Was as below before implementing the 'lost handler detection logic'
        #context.window_manager.event_timer_remove(self.__draw_events)
        #bpy.types.SpaceView3D.draw_handler_remove(self.__draw_handle, "WINDOW")
        #self.__draw_handle = None
        #self.__draw_events = None
        
    def modal(self, context, event):
        if self.__finished:
            return {'FINISHED'}

        ##-- personalized criteria for the Reference Cameras addon --
        # This is an ugly workaround till I figure out how to signal to the N-panel coding that this remote control panel has been finished.
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
                                
    def handle_widget_events(self, event):
        result = False
        for widget in self.widgets:
            if widget.visible or event.type == 'TIMER':
                if widget.handle_event(event):
                    result = True
                    break
        if event.type != 'TIMER':
            for widget in self.widgets:
                if widget.visible:
                    # Need to pass one more time to wrap up any pending change of state for widgets on the widgets list
                    widget.handle_event_finalize(event)
        return result
          
    def terminate_execution(self):
        # This may be overriden by one same named function on the child class
        return False
    
    def finish(self):
        ##-- personalized criteria for the Reference Cameras addon --
        # This is an ugly workaround till I figure out how to signal to the N-panel coding that this remote control panel has been finished.
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
        # check handles are still valid
        if not BL_UI_OT_draw_operator.validate():
            bpy.context.scene.var.RemoVisible = False
            bpy.context.scene.var.btnRemoText = "Open Remote Control"
            return        

        ##-- personalized criteria for the Reference Cameras addon --
        # This is an ugly workaround till I figure out how to signal to the N-panel coding that this remote control panel has been finished.
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
