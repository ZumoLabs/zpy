# This script will package the current repository into a .zip
#   which can be used to install the zpy_addon through Blender

# Remove any existing zips
rm *.zip

# Zip up zpy_addon into a versioned zip file
# excluding any images and git artifacts
zip -r zpy_addon-${ZPY_VERSION}.zip zpy_addon/ \
    --exclude "*.png" ".git/*"