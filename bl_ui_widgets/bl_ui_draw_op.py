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
           "version": (1, 0, 2),
           "blender": (2, 80, 75),
           "location": "View3D > viewport area",
           "support": "COMMUNITY",
           "category": "3D View",
           "warning": "Version numbering diverges from Jayanam's original project",
           "doc_url": "https://github.com/mmmrqs/bl_ui_widgets",
           "tracker_url": "https://github.com/mmmrqs/bl_ui_widgets/issues"
           }

# --- ### Change log

# v1.0.2 (09.30.2021) - by Marcelo M. Marques
# Added: 'region_pointer' class level property to indicate the region in which the drag_panel operator instance has been invoked().
# Added: 'valid_modes' property to indicate the 'bpy.context.mode' valid values for displaying the panel.
# Added: 'get_region_pointer' function to retrieve the value of the 'region_pointer' class level property.
# Added: 'get_3d_area_and_region' function to retrieve the correct area and region (because those are not guaranteed to remain
#         the same after maximizing/restoring screen areas).
# Added: 'valid_display_mode' function to determine whether the user has moved out of the valid area/region.
# Added: 'suppress_rendering' function that can be overriden by programmer in the subclass to control render bypass of the panel widget.
# Added: Logic to the 'invoke' method to avoid "internal error" terminal messages, after maximizing the viewport.
# Chang: How we determine whether the user has moved out of the valid area/region, now using the 'valid_display_mode()' function.
# Chang: Renamed function 'validate()' to 'valid_handler()' for better understanding of its purpose.

# v1.0.1 (09.20.2021) - by Marcelo M. Marques
# Chang: just some pep8 code formatting

# v1.0.0 (09.01.2021) - by Marcelo M. Marques
# Added: 'terminate_execution' function that can be overriden by programmer in the subclass to control termination of the panel widget.
# Added: A call to a new 'handle_event_finalize' function in the widgets so that after finishing processing of all the widgets primary 'handle_event'
#        function, a final pass is done one more time to wrap up any pending change of state for prior widgets already on the widgets list. Without
#        this additional pass it was not possible to make widgets that keep a 'pressed' state in relation to others, to work alright.
# Added: New logic to finish execution of the widget whenever the user moves out of the 3D VIEW display mode (e.g. going into Sculpt editor).
# Added: New logic to only allow paint onto the screen if the user is in the 3D VIEW display mode.
# Added: New logic to detect when drawback handler gets lost (e.g. after opening other blender file) so that it can finish the operator without crashing.
# Chang: Disabled code that finished execution by pressing the ESC key, since the addon has control to finish it by a 'terminate_execution' function.
# Chang: Renamed some local variables so that those become restricted to this class only.

# --- ### Imports
import bpy
import sys

from bpy.types import Operator


class BL_UI_OT_draw_operator(Operator):
    bl_idname = "object.bl_ui_ot_draw_operator"
    bl_label = "bl ui widgets operator"
    bl_description = "Operator for bl ui widgets"
    bl_options = {'REGISTER'}

    handlers = []
    region_pointer = 0  # Uniquely identifies the region that this (drag_panel) operator instance has been invoked()

    def __init__(self):
        self.widgets = []
        self.valid_modes = []
        # self.__draw_handle = None  # <-- Was like this before implementing the 'lost handler detection logic'
        # self.__draw_events = None  #     (ditto)
        self.__finished = False
        self.__informed = False

    @classmethod
    def valid_handler(cls):
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

    def get_region_pointer(self):
        return BL_UI_OT_draw_operator.region_pointer

    def init_widgets(self, context, widgets, valid_modes):
        self.widgets = widgets
        for widget in self.widgets:
            widget.init(context, valid_modes)

    def on_invoke(self, context, event):
        pass

    def on_finish(self, context):
        self.__finished = True

    def invoke(self, context, event):
        # Avoid "internal error: modal gizmo-map handler has invalid area" terminal messages, after maximizing the viewport,
        # by switching the workspace back and forth. Not pretty, but at least it avoids the terminal output getting spammed.
        current = context.workspace
        other = [ws for ws in bpy.data.workspaces if ws != current]
        if other:
            bpy.context.window.workspace = other[0]
            bpy.context.window.workspace = current
        # -----------------------------------------------------------------
        BL_UI_OT_draw_operator.region_pointer = context.region.as_pointer()
        # -----------------------------------------------------------------
        self.on_invoke(context, event)
        args = (self, context)
        self.register_handlers(args, context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def register_handlers(self, args, context):
        BL_UI_OT_draw_operator.handlers = []
        BL_UI_OT_draw_operator.handlers.append(('H', self, context, bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')))
        BL_UI_OT_draw_operator.handlers.append(('T', self, context, context.window_manager.event_timer_add(0.1, window=context.window)))
        # Was as below before implementing the 'lost handler detection logic'
        # self.__draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, "WINDOW", "POST_PIXEL")
        # self.__draw_events = context.window_manager.event_timer_add(0.1, window=context.window)

    def unregister_handlers(self, context):
        for handler in BL_UI_OT_draw_operator.handlers:
            if handler[0] == 'H':
                bpy.types.SpaceView3D.draw_handler_remove(handler[3], 'WINDOW')
            if handler[0] == 'T':
                context.window_manager.event_timer_remove(handler[3])
        BL_UI_OT_draw_operator.handlers = []
        # Was as below before implementing the 'lost handler detection logic'
        # context.window_manager.event_timer_remove(self.__draw_events)
        # bpy.types.SpaceView3D.draw_handler_remove(self.__draw_handle, "WINDOW")
        # self.__draw_handle = None
        # self.__draw_events = None

    def modal(self, context, event):
        if self.__finished:
            return {'FINISHED'}

        area, region, abend = get_3d_area_and_region()

        if abend:
            self.finish()
        if self.terminate_execution(area, region):
            self.finish()
        if area:
            area.tag_redraw()
            if self.handle_widget_events(event):
                return {'RUNNING_MODAL'}

        # Not using this escape option, but left it here for documentation purpose
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

    def suppress_rendering(self, area, region):
        # This might be overriden by one same named function in the derived (child) class
        return False

    def terminate_execution(self, area, region):
        # This might be overriden by one same named function in the derived (child) class
        return False

    def finish(self):
        # -- personalized criteria for the Remote Control panel addon --
        # This is a temporary workaround till I figure out how to signal to
        # the N-panel coding that the remote control panel has been finished.
        bpy.context.scene.var.RemoVisible = False
        bpy.context.scene.var.btnRemoText = "Open Remote Control"
        # -- end of the personalized criteria for the given addon --

        self.unregister_handlers(bpy.context)
        self.on_finish(bpy.context)

    # Draw handler to paint onto the screen
    def draw_callback_px(self, op, context):
        # Check whether handles are still valid
        if not BL_UI_OT_draw_operator.valid_handler():
            # -- personalized criteria for the Remote Control panel addon --
            # This is a temporary workaround till I figure out how to signal to
            # the N-panel coding that the remote control panel has been finished.
            bpy.context.scene.var.RemoVisible = False
            bpy.context.scene.var.btnRemoText = "Open Remote Control"
            # -- end of the personalized criteria for the given addon --
            return

        # This is to detect when user moved into an undesired 'bpy.context.mode'
        # and it will check also the programmer's defined suppress_rendering function
        if valid_display_mode(self.valid_modes, self.suppress_rendering):
            for widget in self.widgets:
                widget.draw()


# --- ### Helper functions

def get_3d_area_and_region(prefs=None):
    abend = False
    try:
        # Left this commented code for a while until I make sure it will not be needed.
        # Case we want to put this back, it will need to import parameter 'idx', and in
        # the calling module the 'idx' value must be set as follows:
        #    ---------------------------------------------------------------------
        #    idx = bpy.context.window_manager.windows[:].index(bpy.context.window)
        #    ---------------------------------------------------------------------
        #
        # if bpy.app.version >= (2, 90, 0):
        #     areas = bpy.context.window.screen.areas
        # else:
        #     areas = bpy.context.window_manager.windows[idx].screen.areas
        #
        # if prefs:
        #     location = bpy.data.screens['Layout'].areas
        # else:
        #     location = bpy.context.window.screen.areas
        # for area in location:
        #     if area.type == 'VIEW_3D':
        #         for region in area.regions:
        #             if region.type == 'WINDOW':
        #                 if region.as_pointer() == BL_UI_OT_draw_operator.region_pointer:
        #                     return (area, region, abend)

        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            if region.as_pointer() == BL_UI_OT_draw_operator.region_pointer:
                                return (area, region, abend)
    except Exception as e:
        if __package__.find(".") != -1:
            package = __package__[0:__package__.find(".")]
        else:
            package = __package__
        print("**WARNING** " + package + " addon issue:")
        print("  +--> unexpected result in 'get_3d_area_and_region' function of bl_ui_draw_op.py module!")
        print("       " + e)
        abend = True
    return (None, None, abend)


def valid_display_mode(valid_modes, suppress_rendering=None):
    if valid_modes:
        if bpy.context.mode not in valid_modes:
            return False

    area, region, abend = get_3d_area_and_region()
    if abend:
        return False
    else:
        if suppress_rendering is not None:
            # Consider not a valid display mode when the overridable custom function
            # returns True (meaning that it wants to suppress the rendering at all).
            if suppress_rendering(area, region):
                return False
    return True
