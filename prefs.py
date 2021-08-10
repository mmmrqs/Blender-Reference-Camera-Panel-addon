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
    "name": "Reference Cameras",
    "description": "Handles cameras associated with a reference photo",
    "author": "Witold Jaworski (enhancements by Marcelo M. Marques)",
    "version": (2, 1, 0),
    "blender": (2, 80, 3),
    "location": "View3D > side panel ([N]), [Cameras] tab",
    "support": "COMMUNITY",
    "category": "3D View",
    "warning": "mmmrqs@gmail.com",
    "wiki_url": "http://airplanes3d.net/scripts-257_e.xml",
    "tracker_url": "http://airplanes3d.net/track-257_e.xml"
    }

#--- ### Change log

#v2.1.0 (08.01.2021) - by Marcelo M. Marques 
#Added: initial creation

#--- ### Imports
import bpy

from bpy.types import AddonPreferences, Operator
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty

class ReferenceCameraPreferences(AddonPreferences):
    bl_idname = __package__

    RC_MESHES: StringProperty(
        name="",
        description="Name (or suffix) for a collection where the work in progress mesh(es) should be placed\nso that the 'switch mesh visibility' feature can be used",
        default="RC:WIP"
    )
    
    RC_CAMERAS: StringProperty(
        name="",
        description="Name (or suffix) for a collection where to place your reference cameras",
        default="RC:Cameras"
    )
    
    RC_TARGETS: StringProperty(
        name="",
        description="<Optional> Name (or suffix) for a collection where the target objects will be moved upon creation of new camera sets. If left blank targets will be placed in the main camera collection",
        default="RC:Targets"
    )
    
    RC_TEMP: StringProperty(
        name="",
        description="Name (or suffix) for a 'working' collection for convenient view adjustments of the current camera",
        default="RC:Temporary"
    )
    
    RC_SUBPANELS: IntProperty(
        name="",
        description="Maximum number of dynamic subpanels for grouping camera selection buttons (when children collections exist under the main camera collection)",
        default=15,
        max=99,
        min=0,
        soft_max=32,
        soft_min=0
    )

    #(identifier, name, description, icon, number)
    RC_SUBP_MODE: EnumProperty(
        name="N-Panel Layout option",
        items=[
            ('COMPACT',  "Compact",  "Display the 5 main camera modes using large buttons.", '', 0),
            ('FULL',     "Full",     "Display all the 7 camera modes using narrow buttons.", '', 1),
            ('EXTENDED', "Extended", "Display all features likewise the 'Remote Control' panel.", '', 2)
        ],
        default='COMPACT'
    )

    RC_ACTION_MAIN: BoolProperty(
        name="Camera Action mode (N-Panel)",
        description="If (ON): camera action start when mode button is pressed.\nIf (OFF): just set the adjustment mode but do not start camera action",
        default=False
    )

    RC_FOCUS: FloatProperty(
        name="",
        description="Perspective Camera lens value in millimeters",
        default=50.0,
        min=1.0,
        soft_max=5000,
        soft_min=1.0,
        step=100,
        precision=2,
        unit='CAMERA',
        subtype='DISTANCE_CAMERA'
    )

    RC_SENSOR: FloatProperty(
        name="",
        description="Perspective Camera sensor width in millimeters",
        default=36.0,
        min=1.0,
        soft_max=100,
        soft_min=1.0,
        step=100,
        precision=2,
        unit='CAMERA'
    )

    #(identifier, name, description, icon, number)
    RC_TRGMODE: EnumProperty(
        name="",
        items=[
            ('TEXTURED', "Textured", "Display the camera's target object with textures", '', 0),
            ('SOLID',    "Solid",    "Display the camera's target object as a solid", '', 1),
            ('WIRE',     "Wire",     "Display the camera's target object as a wireframe", '', 2),
            ('BOUNDS',   "Bounds",   "Display the bounds of the camera's target object", '', 3)
        ],
        default='SOLID'
    )

    RC_TRGCOLOR: FloatVectorProperty(
        name="",
        description="Color and alpha for the camera target object",
        default=(1.0, 0.075, 0.0, 1.0),
        max=1.0, 
        min=0.0, 
        size=4,
        subtype='COLOR'
    )

    RC_OPACITY: FloatProperty(
        name="",
        description="Opacity level for the camera's backgroud image to blend against the viewport background color",
        default=0.5,
        max=1.0,
        min=0.0,
        soft_max=1.0,
        soft_min=0.0,
        step=1,
        precision=3,
        unit='NONE',
        subtype='FACTOR'
    )

    #(identifier, name, description, icon, number)
    RC_DEPTH: EnumProperty(
        name="Depth option for rendering the camera's backgroud image",
        items=[
            ('BACK',  "Back",  "Display under everything.", '', 0),
            ('FRONT', "Front", "Display over everything.", '', 1)
        ],
        default='FRONT'
    )

    RC_UI_BIND: BoolProperty(
        name="General scaling for 'Remote Control' panel",
        description="If (ON): remote panel size changes per Blender interface's resolution scale.\nIf (OFF): remote panel size can only change per its own addon scaling factor",
        default=True
    )

    RC_SCALE: FloatProperty(
        name="",
        description="Scaling to be applied on the 'Remote Control' panel over (in addition to) the interface's resolution scale",
        default=1.0,
        max=2.00,
        min=0.50,
        soft_max=2.00,
        soft_min=0.50,
        step=1,
        precision=2,
        unit='NONE'
    )

    RC_ACTION_REMO: BoolProperty(
        name="Camera Action mode (Remote Control panel)",
        description="If (ON): camera action start when mode button is pressed.\nIf (OFF): just set the adjustment mode but do not start camera action",
        default=True
    )

    RC_SLIDE: BoolProperty(
        name="Keep Remote Control panel pinned when resizing viewport",
        description="If (ON): remote panel slides together with viewport's bottom border.\nIf (OFF): remote panel stays in place regardless of viewport resizing",
        default=False
    )

    RC_POSITION: BoolProperty(
        name="Remote Control panel position per scene",
        description="If (ON): remote panel initial position is the same as in the last opened scene.\nIf (OFF): remote panel remembers its position per each scene",
        default=False
    )

    RC_POS_X: IntProperty(
        name="",
        description="Remote Control panel position X from latest opened scene",
        default=-10000
    )

    RC_POS_Y: IntProperty(
        name="",
        description="Remote Control panel position Y from latest opened scene",
        default=-10000
    )

    def ui_scale(self, value):
        if bpy.context.preferences.addons[__package__].preferences.RC_UI_BIND:
            # From Preferences/Interface/"Display"
            return int(round(value * bpy.context.preferences.view.ui_scale))
        else:
            return value
        
    def over_scale(self, value):
        over_scale = bpy.context.preferences.addons[__package__].preferences.RC_SCALE
        return int(round(self.ui_scale(value) * over_scale))
        
    def draw(self, context):
        layout = self.layout
        
        #-- N-Panel configuration

        layout.separator()
        layout.label(text=" N-Panel configuration")

        split = layout.split(factor=0.45, align=True)
        split.label(text="Meshes Collection name suffix:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        split.prop(self, 'RC_MESHES', text="")

        split = layout.split(factor=0.45, align=True)
        split.label(text="Cameras Collection name suffix:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        split.prop(self, "RC_CAMERAS", text="")

        split = layout.split(factor=0.45, align=True)
        split.label(text="Targets Collection name suffix:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        split.prop(self, "RC_TARGETS", text="")

        split = layout.split(factor=0.45, align=True)
        split.label(text="Temporary Collection name suffix:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        split.prop(self, "RC_TEMP", text="")
        
        split = layout.split(factor=0.45, align=True)
        split.label(text="Subpanels max number:",icon='DECORATE')
        split = split.split(factor=0.4, align=True)
        split.prop(self, "RC_SUBPANELS", text="")

        split = layout.split(factor=0.45, align=True)
        split.label(text="N-Panel layout option:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        row = split.row()
        row.prop(self, "RC_SUBP_MODE", expand=True)

        split = layout.split(factor=0.45, align=True)
        split.label(text="N-Panel action mode:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        split.prop(self, "RC_ACTION_MAIN", text=" Start action immediately")
        
        #-- Defaults for creating new camera/target sets

        layout.separator()
        layout.label(text=" Defaults for creating new camera/target sets")

        split = layout.split(factor=0.45, align=True)
        split.label(text="Perspective Camera focal lenght:",icon='DECORATE')
        split = split.split(factor=0.4, align=True)
        split.prop(self, "RC_FOCUS", expand=True)
        
        split = layout.split(factor=0.45, align=True)
        split.label(text="Perspective Camera sensor width:",icon='DECORATE')
        split = split.split(factor=0.4, align=True)
        split.prop(self, "RC_SENSOR", expand=True)
        
        split = layout.split(factor=0.45, align=True)
        split.label(text="Target Object display mode:",icon='DECORATE')
        split = split.split(factor=0.4, align=True)
        split.prop(self, "RC_TRGMODE", text="", expand=False)
        
        split = layout.split(factor=0.45, align=True)
        split.label(text="Target Object display color:",icon='DECORATE')
        split = split.split(factor=0.4, align=True)
        split.prop(self, "RC_TRGCOLOR", text="")
        
        split = layout.split(factor=0.45, align=True)
        split.label(text="Background Image opacity level:",icon='DECORATE')
        split = split.split(factor=0.4, align=True)
        split.prop(self, "RC_OPACITY", text="")
        
        split = layout.split(factor=0.45, align=True)
        split.label(text="Background Image depth option:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        row = split.row()
        row.prop(self, "RC_DEPTH", expand=True)
        
        #-- Remote Control Panel configuration

        layout.separator()
        layout.label(text=" Remote Control Panel configuration")

        split = layout.split(factor=0.45, align=True)
        split.label(text="General scaling for panel:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        split.prop(self, "RC_UI_BIND", text=" Bound to Blender's UI")

        split = layout.split(factor=0.45, align=True)
        split.label(text="User defined addon scaling:",icon='DECORATE')
        split = split.split(factor=0.4, align=True)
        split.prop(self, "RC_SCALE", text="")
        
        split = layout.split(factor=0.45, align=True)
        split.label(text="Panel action mode:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        split.prop(self, "RC_ACTION_REMO", text=" Start action immediately")

        split = layout.split(factor=0.45, align=True)
        split.label(text="Panel sliding option:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        split.prop(self, "RC_SLIDE", text=" Move along viewport border")

        split = layout.split(factor=0.45, align=True)
        split.label(text="Opening screen position:",icon='DECORATE')
        split = split.split(factor=0.8, align=True)
        split.prop(self, "RC_POSITION", text=" Same as in the last opened scene")

        if bpy.context.scene.get("bl_ui_panel_saved_data") is None:
            coords = "x: 0    " +\
                     "y: 0    "
        else:
            panH = 64 # <-- Panel height copied from 'drag_panel_op.py'
            pos_x = int(round(bpy.context.scene.get("bl_ui_panel_saved_data")["panX"]))
            pos_y = int(round(bpy.context.scene.get("bl_ui_panel_saved_data")["panY"]))
            # Note: Because of the scaling logic it was necessary to make this weird correction math below
            coords = "x: " + str(pos_x) + "    " +\
                     "y: " + str(pos_y + int(panH * (self.over_scale(1) - 1))) + "    "
        
        split = layout.split(factor=0.45, align=True)
        split.label(text="Current screen position:",icon='DECORATE')
        split = split.split(factor=0.4, align=True)
        split.label(text=coords)
        split = split.split(factor=0.65, align=True)
        split.operator(Reset_Coords.bl_idname)
        
        layout.separator()
        box = layout.box()
        row = box.row(align=True)
        box.scale_y = 0.5
        box.label(text="Additional information and Acknowledge:")
        box.label(text="This addon prepared and packaged by Marcelo M Marques (mmmrqs@gmail.com)")
        box.label(text="-(upgrades at https://github.com/mmmrqs/Blender-Reference-Camera-Panel-addon)")
        box.label(text="Object Reference Cameras original project by Witold Jaworski (wjaworski@airplanes3d.net)")
        box.label(text="-(download it from http://airplanes3d.net/scripts-257_e.xml)")
        box.label(text="BL UI Widgets original project by Jayanam (jayanam.games@gmail.com)")
        box.label(text="-(download it from https://github.com/jayanam/bl_ui_widgets)")
        box.label(text="Special thanks to: @batFINGER, Shane Ambler (sambler), vananders, and many others,")
        box.label(text="for their posts on the community forums which were crucial for making this addon.")

class Reset_Coords(bpy.types.Operator):
    bl_idname = "object.reset_coords" 
    bl_label = "Reset Pos"
    bl_description = "Resets the 'Remote Control' panel screen position for this current session only.\n"\
                     "Use this button to recover the panel if it has got stuck out of the viewport area.\n"\
                     "You will need to reopen the panel for the new screen position to take effect"
    @classmethod
    def poll(cls,context):
        return (not bpy.context.scene.get("bl_ui_panel_saved_data") is None)
    
    def invoke(self, context, event):
        return self.execute(context)
        
    def execute(self,context):
        # These numbers copied from 'drag_panel_op.py':
        panW = 631             # Panel width
        panH = 64              # Panel height
        panX = 100             # Panel X coordinate, for top-left corner
        panY = panH + 40 - 1   # Panel Y coordinate, for top-left corner 
        
        for area in bpy.data.screens['Layout'].areas:
            if area.type == 'VIEW_3D':
                if bpy.context.preferences.addons[__package__].preferences.RC_UI_BIND:
                    # From Preferences/Interface/"Display"
                    ui_scale = bpy.context.preferences.view.ui_scale  
                else:
                    ui_scale = 1
                over_scale = bpy.context.preferences.addons[__package__].preferences.RC_SCALE
                # Need this just because I want the panel to be centered
                panX = int((area.width - panW*ui_scale*over_scale) / 2.0) + 1
                break
        try:
            bpy.context.preferences.addons[__package__].preferences.RC_POS_X = panX
            bpy.context.preferences.addons[__package__].preferences.RC_POS_Y = panY
            bpy.context.scene.get("bl_ui_panel_saved_data")["panX"] = panX
            bpy.context.scene.get("bl_ui_panel_saved_data")["panY"] = panY
            bpy.context.scene.var.RemoVisible = False
            bpy.context.scene.var.btnRemoText = "Open Remote Control"
        except: pass
        return {'FINISHED'}

# Registration
def register():
    bpy.utils.register_class(Reset_Coords)
    bpy.utils.register_class(ReferenceCameraPreferences)

def unregister():
    bpy.utils.unregister_class(ReferenceCameraPreferences)
    bpy.utils.unregister_class(Reset_Coords)
     
if __name__ == '__main__':
    register()