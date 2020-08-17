import bpy


def driverMute(obj,idx: int):
    obj.animation_data.drivers[idx].mute=True

def driverUnMute(obj,idx: int):
    obj.animation_data.drivers[idx].mute=False

def driverToggle(obj,idx: int):
    
    st=obj.animation_data.drivers[idx].mute
    
    obj.animation_data.drivers[idx].mute=False if st else True 



