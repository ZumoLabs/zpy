# segmentium
Segmentation add-on for Blender

The current segmentium version is:

```
export SEGMENTIUM_VERSION="1.0.4"
```

To package segmentium for install elsewhere use the zip script:

```
./zip.sh
```

## zpy

Utility bundle for use with bpy.

The current zpy version is:

```
export ZPY_VERSION="v1.1.6"
```

## Install

The current Blender version is:

```
export BLENDER_VERSION="2.90"
```

Symlink (or copy) this folder to the addon folder under your OS's user config folder. For linux this is:

```
mkdir -p ~/.config/blender/${BLENDER_VERSION}/scripts/addons
ln -s ~/zumolabs/segmentium ~/.config/blender/${BLENDER_VERSION}/scripts/addons/segmentium
```

Now start Blender and navigate to "Edit -> Preferences -> Add-ons". Search and enable "segmentium". Save your config.

![Enabling the addon](./doc/addon_setup_location.png)

The add-on will show up in the "N" panel. You can enable the N panel by just pressing "n" on your keyboard.

![The N panel](./doc/addon_panel_location.png)