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

bl_info = {
    "name": "Reference Cameras Control Panel",
    "description": "Handles cameras associated with reference photos",
    "author": "Witold Jaworski & Jayanam (enhancements by Marcelo M. Marques)",
    "version": (2, 1, 0),
    "blender": (2, 80, 3),
    "location": "View3D > side panel ([N]), [Cameras] tab",
    "support": "COMMUNITY",
    "category": "3D View",
    "warning": "",
    "wiki_url": "http://airplanes3d.net/scripts-257_e.xml",
    "tracker_url": "http://airplanes3d.net/track-257_e.xml"
    }

import bpy
import sys
import importlib

from bpy.props import *

modulesFullNames = {}

modulesNames = [
                'prefs',
                'bl_ui_draw_op',
		'bl_ui_widget',
                'bl_ui_tooltip',
                'bl_ui_label',
                'bl_ui_button',
                'bl_ui_patch',
                'bl_ui_drag_panel',
                'drag_panel_op',
                'reference_cameras'
               ]

for currentModuleName in modulesNames:
    if 'DEBUG_MODE' in sys.argv:
        modulesFullNames[currentModuleName] = ('{}'.format(currentModuleName))
    else:
        modulesFullNames[currentModuleName] = ('{}.{}'.format(__name__, currentModuleName))

if 'DEBUG_MODE' in sys.argv:
    import os
    import time
    os.system("cls")
    print('---------------------------------------')
    print('-------------- RESTART ----------------')
    print('---------------------------------------')
    print(time.time(), __name__ + ": registered")
    print()
 
for currentModuleFullName in modulesFullNames.values():
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
        setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)
 
def register():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()

def unregister():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()
 
if __name__ == "__main__":
    register()