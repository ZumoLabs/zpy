# Remove any existing zips
rm *.zip
# Zip up segmentium into a versioned zip file
#   excluding any images and git artifacts
zip -r segmentium-${SEGMENTIUM_VERSION}.zip . \
    --exclude "*.png" ".git/*"