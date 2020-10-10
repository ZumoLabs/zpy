# Remove any existing zips
rm *.zip
# Zip up zpy_addon into a versioned zip file
# excluding any images and git artifacts
zip -r zpy_addon-${ZPY_VERSION}.zip . \
    --exclude "*.png" ".git/*"