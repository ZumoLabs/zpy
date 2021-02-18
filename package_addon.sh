# This script will package the current repository into a .zip
#   which can be used to install the zpy_addon through Blender

# Remove any existing zips
rm *.zip

# Copy the zpy library into the addon folder
cp -r zpy/ zpy_addon/

# Copy the zpy requirements into the zpy folder
cp -r requirements.txt zpy_addon/
cp -r setup.py zpy_addon/

# Zip up zpy_addon into a versioned zip file
# excluding any images and git artifacts
zip -r zpy_addon-${ZPY_VERSION}.zip zpy_addon/ \
    --exclude "*.png" ".git/*"

# Remove the copied contents
rm -rf zpy_addon/zpy
rm -rf zpy_addon/requirements.txt
rm -rf zpy_addon/setup.py
