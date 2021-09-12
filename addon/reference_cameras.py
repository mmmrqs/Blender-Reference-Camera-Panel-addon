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
    "description": "Handles cameras associated with reference photos",
    "author": "Marcelo M. Marques (fork of Witold Jaworski's project)",
    "version": (1, 0, 1),
    "blender": (2, 80, 75),
    "location": "View3D > side panel ([N]), [Cameras] tab",
    "support": "COMMUNITY",
    "category": "3D View",
    "warning": "Version numbering diverges from Witold's original project",
    "doc_url": "http://airplanes3d.net/scripts-257_e.xml",
    "tracker_url": "https://github.com/mmmrqs/Blender-Reference-Camera-Panel-addon/issues"
    }

#--- ### Change log

#v1.0.1 (09.12.2021) - by Marcelo M. Marques 
#Fixed: Saved the current camera state to prevent impact by the depsgraph_update_post's after_update() function
#v1.0.0 (09.01.2021) - by Marcelo M. Marques 
#Added: Addon preferences with properties to customize most of the panel's features.
#Added: Group of buttons to set the transformation orientation and select the camera/target.
#Added: Button to blink the active meshe(s) by continuously turning visibility on or off.
#Added: Button to open/close a floating 'Remote Control' panel.
#Added: Buttons to lock position and rotation of target object.
#Added: Buttons to save/recover camera+target set setups.
#Added: Buttons to remove (hide) cameras from the N-Panel groups.
#Added: Buttons to add to the scene new camera/target set auto configured to work with this addon.
#Added: Function to add to the scene the set of collections needed to work with this addon.
#Added: Logic to allow the many reference cameras to be automatically organized in distinct groups.
#Chang: Replaced constants by functions that retrieve the values from the addon preferences.

#--- ### Imports
import functools
import math
import bpy
import os

from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper

#from . drag_panel_op import DP_OT_draw_operator  <-- not needed anymore but left as example

#--- ### Diagnostic flag 
DEBUG = 0 # Set it to 0 in the production version; 1 to see diagnostic messages; 2 to enable PyDev debugger

#--- ### For direct debugging of this add-on (update the pydevd path!) ---------------------------
if DEBUG >= 2:
    import sys
    pydev_path = 'C:/Users/me/.p2/pool/plugins/org.python.pydev.core_7.2.1.201904261721/pysrc'
    if sys.path.count(pydev_path) < 1: sys.path.append(pydev_path)
    import pydevd
    pydevd.settrace(stdoutToServer=True, stderrToServer=True, suspend=False) #stop at first breakpoint
    #Beware: remove all breakpoints from other PyDev projects opened in Eclipse IDE


#--- ###  "Preferences Properties acting as Proxy-Constants"
def RC_MESHES():
    """ Name of a collection where the "work in progress" meshes should be placed so as the switch-mesh-visibility feature can be used """ 
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_MESHES)

def RC_CAMERAS():
    """ Place your reference cameras in a collection that ends with this suffix (for example: "5.9.A RC:Cameras", or "Special - RC:Cameras", or similar) """ 
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_CAMERAS)

def RC_TARGETS():
    """ Name for a collection where the target objects will be moved upon creation of new camera sets. 
        If left blank targets will be placed in the main camera collection.
    """     
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_TARGETS)

def RC_TEMP():
    """ A "working" collection for convenient view adjustments of the current camera. (this is also the collection name suffix). 
        The script creates such a collection if it does not exists. Then it will automatically place there the links 
        to the current camera and its target object. (Eventually previous contents will be unlinked). 
    """     
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_TEMP)
 
def RC_SUBPANELS():
    """ Maximum number of dynamic subpanels for grouping camera selection buttons (when children collections exist under the main camera collection) """ 
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_SUBPANELS)

def RC_SUBP_MODE():
    """ N-Panel Layout option: {COMPACT, FULL, EXTENDED}
        {COMPACT}: Only 5 main modes with large buttons / {FULL}: All 7 modes but narrow buttons / {EXTENDED}: All features from Remote Control panel
    """     
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_SUBP_MODE)

def RC_ACTION_MAIN():
    """ Camera Action mode. If (ON) camera action will start when mode button pressed; 
        If (OFF) just set the adjustment mode but do not start camera action.
    """
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_ACTION_MAIN)

def RC_FOCUS():
    """ Perspective Camera lens value in millimeters """
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_FOCUS)

def RC_SENSOR():
    """ Size of the image sensor area in millimeters """
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_SENSOR)

def RC_TRGMODE():
    """ Target Objects Display mode: {TEXTURED, SOLID, WIRE, BOUNDS} """ 
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_TRGMODE)

def RC_TRGCOLOR():
    """ Color and alpha for the camera target object """
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_TRGCOLOR)

def RC_OPACITY():
    """ Opacity level for the camera background image to blend against the viewport background color """
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_OPACITY)

def RC_DEPTH():
    """ Depth option for rendering the camera's background image """
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_DEPTH)

def RC_BLINK_ON():
    """ Time duration for the 'ON' stage of the blinking mesh cycle, in units of 1/10th of a second """
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_BLINK_ON)

def RC_BLINK_OFF():
    """ Time duration for the 'OFF' stage of the blinking mesh cycle, in units of 1/10th of a second """
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_BLINK_OFF)

def RC_ACTION_REMO():
    """ Camera Action mode. If (ON) camera action will start when mode button pressed; 
        If (OFF) just set the adjustment mode but do not start camera action.
    """
    package = __package__[0:__package__.find(".")]
    return (bpy.context.preferences.addons[package].preferences.RC_ACTION_REMO)

#--- ### Helper functions
def get_active_object(context = None):
    """ Returns current active object
        Arguments:
            @context (Context): current context (optional - bpy.context is used by default)
    """
    if not context: 
        context = bpy.context
    return context.object

def set_active_object(obj):
    """ Sets the current active object - program must be in Object Mode!
        Arguments:
            @obj (Object):    new active object
    """
    bpy.context.view_layer.objects.active = obj

def get_current_mode(context = None):
    """Returns current mode of the 3D View:
        Arguments:
            @context (Context):    current context (optional - as received by the operator)
    """
    if context:
        return context.mode
    else:
        return bpy.context.mode
    
def set_current_mode(new_mode):
    """Sets current mode of the 3D View:
        Arguments:
            @new_mode (string):    one of the modes received from the get_currentmode() function 
    """
    if new_mode == 'EDIT_MESH': 
        new_mode = 'EDIT'
    bpy.ops.object.mode_set(mode = new_mode)

def set_edit_mode():
    """Switches Blender into Edit Mode
    """
    set_current_mode('EDIT')
    
def is_edit_mode(context = None):
    """Returns True, when Blender is in Edit Mode
        Arguments:
            @context (Context):    current context (optional - as received by the operator)
    """
    if context:
        return context.mode == 'EDIT_MESH'
    else:
        return bpy.context.mode == 'EDIT_MESH'
            
def set_object_mode():
    """Switches Blender into Object Mode
    """
    set_current_mode('OBJECT')
    
def is_object_mode(context = None):
    """Returns True, when Blender is in the Object Mode
        Arguments:
            @context (Context):    current context (optional - as received by the operator)
    """
    if context:
        return context.mode == 'OBJECT'
    else:
        return bpy.context.mode == 'OBJECT'

def get_object(name, default, context = None):
    """ Returns object, corresponding to the given name
        Arguments:
            @name (string):     object name (may be empty)
            @default (Object):  object to use when the @name is not found
            @context (Context): current context (optional - bpy.context is used by default)
    """ 
    if not context:
        context = bpy.context
    obj = context.scene.objects.get(name, None)
    if obj:
        return obj
    else:
        return default

def find_collection(base, name_suffix):
    """ Returns first collection which name ends with given expression, or None
        Arguments:
            @base (Collection):     the root collection
            @name_suffix (String):  the name suffix we are searching for (case sensitive!)
    """ 
    if not base: return None
    if base.name.endswith(name_suffix):
        return base
    else:
        result = None
        for col in base.children:
            result = find_collection(col, name_suffix)
            if result: break
        return result #it can be None
       
def get_image(camera):
    """ Returns first image associated with this camera, or None
        Arguments:
            @camera (Object):     a camera object
    """ 
    if camera.data.background_images:
        return camera.data.background_images[0].image
    else:
        return None

def get_target(camera):
    """ Returns the camera target object, or None
        Arguments:
            @camera (Object):     a camera object
    """ 
    if camera.constraints:
        constr = camera.constraints[0]
        if constr.type == 'TRACK_TO' and constr.influence > 0.99: #It should be == 1.0, but I want to avoid numerical errors
            return constr.target
        else:
            return None
    else:
        return None

def get_camera_names(cntx):
    """ Returns the list of the names of reference camera objects found in given context (scene)
        Arguments:
            @cntx (Context):     a Blender context
        Remarks:
        It searches for the first collection which name ends with RC_CAMERAS suffix.
        If tere is no such a collection in this scene - returns None.
        If it finds it - returns the list of the camera objects from this collection that have both:
            1. background image
            2. active TrackTo constraint
        If there are no such objects, it returns an empty list ([]) 
    """ 
    rc = find_collection(cntx.scene.collection, RC_CAMERAS())
    if rc:
        result = []
        for obj in rc.objects:
            if obj.type == 'CAMERA' and obj.hide_select == False:
                if get_image(obj):
                    if get_target(obj):
                        result.append([rc.name,obj.name]) 
        #looking up for children collections
        children = False
        for rch in rc.children:
            for obj in rch.objects:
                if obj.type == 'CAMERA':
                    if get_image(obj):
                        if get_target(obj):
                            children = True
                            if obj.hide_select == False and obj.users_collection[0].hide_select == False:
                                result.append([rch.name,obj.name]) 
        if not children:
            for id in result:
                id[0] = ''  #clear the Group name element to prevent drawing any groups at all      
        return result
    else:
        return None
    
def wrap_text(width, text):
    """ Returns the list that contains the subsequent fragments of the text, none of them longer than <width> characters
        (Useful for displaying long-text descriptions in panels)
        Arguments:
            @width (int):     maximum number of characters per line
            @text  (String):  text to be split
    """     
    lines = []
    arr = text.split()
    lengthSum = 0
    strSum = ""
    
    for var in arr:
        lengthSum+=len(var) + 1
        if lengthSum <= width:
            strSum += " " + var
        else:
            lines.append(strSum)
            lengthSum = len(var)
            strSum = var

    lines.append(" " + strSum)
    return lines
   
def view_is_camera():
    screen = bpy.context.window.screen
    for area in screen.areas:
       if area.type == 'VIEW_3D':
           for region in area.regions:
               if region.type == 'WINDOW':
                   region3d = area.spaces[0].region_3d
                   if region3d.view_perspective == 'CAMERA':
                       return True
    return False
   
def unlink_all_objects(col):
    """ Removes (unlinks) all objects from given collection
        Arguments:
            @col (Collection):     a collection
    """ 
    for obj in col.objects:
        col.objects.unlink(obj)
        
        
#--- ### Core operations

    
#--- ### Properties
class Variables(bpy.types.PropertyGroup):
    OpState1: BoolProperty(default=False)
    OpState2: BoolProperty(default=False)
    OpState3: BoolProperty(default=False)
    OpState4: BoolProperty(default=False)
    OpState5: BoolProperty(default=False)
    OpState6: BoolProperty(default=False)
    OpState7: BoolProperty(default=False)
    OpState8: BoolProperty(default=False)
    OpState9: BoolProperty(default=False)
    OpStateA: BoolProperty(default=False)
    OpStatM1: BoolProperty(default=False)
    OpStatM2: BoolProperty(default=False)
    OpStatM3: BoolProperty(default=False)
    MeshVisible: BoolProperty(default=True)
    RemoVisible: BoolProperty(default=False)
    btnRemoText: StringProperty(default="Open Remote Control")
    btnRemoIcon: StringProperty(default="") #place holder only, not used for now
    timerObject: StringProperty(default="")
    addon_ident: StringProperty(default="RC_CAMERA")

class RC_memory_slot(bpy.types.PropertyGroup):
    CameraLens: FloatProperty(default=0)
    CameraLocation: FloatVectorProperty(size=3,default=(0,0,0),subtype='TRANSLATION')  
    CameraRotation: FloatVectorProperty(size=3,default=(0,0,0),subtype='EULER')
    TargetLocation: FloatVectorProperty(size=3,default=(0,0,0),subtype='TRANSLATION')  
    TargetRotation: FloatVectorProperty(size=3,default=(0,0,0),subtype='EULER')
    
class CustomSceneList(bpy.types.PropertyGroup):
    # name = StringProperty() # this is inherited from bpy.types.PropertyGroup
    pass

    
#--- ### Operators
class RefCameraPanelbutton_ZOOM(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_zoom"
    bl_label = "Set adjustment mode"
    bl_description = "(GZ: Zoom) - Camera LOCAL mode; Pivot Point Active Element"
    #--- parameters
    mode : StringProperty(name="mode", description="execution mode", default="NPANEL")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return is_object_mode(context)
    
    def execute(self,context):
        SetAdjustmentMode("ZOOM")
        start_action = RC_ACTION_MAIN() if self.mode == 'NPANEL' else RC_ACTION_REMO()
        if start_action:
            bpy.ops.transform.translate('INVOKE_DEFAULT',constraint_axis=(False,False,True)) 
        return {'FINISHED'}
        
class RefCameraPanelbutton_HORB(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_horb"
    bl_label = "Set adjustment mode"
    bl_description = "(RZ: Horizontal Orbit) - Camera GLOBAL mode; Pivot Point 3D Cursor"
    #--- parameters
    mode : StringProperty(name="mode", description="execution mode", default="NPANEL")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return is_object_mode(context)
    
    def execute(self,context):
        SetAdjustmentMode("HORB")
        start_action = RC_ACTION_MAIN() if self.mode == 'NPANEL' else RC_ACTION_REMO()
        if start_action:
            bpy.ops.transform.rotate('INVOKE_DEFAULT',constraint_axis=(False,False,True)) 
        return {'FINISHED'}
        
class RefCameraPanelbutton_VORB(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_vorb"
    bl_label = "Set adjustment mode"
    bl_description = "(RX: Vertical Orbit) - Camera LOCAL mode; Pivot Point 3D Cursor"
    #--- parameters
    mode : StringProperty(name="mode", description="execution mode", default="NPANEL")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return is_object_mode(context)
    
    def execute(self,context):
        SetAdjustmentMode("VORB")
        start_action = RC_ACTION_MAIN() if self.mode == 'NPANEL' else RC_ACTION_REMO()
        if start_action:
           bpy.ops.transform.rotate('INVOKE_DEFAULT',constraint_axis=(True,False,False)) 
        return {'FINISHED'}
        
class RefCameraPanelbutton_TILT(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_tilt"
    bl_label = "Set adjustment mode"
    bl_description = "(RY: Tilt) - Target LOCAL mode; Pivot Point Active Element"
    #--- parameters
    mode : StringProperty(name="mode", description="execution mode", default="NPANEL")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        if (not is_object_mode(context)):
            return False
        else:
            return (not context.scene.var.OpState9)
    
    def execute(self,context):
        SetAdjustmentMode("TILT")
        start_action = RC_ACTION_MAIN() if self.mode == 'NPANEL' else RC_ACTION_REMO()
        if start_action:
            bpy.ops.transform.rotate('INVOKE_DEFAULT',constraint_axis=(False,True,False)) 
        return {'FINISHED'}
        
class RefCameraPanelbutton_MOVE(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_move"
    bl_label = "Set adjustment mode"
    bl_description = "(GXYZ: Translation) - Camera+Target GLOBAL mode; Pivot Point Active Element"
    #--- parameters
    mode : StringProperty(name="mode", description="execution mode", default="NPANEL")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        if (not is_object_mode(context)):
            return False
        else:
            return (not context.scene.var.OpState8)
    
    def execute(self,context):
        SetAdjustmentMode("MOVE")
        start_action = RC_ACTION_MAIN() if self.mode == 'NPANEL' else RC_ACTION_REMO()
        if start_action:
            bpy.ops.transform.translate('INVOKE_DEFAULT') 
        return {'FINISHED'}
        
class RefCameraPanelbutton_ROLL(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_roll"
    bl_label = "Set adjustment mode"
    bl_description = "(RXY: Rotation) - Camera+Target GLOBAL mode; Pivot Point Active Element"
    #--- parameters
    mode : StringProperty(name="mode", description="execution mode", default="NPANEL")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        if (not is_object_mode(context)):
            return False
        else:
            return (not context.scene.var.OpState9)
    
    def execute(self,context):
        SetAdjustmentMode("ROLL")
        start_action = RC_ACTION_MAIN() if self.mode == 'NPANEL' else RC_ACTION_REMO()
        if start_action:
            bpy.ops.transform.rotate('INVOKE_DEFAULT') 
        return {'FINISHED'}
        
class RefCameraPanelbutton_POV(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_pov"
    bl_label = "Set adjustment mode"
    bl_description = "(GXYZ: Perspective) - Camera GLOBAL mode; Pivot Point Active Element"
    #--- parameters
    mode : StringProperty(name="mode", description="execution mode", default="NPANEL")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return is_object_mode(context)
    
    def execute(self,context):
        SetAdjustmentMode("POV")
        start_action = RC_ACTION_MAIN() if self.mode == 'NPANEL' else RC_ACTION_REMO()
        if start_action:
            bpy.ops.transform.translate('INVOKE_DEFAULT') 
        return {'FINISHED'}
        
class RefCameraPanelbutton_RSET(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_rset"
    bl_label = "Reset Target"
    bl_description = "Sets Target Location and Rotation to (0,0,0) and removes related locks"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return is_object_mode(context)
    
    def execute(self,context):
        scn = bpy.context.scene
        camera = scn.camera
        target = get_target(camera)    
        scn.var.OpState8 = False
        scn.var.OpState9 = False
        target.lock_location = (scn.var.OpState8,scn.var.OpState8,scn.var.OpState8)
        target.lock_rotation = (scn.var.OpState9,scn.var.OpState9,scn.var.OpState9)
        target.location = (0,0,0)
        target.rotation_euler = (0,0,0)
        return {'FINISHED'}
        
class RefCameraPanelbutton_LPOS(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_lpos"
    bl_label = "Lock Position"
    bl_description = "Locks Target Position properties and disables impacted buttons"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return is_object_mode(context)

    def execute(self,context):
        scn = bpy.context.scene
        camera = scn.camera
        target = get_target(camera)         
        scn.var.OpState8 = not scn.var.OpState8
        target.lock_location = (scn.var.OpState8,scn.var.OpState8,scn.var.OpState8)
        if scn.var.OpState5:
            scn.var.OpState5 = False
            SetAdjustmentMode("ZOOM")
        return {'FINISHED'}
    
class RefCameraPanelbutton_LROT(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_lrot"
    bl_label = "Lock Rotation"
    bl_description = "Locks Target Rotation properties and disables impacted buttons"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return is_object_mode(context)
    
    def execute(self,context):
        scn = bpy.context.scene
        camera = scn.camera
        target = get_target(camera)           
        scn.var.OpState9 = not scn.var.OpState9
        target.lock_rotation = (scn.var.OpState9,scn.var.OpState9,scn.var.OpState9)
        if scn.var.OpState4 or scn.var.OpState6:
            scn.var.OpState4 = False
            scn.var.OpState6 = False
            SetAdjustmentMode("ZOOM")
        return {'FINISHED'}

def blink_mesh_objects():
    context = bpy.context
    try:
        rc = find_collection(context.scene.collection, RC_MESHES())
        if rc:
            if not context.view_layer.layer_collection.children[RC_MESHES()].hide_viewport:
                for obj in rc.objects:
                    if not obj.type == 'MESH': 
                        continue
                    thisObjWasMadeHidden = obj.hide_get()
                    thisObjFound = False
                    for stateListed in context.scene.lastObjectSet:
                        if obj.name == stateListed.name:
                            obj.hide_set(context.scene.var.MeshVisible)
                            thisObjFound = True
                            break
                    if thisObjFound == False and thisObjWasMadeHidden == False:
                        #-this is a workaround to add to the list those meshes that
                        # the user has manually unhidden directly on the outliner's collection 
                        obj.hide_set(context.scene.var.MeshVisible)
                        newItem = context.scene.lastObjectSet.add()
                        newItem.name = obj.name
                    if thisObjFound == True and thisObjWasMadeHidden == True and context.scene.var.MeshVisible == True:
                        #-this is a workaround to remove from the list those meshes that
                        # the user has manually hidden directly on the outliner's collection 
                        itemID = context.scene.lastObjectSet.find(obj.name)
                        context.scene.lastObjectSet.remove(itemID)
                return True        
    except:
        pass
    return False

def blink_mesh_timer(idx):
    context = bpy.context
    has_error = True
    break_out = False
    try:
        if context.mode == 'OBJECT':
            if bpy.app.version >= (2, 90, 0):    
                areas = context.window.screen.areas
            else:
                areas = context.window_manager.windows[idx].screen.areas
            #
            for area in areas:
                if area.type == 'VIEW_3D':
                    # The following code is better for Blender 2.90 and greater
                    if bpy.app.version >= (2, 90, 0):    
                        #if area.regions[-1].data.view_perspective == 'CAMERA': # <-- Could've done just this instead
                            #has_error = not blink_mesh_objects()               #     but I didn't trust it for production.
                        #break                                                  #
                        for region in area.regions:
                            if region.type == 'WINDOW':
                                if region.data.view_perspective == 'CAMERA':    # 2.80 issue: '.data' does not exist here
                                    has_error = not blink_mesh_objects()
                                    break_out = True
                                    break
                    else:
                    # The following code is needed for Blender 2.80 thru 2.83
                        for space_data in area.spaces:
                            if space_data.type == 'VIEW_3D': # This is a SpeceView3D
                                if space_data.region_3d.view_perspective == 'CAMERA': # This is a RegionView3D
                                    has_error = not blink_mesh_objects()
                                    break_out = True
                                break
                # Found one that works, so get out of external "For-loop"
                if break_out:
                    break        
    except: 
        pass

    if len(context.scene.lastObjectSet.items()) > 0 and not has_error:
        context.scene.var.MeshVisible = not context.scene.var.MeshVisible
        package = __package__[0:__package__.find(".")]
        preferences = bpy.context.preferences.addons[package].preferences
        duration = preferences.RC_BLINK_ON if context.scene.var.MeshVisible else preferences.RC_BLINK_OFF
        return round(duration,1)
    else:    
        # Auto stop blinking if meshes are made unavailable or any errors
        context.scene.var.OpStateA = False
        if not context.scene.var.MeshVisible:
            # Call it one last time if needed to leave the mesh(es) turned on
            context.scene.var.MeshVisible = blink_mesh_objects()
        return None

class RefCameraPanelbutton_FLSH(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_flsh" #
    bl_label = "Blink mesh(es)"
    bl_description = "Turns the mesh(es) visibility on/off"
    #--- parameters
    mode : StringProperty(name="mode", description="execution mode", default="NPANEL")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return is_object_mode(context)
            
    @classmethod
    def description(cls, context, event):
        description = "Turns the visibility on/off for mesh(es) in collection '{0}'.\n" +\
                      "Blinking frequency can be adjusted in the addon Preferences.\n" +\
                      "Current settings are:  On ({1:.1f} sec), Off ({2:.1f} sec)"
        return (description.format(RC_MESHES(), RC_BLINK_ON(), RC_BLINK_OFF()))

    def invoke(self, context, event):
        #input validation: 
        return self.execute(context)
            
    def execute(self, context):
        idx = bpy.context.window_manager.windows[:].index(bpy.context.window)
        if blink_mesh_timer(idx) is None:
            if self.mode == 'NPANEL':
                self.report(type={'ERROR'}, message="Collection '" + RC_MESHES() + "' not found or all meshes are hidden")
            return {'CANCELLED'}
        else:    
            context.scene.var.OpStateA = not context.scene.var.OpStateA
            if context.scene.var.OpStateA:
                if not bpy.app.timers.is_registered(blink_mesh_timer):
                    bpy.types.Scene.timerObject = functools.partial(blink_mesh_timer, idx)
                    bpy.app.timers.register(bpy.types.Scene.timerObject, first_interval=0, persistent=False)
            else:
                if bpy.app.timers.is_registered(bpy.types.Scene.timerObject):
                    bpy.app.timers.unregister(bpy.types.Scene.timerObject)
                    bpy.types.Scene.timerObject = None
                if not context.scene.var.MeshVisible:
                    # Call it one last time if needed to leave the mesh(es) turned on
                    context.scene.var.MeshVisible = blink_mesh_objects()
        return {'FINISHED'}
        
def switch_memory_data(slot=0):
    global LastState

    scn = bpy.context.scene
    camera = scn.camera
    target = get_target(camera)  
    
    scene = bpy.context.scene
    backup_slot = scene.memory_slots_collection[0]
    memory_slot = scene.memory_slots_collection[slot]
    
    # Copy slot data into a temporary variable to make the switch later
    backup_slot.CameraLens = memory_slot.CameraLens
    backup_slot.CameraLocation = memory_slot.CameraLocation
    backup_slot.CameraRotation = memory_slot.CameraRotation
    backup_slot.TargetLocation = memory_slot.TargetLocation
    backup_slot.TargetRotation = memory_slot.TargetRotation
    
    # Store current scene data in the given memory slot
    memory_slot.CameraLens = camera.data.lens
    memory_slot.CameraLocation = camera.location
    memory_slot.CameraRotation = camera.rotation_euler
    memory_slot.TargetLocation = target.location
    memory_slot.TargetRotation = target.rotation_euler

    # Apply the former slot data to the current scene 
    camera.data.lens = backup_slot.CameraLens
    camera.location = backup_slot.CameraLocation
    camera.rotation_euler = backup_slot.CameraRotation
    target.location = backup_slot.TargetLocation
    target.rotation_euler = backup_slot.TargetRotation

    # Finally save the current state to prevent impact by the depsgraph_update_post's after_update() function
    LastState = (camera.name, camera.data.lens)

class RefCameraPanelbutton_M1(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_m1"
    bl_label = "M1"
    bl_description = "Switches the Camera+Target set configuration with memory slot 1"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context) and bpy.context.scene.var.OpStatM1)
    
    def execute(self,context):
        switch_memory_data(1) 
        return {'FINISHED'}
        
class RefCameraPanelbutton_M2(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_m2"
    bl_label = "M2"
    bl_description = "Switches the Camera+Target set configuration with memory slot 2"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context) and bpy.context.scene.var.OpStatM2)
    
    def execute(self,context):
        switch_memory_data(2) 
        return {'FINISHED'}
        
class RefCameraPanelbutton_M3(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_m3"
    bl_label = "M3"
    bl_description = "Switches the Camera+Target set configuration with memory slot 3"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context) and bpy.context.scene.var.OpStatM3)
    
    def execute(self,context):
        switch_memory_data(3) 
        return {'FINISHED'}
        
class RefCameraPanelbutton_MS(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_ms"
    bl_label = "MSave"
    bl_description = "Saves the Camera+Target set configuration in the next available memory slot"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context) and not bpy.context.scene.var.OpStatM3)
    
    def execute(self,context):
        scn = bpy.context.scene
        if not scn.var.OpStatM1:
            scn.var.OpStatM1 = True
            backup_slot = bpy.context.scene.memory_slots_collection.add()
            memory_slot = bpy.context.scene.memory_slots_collection.add()
            self.save_memory_data(memory_slot)
        else:
            if not scn.var.OpStatM2:
                scn.var.OpStatM2 = True
                memory_slot = bpy.context.scene.memory_slots_collection.add()
                self.save_memory_data(memory_slot)
            else:    
                if not scn.var.OpStatM3:
                    scn.var.OpStatM3 = True
                    memory_slot = bpy.context.scene.memory_slots_collection.add()
                    self.save_memory_data(memory_slot)
        return {'FINISHED'}
        
    def save_memory_data(self, memory_slot):
        scn = bpy.context.scene
        camera = scn.camera
        target = get_target(camera)  
        
        # Store current scene data on the given memory slot
        memory_slot.CameraLens = camera.data.lens
        memory_slot.CameraLocation = camera.location
        memory_slot.CameraRotation = camera.rotation_euler
        memory_slot.TargetLocation = target.location
        memory_slot.TargetRotation = target.rotation_euler

class RefCameraPanelbutton_MC(bpy.types.Operator):
    bl_idname = "object.ref_camera_panelbutton_mc"
    bl_label = "MC"
    bl_description = "Clears out all three memory slots"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context) and bpy.context.scene.var.OpStatM1)
    
    def execute(self,context):
        scn = bpy.context.scene
        scn.var.OpStatM1 = False
        scn.var.OpStatM2 = False
        scn.var.OpStatM3 = False
        bpy.context.scene.memory_slots_collection.clear()
        return {'FINISHED'}
        
def focus_on_object(object):
    object.hide_set(False) 
    object.hide_select = False
    object.select_set(True) 
    bpy.context.view_layer.objects.active = object
        
def SetAdjustmentMode(type="None"):
    ''' Sets the transformation orientation & selects camera/target '''
    camera = bpy.context.scene.camera
    target = get_target(camera)           

    scn = bpy.context.scene
    var = scn.var

    if type == "None":
        #when it is "None" the prior state will be kept
        pass
    else:
        #clean up all button states
        var.OpState1 = False
        var.OpState2 = False
        var.OpState3 = False
        var.OpState4 = False
        var.OpState5 = False
        var.OpState6 = False
        var.OpState7 = False

    #select the appropriate button state            
    if type == 'ZOOM':  
        var.OpState1 = True
    if type == 'HORB':
        var.OpState2 = True
    if type == 'VORB':
        var.OpState3 = True
    if type == 'TILT':
        var.OpState4 = True
    if type == 'MOVE':
        var.OpState5 = True
    if type == 'ROLL':        
        var.OpState6 = True
    if type == 'POV':
        var.OpState7 = True

    #make sure, that everything is deselected to avoid moving them by accident
    bpy.ops.object.select_all(action='DESELECT') 
    #now select and set the camera and/or target according to user option
    if var.OpState1:
        #ZOOM: Dolly moves only back and forth on camera's axis (G + ZZ + move mouse)
        #Good to adjust 'Distance/Size' 
        #Characteristics - Selected:Camera; Transformation:Local; Pivot:ActiveElement(=Camera)
        focus_on_object(camera)
        scn.transform_orientation_slots[0].type = 'LOCAL'
        scn.tool_settings.transform_pivot_point = 'ACTIVE_ELEMENT'

    if var.OpState2:
        #Horizontal Orbit: The camera rotates around the target which stays in place (R + Z + move mouse)
        #Good to adjust 'Rotation'
        #Characteristics - Selected:Camera; Transformation:Global; Pivot:3DCursor (which is moved to 'Target' origin)
        focus_on_object(target)
        bpy.ops.view3d.snap_cursor_to_selected()
        target.select_set(False) 
        #now select and set the camera and/or target according to user option
        focus_on_object(camera)
        scn.transform_orientation_slots[0].type = 'GLOBAL'
        scn.tool_settings.transform_pivot_point = 'CURSOR'

    if var.OpState3:
        #Vertical Orbit: The camera rotates around the target which stays in place (R + XX + move mouse)
        #Good to adjust 'Elevation/Azimuth'
        #Characteristics - Selected:Camera; Transformation:Local; Pivot:3DCursor (which is moved to 'Target' origin)
        focus_on_object(target)
        bpy.ops.view3d.snap_cursor_to_selected()
        target.select_set(False) 
        #now select and set the camera and/or target according to user option
        focus_on_object(camera)
        scn.transform_orientation_slots[0].type = 'LOCAL'
        scn.tool_settings.transform_pivot_point = 'CURSOR'

    if var.OpState4:
        #TILT: Camera stays still, moves from up and down (R + YY + move mouse)
        #Good to adjust 'Inclination'
        #Characteristics - Selected:Target; Transformation:Local; Pivot:ActiveElement(=Target)
        focus_on_object(target)
        scn.transform_orientation_slots[0].type = 'LOCAL'
        scn.tool_settings.transform_pivot_point = 'ACTIVE_ELEMENT'

    if var.OpState5:
        #this one is same as button6 (not an error)
        #Translation: Truck/Pedestal moves only from left to right on camera's axis (G + X/Y/Z + move mouse)
        #Good to adjust 'Position'
        #Characteristics - Selected:Camera+Target; Transformation:Global; Pivot:ActiveElement(=Target)
        focus_on_object(camera)
        focus_on_object(target)
        scn.transform_orientation_slots[0].type = 'GLOBAL'
        scn.tool_settings.transform_pivot_point = 'ACTIVE_ELEMENT'

    if var.OpState6:
        #this one is same as button5 (not an error)
        #Roll: Camera stays still, lean from left to right (R + X/Y + move mouse)
        #Good to adjust 'Angle'
        #Characteristics - Selected:Camera+Target; Transformation:Global; Pivot:ActiveElement(=Target)
        focus_on_object(camera)
        focus_on_object(target)
        scn.transform_orientation_slots[0].type = 'GLOBAL'
        scn.tool_settings.transform_pivot_point = 'ACTIVE_ELEMENT'

    if var.OpState7:
        #Perspective: combination of Camera's Translation with Elevation/Rotation (G + X/Y/Z + mouse move)
        #Good to adjust 'Point of View'
        #Characteristics - Selected:Camera; Transformation:Global; Pivot:ActiveElement(=Target)
        focus_on_object(camera)
        scn.transform_orientation_slots[0].type = 'GLOBAL'
        scn.tool_settings.transform_pivot_point = 'ACTIVE_ELEMENT'

class SetRemoteControl(bpy.types.Operator):
    ''' Opens/Closes the remote control panel '''
    bl_idname = "object.set_remote_control" #
    bl_label = "Open Remote Control"
    bl_description = "Turns the camera remote control on/off"
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context))
        
    def invoke(self, context, event):
        #input validation: 
        return self.execute(context)
            
    def execute(self,context):
        if context.scene.var.RemoVisible == True:
            context.scene.var.btnRemoText = "Open Remote Control"
        else:    
            context.scene.var.btnRemoText = "Close Remote Control"
            context.scene.var.objRemote = bpy.ops.object.dp_ot_draw_operator('INVOKE_DEFAULT')

        context.scene.var.RemoVisible = not context.scene.var.RemoVisible 
        return {'FINISHED'}
        
class SetReferenceCamera(bpy.types.Operator):
    ''' Sets one of the predefined cameras and associated reference images '''
    bl_idname = "object.set_reference_camera" #
    bl_label = "Set reference camera"
    bl_description = "Sets one of the predefined cameras and associated reference images"
    # bl_options = {'REGISTER', 'UNDO'} #Set this options, if you want to update  
    #                                  parameters of this operator interactively 
    #                                  (in the Tools pane) 
    #--- parameters
    camera_name : StringProperty(name="camera", description="camera object name, (one of the predefined camera with a reference image in the background)", default = "")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context))
        
    def invoke(self, context, event):
        #input validation: 
        camera = get_object(self.camera_name,get_active_object(context),context)
        if camera: 
            return self.execute(context)
        else:
            self.report(type={'ERROR'}, message="Camera '" + self.camera_name + "' not found")
            return {'CANCELLED'}
        
    def execute(self,context):
        #make sure, that everyting is deselected to avoid moving them by accident
        bpy.ops.object.select_all(action='DESELECT') 
        #make sure, that all cameras and targets are hidden from view to leave a clean scene
        rc = find_collection(context.scene.collection, RC_CAMERAS())
        if rc:
            for obj in rc.objects:
                obj.hide_set(True)
            #looking up for each collection child
            for rch in rc.children:
                for obj in rch.objects:
                    obj.hide_set(True)
        rc = find_collection(context.scene.collection, RC_TARGETS())
        if rc:
            for obj in rc.objects:
                obj.hide_set(True)
        #now it can enable the appropriate camera
        camera = get_object(self.camera_name,get_active_object(context),context)
        camera.hide_set(False) 
        #update the working collection (if exists):
        wrk = find_collection(context.scene.collection, RC_TEMP())
        if not wrk: #if the working collection does not exists - create one:
            if RC_TEMP() in bpy.data.collections: #if such a collection already exists in another scene:
                wrk = bpy.data.collections[RC_TEMP()] #use it, to avoid Python exception
            else:
                wrk = bpy.data.collections.new(RC_TEMP())#create a new collection
            context.scene.collection.children.link(wrk) #add it to the current scene
        #at this point wrk represents the working collection:
        unlink_all_objects(wrk) #clear its previous contents
        #link the current camera and its target:
        wrk.objects.link(camera)
        wrk.objects.link(get_target(camera))
        wrk.hide_viewport = False #make sure, that the working collection is visible
        wrk.hide_render = True #make sure, that the working collection will not be rendered 
        set_active_object(camera) #this line works if the <camera> object is visible in viewport.
        bpy.ops.view3d.object_as_camera()
        #Update current render settings (it determines the camera screen size)
        image = get_image(camera) 
        context.scene.render.resolution_x = image.size[0] #size:x
        context.scene.render.resolution_y = image.size[1] #size:y
        #turn visibility for the related target/constraint
        target = get_target(camera)
        target.hide_set(False) 
        #Calls the adjustment mode class in its default mode to keep current mode
        SetAdjustmentMode() 
        #Calls the memory slot clear operator
        if bpy.ops.object.ref_camera_panelbutton_mc.poll():        
            bpy.ops.object.ref_camera_panelbutton_mc()
        return {'FINISHED'}

class AddCollectionSet(bpy.types.Operator):
    ''' Adds the required collection set '''
    bl_idname = "object.add_collection_set" #
    bl_label = "Open Image"
    bl_description = "Adds the required collection set to the scene"
    # bl_options = {'REGISTER', 'UNDO'} #Set this options, if you want to update  
    #                                  parameters of this operator interactively 
    #                                  (in the Tools pane) 
    #--- parameters
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context))
        
    def execute(self,context):
        if RC_CAMERAS() != "":
            rc1 = find_collection(context.scene.collection, RC_CAMERAS())
            if not rc1:
                #add RC_CAMERAS collection
                if RC_CAMERAS() in bpy.data.collections: #if such a collection already exists in another scene:
                    wrk = bpy.data.collections[RC_CAMERAS()] #use it, to avoid Python exception
                else:
                    wrk = bpy.data.collections.new(RC_CAMERAS())#create a new collection
                context.scene.collection.children.link(wrk) #add it to the current scene
                wrk.hide_viewport = False #make sure, that the working collection is visible
                wrk.hide_render = True #make sure, that the working collection will not be rendered 
                        
        if RC_TARGETS() != "":
            rc = find_collection(context.scene.collection, RC_TARGETS())
            if not rc:
                #add RC_TARGETS collection
                if RC_TARGETS() in bpy.data.collections: #if such a collection already exists in another scene:
                    wrk = bpy.data.collections[RC_TARGETS()] #use it, to avoid Python exception
                else:
                    wrk = bpy.data.collections.new(RC_TARGETS())#create a new collection
                context.scene.collection.children.link(wrk) #add it to the current scene
                wrk.hide_viewport = False #make sure, that the working collection is visible
                wrk.hide_render = True #make sure, that the working collection will not be rendered 

        if RC_MESHES() != "":
            rc = find_collection(context.scene.collection, RC_MESHES())
            if not rc:
                #add RC_MESHES collection
                if RC_MESHES() in bpy.data.collections: #if such a collection already exists in another scene:
                    wrk = bpy.data.collections[RC_MESHES()] #use it, to avoid Python exception
                else:
                    wrk = bpy.data.collections.new(RC_MESHES())#create a new collection
                context.scene.collection.children.link(wrk) #add it to the current scene
                wrk.hide_viewport = False #make sure, that the working collection is visible
                wrk.hide_render = True #make sure, that the working collection will not be rendered 
        return {'FINISHED'}

class CreateNewCameraSet(bpy.types.Operator, ImportHelper):
    ''' Adds to the current collection a new set of Camera and Target '''
    bl_idname = "object.create_new_camera_set" #
    bl_label = "Open Image"
    bl_description = "Adds to the current collection a new set of Camera and Target"
    # bl_options = {'REGISTER', 'UNDO'} #Set this options, if you want to update  
    #                                  parameters of this operator interactively 
    #                                  (in the Tools pane) 
    #--- parameters
    collect_name : StringProperty(name="collection", description="name of current collection", default = "")
    filter_glob  : StringProperty(default='*.jpg;*.jpeg;*.png;*.tga;*.tif;*.tiff;*.bmp', options={'HIDDEN'})
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context))
        
    def execute(self,context):
        camera_rc = find_collection(context.scene.collection, self.collect_name)
        if not camera_rc: 
            self.report(type={'ERROR'}, message="Collection '" + self.collect_name + "' not found")
            return {'CANCELLED'} 

        if RC_TARGETS() == "":
            target_rc = camera_rc
        else:
            target_rc = find_collection(context.scene.collection, RC_TARGETS())
            if not target_rc:
                self.report(type={'ERROR'}, message="Targets collection '" + RC_TARGETS() + "' not found")
                return {'CANCELLED'} 

        camera_name = bpy.path.display_name(self.filepath, has_ext=True)
        target_name = camera_name + ".Target"

        #validate camera does not exist already and get a group id
        ids = get_camera_names(context)
        ids.sort()
        subpanel = 0
        sub_name = ""
        propSubPanel = ""
        if ids != None:
            for id in ids:
                if id[0] != "" and id[0] != sub_name:
                    subpanel += 1
                    sub_name = id[0]
                    if sub_name == self.collect_name:
                        propSubPanel = f"panel_switch_{subpanel:03d}"
                if id[1] == camera_name:
                    if subpanel > 0:
                        #currently the API does not offer a way to expand/collapse the main panel
                        setattr(bpy.context.scene, f"panel_switch_{subpanel:03d}", True)
                    bpy.ops.object.set_reference_camera(camera_name=camera_name)
                    self.report(type={'ERROR'}, message="A camera named '" + camera_name + "' already exists")
                    return {'CANCELLED'} 

        #validate target does not exist already 
        if get_object(target_name,None,context) != None:
            self.report(type={'ERROR'}, message="A target named '" + target_name + "' already exists")
            return {'CANCELLED'} 

        try:
            #new camera instance 
            camera_data = bpy.data.cameras.new(name=camera_name)
            camera_object = bpy.data.objects.new(camera_name, camera_data)
            camera_object.location = (0,0,10)
            camera_object.data.sensor_width = RC_SENSOR()
            camera_object.data.lens = RC_FOCUS()
            camera_object.data.lens_unit = 'MILLIMETERS'
            camera_object.data.clip_start = 1.0
            camera_object.data.clip_end = 3000
            camera_object.data.type = 'PERSP'

            #new target instance 
            bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=0.3,depth=0.3,end_fill_type='NGON',location=(0,0,0),rotation=(0,0,0))
            bpy.context.object.name = target_name
            target_object = bpy.context.object
            target_object.display_type = RC_TRGMODE() 
            target_object.color = RC_TRGCOLOR()

            #set camera constraints
            constraint = camera_object.constraints.new('TRACK_TO')
            constraint.target = target_object
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'
            constraint.use_target_z = True

            #set target constraints
            constraint = target_object.constraints.new('COPY_ROTATION')
            constraint.target = camera_object
            constraint.use_x = False
            constraint.use_y = False
            constraint.use_z = True

            #link to collection
            camera_rc.objects.link(camera_object)
            collection = target_object.users_collection[0]
            collection.objects.unlink(target_object)
            target_rc.objects.link(target_object)

            #add backgound image to camera
            image = bpy.data.images.load(self.filepath)
            camera_object.data.show_background_images = True
            bg = camera_object.data.background_images.new()
            bg.image = image
            bg.alpha = RC_OPACITY()
            bg.display_depth = RC_DEPTH()
            bg.frame_method = 'CROP'

        except:
            self.report(type={'ERROR'}, message="Failed creation of camera and/or target")
            return {'CANCELLED'} 

        #selects the new added camera set
        bpy.ops.object.set_reference_camera(camera_name=camera_object.name)
        #make sure the destination subpanel is not collapsed
        if subpanel > 0 and propSubPanel != "":
            #currently the API does not offer a way to expand/collapse the main panel
            setattr(bpy.context.scene, propSubPanel, True)
        return {'FINISHED'}

class UnlistReferenceCamera(bpy.types.Operator):
    ''' Removes this camera from the list set '''
    bl_idname = "object.unlist_reference_camera" 
    bl_label = "Hide"
    bl_description = "Removes this camera from the list set"
    # bl_options = {'REGISTER', 'UNDO'} #Set this options, if you want to update  
    #                                  parameters of this operator interactively 
    #                                  (in the Tools pane) 
    #--- parameters
    camera_name : StringProperty(name="camera", description="camera object name, (one of the predefined camera with a reference image in the background)", default = "")
    #--- Blender interface methods
    @classmethod
    def poll(cls,context):
        return (is_object_mode(context))
        
    def invoke(self, context, event):
        #input validation: 
        camera = get_object(self.camera_name,get_active_object(context),context)
        if camera: 
            return self.execute(context)
        else:
            self.report(type={'ERROR'}, message="Camera '" + self.camera_name + "' not found")
            return {'CANCELLED'}
        
    def execute(self,context):
        camera = get_object(self.camera_name,get_active_object(context),context)
        if camera: 
            #disables and removes the camera from list set
            camera.select_set(False)
            camera.hide_set(True)
            camera.hide_select = True
            #disables and removes its target from list set
            target = get_target(camera) 
            target.select_set(False) 
            target.hide_set(True)
            target.hide_select = True
        return {'FINISHED'}

class OBJECT_PT_CameraLens(bpy.types.Panel):
    #in PROPERTIES window none of the operators work - thus I use the Properties window
    bl_space_type = 'VIEW_3D' #'PROPERTIES'
    bl_region_type = 'UI' #'WINDOW'
    bl_category = "Cameras"
    bl_label = "Current"
    #bl_options = {'HIDE_HEADER'}
       
    #--- methods    
    @classmethod
    def poll(cls, context):
        #show this panel in Object Mode, only:
        return (context.mode == 'OBJECT')
   
    def draw(self, context):
        layout = self.layout
        if DEBUG: layout.operator(unreg.bl_idname, text="Unregister Me")
        ids = get_camera_names(context)
        if ids == None or ids == []:
            return None

        self.lens = context.scene.camera.data.lens
        camera = context.scene.camera.data
        camobj = get_object(context.scene.camera.name,get_active_object(context),context)
        if camobj.hide_select == False:
            layout.label(text="Camera: " + context.scene.camera.name)
        else:
            layout.label(text="Camera:  No camera selected") 
        layout.separator()
            
        showControls = False
        if context.space_data.type == 'VIEW_3D' and context.mode == 'OBJECT':
            if camera.type != 'PERSP' or camobj.hide_select or camobj.users_collection[0].hide_select:
                #-- do not show camera control buttons
                showControls = False
            else:
                showControls = view_is_camera()

        if showControls:
            #-- camera focal length slider
            layout.prop(camera, "lens", text="Lens")
            
            if RC_SUBP_MODE() != 'EXTENDED' and context.scene.var.RemoVisible == False:
                #-- object visibility button
                op = layout.operator(RefCameraPanelbutton_FLSH.bl_idname, text="Blink Mesh(es)", depress=context.scene.var.OpStateA)  #, icon=context.scene.var.btnMeshIcon)
                    
            if RC_SUBP_MODE() != 'EXTENDED' or context.scene.var.RemoVisible == True:                        
                #-- remote control switch button
                op = layout.operator(SetRemoteControl.bl_idname, text=context.scene.var.btnRemoText)
                
            #if remote control is active suppress buttons on N-Panel
            if context.scene.var.RemoVisible == True:
                layout.separator()
            
            #-- transformation orientation mode buttons
            elif RC_SUBP_MODE() == 'COMPACT':
                row = layout.row(align=True)
                row.scale_y = 2
                op = row.operator(RefCameraPanelbutton_ZOOM.bl_idname, text="Zoom", depress=context.scene.var.OpState1)
                op = row.operator(RefCameraPanelbutton_HORB.bl_idname, text="HOrb", depress=context.scene.var.OpState2)
                op = row.operator(RefCameraPanelbutton_VORB.bl_idname, text="VOrb", depress=context.scene.var.OpState3)
                op = row.operator(RefCameraPanelbutton_TILT.bl_idname, text="Tilt", depress=context.scene.var.OpState4) 
                op = row.operator(RefCameraPanelbutton_MOVE.bl_idname, text="Move", depress=context.scene.var.OpState5)
                
            elif RC_SUBP_MODE() == 'FULL':
                row = layout.row(align=True)
                row.scale_y = 2
                op = row.operator(RefCameraPanelbutton_ZOOM.bl_idname, text="ZM", depress=context.scene.var.OpState1)
                op = row.operator(RefCameraPanelbutton_HORB.bl_idname, text="HO", depress=context.scene.var.OpState2)
                op = row.operator(RefCameraPanelbutton_VORB.bl_idname, text="VO", depress=context.scene.var.OpState3)
                op = row.operator(RefCameraPanelbutton_TILT.bl_idname, text="TI", depress=context.scene.var.OpState4)
                op = row.operator(RefCameraPanelbutton_MOVE.bl_idname, text="MV", depress=context.scene.var.OpState5)
                op = row.operator(RefCameraPanelbutton_ROLL.bl_idname, text="RO", depress=context.scene.var.OpState6)
                op = row.operator(RefCameraPanelbutton_POV.bl_idname,  text="PV", depress=context.scene.var.OpState7)
                
            elif RC_SUBP_MODE() == 'EXTENDED':
                scn_var = bpy.context.scene.var
                flow = layout.grid_flow(row_major=True, columns=4, even_columns=True, even_rows=True, align=True)
                flow.scale_y = 1.75
                op = flow.operator(RefCameraPanelbutton_MOVE.bl_idname, text="Move", depress=context.scene.var.OpState5)
                op = flow.operator(RefCameraPanelbutton_ROLL.bl_idname, text="Roll", depress=context.scene.var.OpState6)
                op = flow.operator(RefCameraPanelbutton_POV.bl_idname,  text="PoV",  depress=context.scene.var.OpState7)
                op = flow.operator(SetRemoteControl.bl_idname,          text="", icon="TRIA_RIGHT_BAR") # ex-labeled "[REM]"
                op = flow.operator(RefCameraPanelbutton_ZOOM.bl_idname, text="Zoom", depress=context.scene.var.OpState1)
                op = flow.operator(RefCameraPanelbutton_HORB.bl_idname, text="HOrb", depress=context.scene.var.OpState2)
                op = flow.operator(RefCameraPanelbutton_VORB.bl_idname, text="VOrb", depress=context.scene.var.OpState3)
                op = flow.operator(RefCameraPanelbutton_TILT.bl_idname, text="Tilt", depress=context.scene.var.OpState4)
                flow = layout.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
                op = flow.operator(RefCameraPanelbutton_RSET.bl_idname, text="Reset Target")
                op = flow.operator(RefCameraPanelbutton_LPOS.bl_idname, text="Lock Position",  depress=context.scene.var.OpState8)
                op = flow.operator(RefCameraPanelbutton_FLSH.bl_idname, text="Blink Mesh(es)", depress=context.scene.var.OpStateA)
                op = flow.operator(RefCameraPanelbutton_LROT.bl_idname, text="Lock Rotation",  depress=context.scene.var.OpState9)
                
            #-- memory slots buttons
            if not context.scene.var.RemoVisible:
                box = layout.box()
                row = box.row(align=False)
                op = row.operator(RefCameraPanelbutton_M1.bl_idname, text="M1")
                op = row.operator(RefCameraPanelbutton_M2.bl_idname, text="M2")
                op = row.operator(RefCameraPanelbutton_M3.bl_idname, text="M3")
                op = row.operator(RefCameraPanelbutton_MS.bl_idname, text="MS")
                op = row.operator(RefCameraPanelbutton_MC.bl_idname, text="MC")

        return None
                
class OBJECT_PT_RefCameras(bpy.types.Panel):
    #in PROPERTIES window none of the operators work - thus I use the Properties window
    bl_idname = "OBJECT_PT_RefCameras"
    bl_space_type = 'VIEW_3D' 
    bl_region_type = 'UI' 
    bl_category = "Cameras"
    bl_label = " " #"Ref Cameras"
    #bl_options = {'HIDE_HEADER'}
    
    #--- methods    
    @classmethod
    def poll(cls, context):
        #show this panel in Object Mode, only:
        return (context.mode == 'OBJECT')
   
    def draw_header(self, context):
        ids = get_camera_names(context)
        if ids == None:
            layout = self.layout
            layout.label(text=" Ref Cameras")
        else:
            if ids == []:
                layout = self.layout
                layout.label(text=" Ref Cameras")
            elif ids[0][0] == "":
                layout = self.layout
                row = layout.row(align=True)
                row.alignment = 'LEFT'
                row.label(text=" Ref Cameras")
                op = row.operator(CreateNewCameraSet.bl_idname, text="", icon="FILE_NEW", emboss=True).collect_name = RC_CAMERAS()
            else:
                layout = self.layout
                layout.label(text=" Ref Cameras")
        return None

    def draw(self, context):
        scn = context.scene
        layout = self.layout

        ids = get_camera_names(context)
        if ids == None:
            self.show_message(context, 'ERROR', "This scene contains no collection which name ends with '" + RC_CAMERAS() + "' suffix.")
            layout.separator()
            box = layout.box()
            op = box.operator(AddCollectionSet.bl_idname, text="Add Required Collections")
            layout.separator()
            return None
        if ids == []:
            collect = find_collection(context.scene.collection, RC_CAMERAS()) #In this case we know at least, that such a collection exists
                                                                              #so I am locating it here, to provide its full name to the user
            self.show_message(context, 'QUESTION', "Collection '" + collect.name +\
                              "' does not contain any selectable camera with a background image and a TrackTo constraint")
            layout.separator()
            box = layout.box()
            op = box.operator(CreateNewCameraSet.bl_idname, text="Create New Camera Set").collect_name = collect.name
            layout.separator()
            return None

        #If there is data to be displayed let's now populate the subpanels accordingly
        ids.sort()
        subpanel = 0
        sub_name = ""
        showSubPanel = True
        for id in ids:
            if id[0] != "" and id[0] != sub_name:
                sub_name = id[0]
                subpanel += 1
                if subpanel > RC_SUBPANELS():
                    self.show_message(context, 'ERROR', f"Max number of {RC_SUBPANELS()} collections in '" +\
                                      RC_CAMERAS() + "' reached. More cameras not listed above. Check addon preferences.")
                    break

                box = layout.box()
                split = box.split(factor=0.9,align=True)
                row = split.row(align=True)
                row.alignment = 'LEFT'
                
                propSubPanel = f"panel_switch_{subpanel:03d}"
                showSubPanel = scn.get(propSubPanel)
                if showSubPanel == None:
                    showSubPanel = True

                if showSubPanel:
                    row.prop(scn, propSubPanel, icon="TRIA_DOWN", text="", emboss=False)
                    row.label(text=sub_name.upper())
                else:
                    row.prop(scn, propSubPanel, icon="TRIA_RIGHT", text="", emboss=False)
                    row.label(text=sub_name.upper())

                row = split.row(align=True)
                row.alignment = 'RIGHT'
                op = row.operator(CreateNewCameraSet.bl_idname, text="", icon="FILE_NEW", emboss=True).collect_name = sub_name
                
            if showSubPanel:
                if id[0] != "":
                    split = box.split(factor=0.8,align=True)
                else:
                    split = layout.split(factor=0.8,align=True)
                    
                camera_state = False    
                if context.space_data.type == 'VIEW_3D' and context.mode == 'OBJECT':
                    if context.scene.camera.name == id[1]:
                        camera_state = view_is_camera()

                op = split.operator(SetReferenceCamera.bl_idname, text=id[1], depress=camera_state)
                op.camera_name = id[1]
                op = split.operator(UnlistReferenceCamera.bl_idname, text="Hide")
                op.camera_name = id[1]
    
    def show_message(self, cntx, icon, msg):
        """ Helper function that shows in this panel a multi-line text with an optional icon
            Arguments:
                @cntx (Context):     current context
                @icon (str):         icon keyword (can be None)
                @msg (String):       message text
        """ 
        property_shelf = None
        area = cntx.area
        for region in area.regions:
            if region.type == 'UI':
                property_shelf = region
                
        if property_shelf:
            lines = wrap_text(math.ceil(property_shelf.width/8.5), msg)
            layout = self.layout
            for line in lines:
                row = layout.row(align = True)
                row.alignment = 'EXPAND'
                if icon:
                    row.label(text=line, icon=icon)
                    icon = None
                else:
                    row.label(text=line)

#This class only registers when DEBUG > 0
class unreg(bpy.types.Operator):
    bl_idname = "object.unregister_me"
    bl_label = "Unregister Me"
    bl_description = "Unregister the Reference Cameras Control Panel addon and closes it"
    def execute(self, context):
        unregister()
        return{"FINISHED"}


#--- ### API interface functions that handle the automatic camera distance adjustments
from mathutils import Vector
from bpy.app.handlers import persistent
LastState = None #Tuple of two elements: camera object name and its last lens length 
Counter = 0 #Diagnostic counter (for debugging)
 
@persistent
def after_update(arg):
    global LastState, Counter
    camera = bpy.context.scene.camera
    if LastState and LastState[0] == camera.name and camera.data.type == 'PERSP':
        if DEBUG > 0: Counter += 1
        fp = LastState[1] #previous lens length
        if fp != camera.data.lens and fp > 0: #this second condition just in case
            #check if this is one of the reference cameras:
            target = get_target(camera)
            if get_image(camera) and target: #If it has a background image and target object:
                f = camera.data.lens #current lens length
                cv = camera.location
                tv = target.location
                dv = cv - tv #dv is a vector from camera to target object
                u = (f - fp)/fp
                cv += (dv*u) 
                camera.location = cv #shift the camera proportionally to the change in the lens length

                if DEBUG > 0: 
                    print(str(Counter) + ":\tcamera lens length CHANGED from " + str(fp) + " to " + str(camera.data.lens))
                    print("\tnew distance: " + str((camera.location - target.location).length))
    #Finally: save the current state
    LastState = (camera.name, camera.data.lens)
    
Count = 0    
def reference_camera_timer():
    global Count
    Count += 1
    print(Count)
    return None
    
#--- ### Register
if DEBUG: import os
if DEBUG: import time

import bpy.app
from bpy.utils import unregister_class, register_class
#list of the classes in this add-on to be registered in Blender API:
classes = [ 
            Variables,
            RC_memory_slot,
            CustomSceneList,
            AddCollectionSet,
            CreateNewCameraSet,
            SetRemoteControl,
            SetReferenceCamera,
            UnlistReferenceCamera,
            RefCameraPanelbutton_ZOOM,
            RefCameraPanelbutton_HORB,
            RefCameraPanelbutton_VORB,
            RefCameraPanelbutton_TILT,
            RefCameraPanelbutton_MOVE,
            RefCameraPanelbutton_ROLL,
            RefCameraPanelbutton_POV,
            RefCameraPanelbutton_RSET,
            RefCameraPanelbutton_FLSH,
            RefCameraPanelbutton_LPOS,
            RefCameraPanelbutton_LROT,
            RefCameraPanelbutton_M1,
            RefCameraPanelbutton_M2,
            RefCameraPanelbutton_M3,
            RefCameraPanelbutton_MS,
            RefCameraPanelbutton_MC,
            OBJECT_PT_CameraLens,
            OBJECT_PT_RefCameras,
          ]  
if DEBUG: classes.append(unreg)  #for debugging purposes this can be helpful


def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.var = bpy.props.PointerProperty(type=Variables)
    bpy.types.Scene.lastObjectSet = bpy.props.CollectionProperty(type=CustomSceneList)
    bpy.types.Scene.memory_slots_collection = bpy.props.CollectionProperty(type=RC_memory_slot)
    bpy.types.Scene.timerObject = PointerProperty(type=bpy.types.Object)
    for i in range(RC_SUBPANELS()):
        propSubPanel = f"panel_switch_{i+1:03d}"
        setattr(bpy.types.Scene, propSubPanel, bpy.props.BoolProperty(name=propSubPanel,default=True,description="Collapse/Expand this subpanel"))
    bpy.app.handlers.depsgraph_update_post.append(after_update)

    if DEBUG: 
        os.system("cls")
        timestr = time.strftime("%Y-%m-%d %H:%M:%S")
        print('---------------------------------------')
        print('-------------- RESTART ----------------')
        print('---------------------------------------')
        print(timestr, __name__ + ": registered")


def unregister():
    del bpy.types.Scene.var
    del bpy.types.Scene.lastObjectSet
    del bpy.types.Scene.memory_slots_collection
    del bpy.types.Scene.timerObject
    bpy.app.handlers.depsgraph_update_post.remove(after_update)    
    for i in range(RC_SUBPANELS()):
        propSubPanel = f"panel_switch_{i+1:03d}"
        delattr(bpy.types.Scene, propSubPanel)
    for cls in reversed(classes):
        unregister_class(cls)  
    if DEBUG: 
        timestr = time.strftime("%Y-%m-%d %H:%M:%S")
        print(timestr, __name__ + ": UNregistered")


if __name__ == '__main__':
    register()
