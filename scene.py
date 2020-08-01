import bpy




############################

def isEditMode():

    if bpy.context.object.mode == "EDIT":
        return True

    else:
        return False

def isSculptMode():

    return bpy.context.object.mode == "SCULPT"


def isObjectMode():

    return bpy.context.object.mode == "OBJECT"


def toggleObjectMode():

    if isEditMode() or isSculptMode():
        bpy.ops.object.mode_set(mode="OBJECT")

    else:
        return True

    return

def toggleEditMode():

    bpy.ops.object.mode_set(mode='EDIT')


def setActiveObject(context, obj):

    bpy.context.view_layer.objects.active = obj

def selectObject(obj):

    obj.select_set(True)

def deselectObject(obj):

    obj.select_set(False)


def deselectAll():
    
    bpy.ops.object.select_all(action='DESELECT')
    
def setSelectActive(obj):

    deselectAll()
    selectObject(obj)
    setActiveObject(obj)


def getSelectedMeshObjects(context=bpy.context):
    
    return  [obj for obj in context.selected_objects if obj.type=="MESH"]


def processSelected(func):
    
    objs=getSelectedMeshObjects()
    
    for obj in objs:
        func




############################


def setPivot(context, pivot_mode='MEDIAN_POINT'):

    bpy.context.scene.tool_settings.transform_pivot_point = pivot_mode

def setTransformOrient(context,transform_mode='GLOBAL'):

    bpy.context.scene.transform_orientation_slots[0].type=transform_mode
    bpy.context.scene.transform_orientation_slots[1].type=transform_mode

def getCursorPosition():

    return bpy.context.scene.cursor_location

def setCursorLocation(pos):

    bpy.context.scene.cursor_location=pos

def enableManipulator(context):

    context.scene.tool_settings.use_gizmo_mode = {'TRANSLATE', 'ROTATE'}
    bpy.ops.wm.tool_set_by_name(name="Transform")


def setObjectPivot2Cursor():

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return bpy.context.object.location

def setObjectPivot2OwnCenter(pivot_center="ORIGIN_CENTER_OF_MASS"):
    """ """
    ctype='GEOMETRY_ORIGIN'
    if pivot_center==ctype:
        bpy.ops.object.origin_set(type=ctype)

    ctype='ORIGIN_GEOMETRY'
    if pivot_center==ctype:
        bpy.ops.object.origin_set(type=ctype)

    ctype='ORIGIN_CURSOR'
    if pivot_center==ctype:
        bpy.ops.object.origin_set(type=ctype)

    ctype='ORIGIN_CENTER_OF_MASS'
    if pivot_center==ctype:
        bpy.ops.object.origin_set(type=ctype)

    ctype='ORIGIN_CENTER_OF_VOLUME'
    if pivot_center==ctype:
        bpy.ops.object.origin_set(type=ctype)

    return bpy.context.object.location

def setCursor2Selected():
    bpy.ops.view3d.snap_cursor_to_selected()
    return bpy.context.space_data.cursor_location



def setObjectViewMode(context):
    
    context.space_data.shading.color_type = 'OBJECT'
    
def setVertexColorViewMode(context):
    
    context.space_data.shading.color_type = 'VERTEX'

def setObjectMode(mode="OBJECT"):
    
    bpy.ops.object.mode_set(mode=mode)