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
    "author": "Jayanam (enhancements by Marcelo M. Marques)",
    "version": (0, 6, 5, 0),
    "blender": (2, 80, 3),
    "location": "View3D",
    "support": "COMMUNITY",
    "category": "3D View",
    "warning": ""
    }

import bpy
from bpy.props import StringProperty, BoolProperty

#--- ### Properties
class Variables(bpy.types.PropertyGroup):
    OpState1: bpy.props.BoolProperty(default=False)
    OpState2: bpy.props.BoolProperty(default=False)
    OpState3: bpy.props.BoolProperty(default=False)
    OpState4: bpy.props.BoolProperty(default=False)
    OpState5: bpy.props.BoolProperty(default=False)
    OpState6: bpy.props.BoolProperty(default=False)
    RemoVisible: bpy.props.BoolProperty(default=False)
    btnRemoText: bpy.props.StringProperty(default="Open Demo Panel")

def is_object_mode(context = None):
    """Returns True, when Blender is in the Object Mode
        Arguments:
            @context (Context):    current context (optional - as received by the operator)
    """
    if context:
        return context.mode == 'OBJECT'
    else:
        return bpy.context.mode == 'OBJECT'

class Set_Demo_Panel(bpy.types.Operator):
    ''' Opens/Closes the remote control demo panel '''
    bl_idname = "object.set_demo_panel" 
    bl_label = "Open Demo Panel"
    bl_description = "Turns the remote control demo panel on/off"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context))
        
    def invoke(self, context, event):
        #input validation: 
        return self.execute(context)
            
    def execute(self,context):
        if context.scene.var.RemoVisible == True:
            context.scene.var.btnRemoText = "Open Demo Panel"
        else:    
            context.scene.var.btnRemoText = "Close Demo Panel"
            context.scene.var.objRemote = bpy.ops.object.dp_ot_draw_operator('INVOKE_DEFAULT')

        context.scene.var.RemoVisible = not context.scene.var.RemoVisible 
        return {'FINISHED'}
        
class OBJECT_PT_Demo(bpy.types.Panel):
    bl_space_type = 'VIEW_3D' 
    bl_region_type = 'UI' 
    bl_category = "BL_UI_Widget"
    bl_label = "Current"
       
    @classmethod
    def poll(cls, context):
        #show this panel in Object Mode, only:
        return (context.mode == 'OBJECT')
   
    def draw(self, context):
        if context.space_data.type == 'VIEW_3D' and context.mode == 'OBJECT':
            #-- remote control switch button
            op = self.layout.operator(Set_Demo_Panel.bl_idname, text=context.scene.var.btnRemoText)
        return None


import bpy.app
from bpy.utils import unregister_class, register_class

#list of the classes in this add-on to be registered in Blender API:
classes = [ 
            Variables,
            Set_Demo_Panel,
            OBJECT_PT_Demo,
          ]  

def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.var = bpy.props.PointerProperty(type=Variables)

def unregister():
    del bpy.types.Scene.var
    for cls in reversed(classes):
        unregister_class(cls)  

if __name__ == '__main__':
    register()