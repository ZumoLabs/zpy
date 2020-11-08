#!/bin/bash
set -e

BLENDER_VERSION=${BLENDER_VERSION:-"2.90"}
BLENDER_VERSION_FULL=${BLENDER_VERSION_FULL:-"2.90.1"}
ZPY_VERSION=${ZPY_VERSION:-"1.2.2"}

# First check if the OS is Linux.
if [[ "$(uname)" = "Linux" ]]; then
  ON_LINUX=true
  ON_MAC=false
else
  ON_MAC=true
  ON_LINUX=false
fi

# string formatters
if [[ -t 1 ]]; then
  tty_escape() { printf "\033[%sm" "$1"; }
else
  tty_escape() { :; }
fi
tty_mkbold() { tty_escape "1;$1"; }
tty_underline="$(tty_escape "4;39")"
tty_blue="$(tty_mkbold 34)"
tty_red="$(tty_mkbold 31)"
tty_bold="$(tty_mkbold 39)"
tty_reset="$(tty_escape 0)"

mac_dmg_install() {
  VOLUME=`hdiutil attach "$1" | grep Volumes | awk '{print $3}'`
  cp -rf $VOLUME/*.app /Applications
  hdiutil detach "$VOLUME"
}

execute() {
  if ! "$@"; then
    abort "$(printf "Failed during: %s" "$(shell_join "$@")")"
  fi
}

shell_join() {
  local arg
  printf "%s" "$1"
  shift
  for arg in "$@"; do
    printf " "
    printf "%s" "${arg// /\ }"
  done
}

have_sudo_access() {
  local -a args
  if [[ -n "${SUDO_ASKPASS-}" ]]; then
    args=("-A")
  fi

  if [[ -z "${HAVE_SUDO_ACCESS-}" ]]; then
    if [[ -n "${args[*]-}" ]]; then
      /usr/bin/sudo "${args[@]}" -l mkdir &>/dev/null
    else
      /usr/bin/sudo -l mkdir &>/dev/null
    fi
    HAVE_SUDO_ACCESS="$?"
  fi

  if [[ -z "${HOMEBREW_ON_LINUX-}" ]] && [[ "$HAVE_SUDO_ACCESS" -ne 0 ]]; then
    abort "Need sudo access on macOS (e.g. the user $USER to be an Administrator)!"
  fi

  return "$HAVE_SUDO_ACCESS"
}

execute_sudo() {
  local -a args=("$@")
  if [[ -n "${SUDO_ASKPASS-}" ]]; then
    args=("-A" "${args[@]}")
  fi
  if have_sudo_access; then
    bprint "/usr/bin/sudo" "${args[@]}"
    execute "/usr/bin/sudo" "${args[@]}"
  else
    bprint "${args[@]}"
    execute "${args[@]}"
  fi
}

bprint() {
  printf "${tty_blue}==>${tty_bold} %s${tty_reset}\n" "$(shell_join "$@")"
}

cd "${HOME}" || exit 1

###################################################################### script

if $ON_MAC ; then 
  if ! command -v curl >/dev/null; then
    echo "Must install cURL"
    exit 1
  fi
  if ! command -v unzip >/dev/null; then
    echo "Must install zip"
  fi
elif $ON_LINUX ; then
  if ! command -v wget >/dev/null; then
    echo "Must install wget"
    exit 1
  fi
fi

bprint "This script will perform the following:"
echo "Install/Update Blender -- version ${BLENDER_VERSION}"
echo "Install/Update zpy -- version ${ZPY_VERSION}"

# Install Blender
bprint "Downloading and installing Blender..."
read -p "Install Blender? (y/n) " RESP
if [ "$RESP" = "y" ]; then
  if $ON_LINUX ; then
    wget https://download.blender.org/release/Blender${BLENDER_VERSION}/blender-${BLENDER_VERSION_FULL}-linux64.tar.xz
    tar -xvf blender-${BLENDER_VERSION_FULL}-linux64.tar.xz --strip-components=1 -C /bin
    rm -rf blender-${BLENDER_VERSION_FULL}-linux64.tar.xz
    rm -rf blender-${BLENDER_VERSION_FULL}-linux64
    echo "Blender installed succesfully"
  elif $ON_MAC ; then
    curl -O https://download.blender.org/release/Blender${BLENDER_VERSION}/blender-${BLENDER_VERSION_FULL}-macOS.dmg
    mac_dmg_install blender-${BLENDER_VERSION_FULL}-macOS.dmg
    rm -rf blender-${BLENDER_VERSION_FULL}-macOS.dmg
    echo "Blender installed succesfully"
  else 
    echo "Windows currently not supported"
  fi
else
  echo "Skipping Blender install"
fi

bprint "Verifying Credentials..."
if [ -z "${ARTIFACTORY_USER}" ]; then
  echo "Please define ARTIFACTORY_USER for https://zumolabs.jfrog.io/"
  exit 1
fi

if [ -z "${ARTIFACTORY_KEY}" ]; then
  echo "Please define ARTIFACTORY_KEY for https://zumolabs.jfrog.io/"
  exit 1
fi

# Install zpy pip
bprint "Downloading and installing zpy python package..."
read -p "Download and install zpy python package? (y/n) " RESP
if [ "$RESP" = "y" ]; then
  if $ON_LINUX ; then
    export BLENDER_PATH="/bin/$BLENDER_VERSION"
    export BLENDER_LIB_PY="${BLENDER_PATH}/python/lib/python3.7"
    export BLENDER_BIN_PY="${BLENDER_PATH}/python/bin/python3.7m"
    export BLENDER_BIN_PIP="${BLENDER_PATH}/python/bin/pip3"
    ${BLENDER_BIN_PY} -m ensurepip && ${BLENDER_BIN_PIP} install --upgrade pip
    ${BLENDER_BIN_PIP} install --pre --upgrade --extra-index-url=https://${ARTIFACTORY_USER}:${ARTIFACTORY_KEY}@zumolabs.jfrog.io/artifactory/api/pypi/zpy/simple zpy-zumo==${ZPY_VERSION}
    echo "zpy pip installed succesfully"
  elif $ON_MAC ; then
    export BLENDER_PATH="/Applications/Blender.app/Contents/Resources/${BLENDER_VERSION}"
    export BLENDER_LIB_PY="${BLENDER_PATH}/python/lib/python3.7"
    export BLENDER_BIN_PY="${BLENDER_PATH}/python/bin/python3.7m"
    export BLENDER_BIN_PIP="${BLENDER_PATH}/python/bin/pip3"
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    ${BLENDER_BIN_PY} get-pip.py && ${BLENDER_BIN_PIP} install --upgrade pip
    ${BLENDER_BIN_PIP} install --pre --upgrade --extra-index-url=https://${ARTIFACTORY_USER}:${ARTIFACTORY_KEY}@zumolabs.jfrog.io/artifactory/api/pypi/zpy/simple zpy-zumo==${ZPY_VERSION}
    rm -rf get-pip.py
    echo "zpy pip installed succesfully"
  else 
    echo "Windows currently not supported"
  fi
else
  echo "Skipping zpy pip install"
fi

# Install zpy addon
bprint "Downloading and installing zpy addon..."
read -p "Download and install zpy addon? (y/n) " RESP
if [ "$RESP" = "y" ]; then
  if $ON_LINUX ; then
    curl -H "X-JFrog-Art-Api:${ARTIFACTORY_KEY}" -O "https://zumolabs.jfrog.io/artifactory/addons/zpy_addon-v${ZPY_VERSION}.zip"
    export BLENDERADDONS="/bin/${BLENDER_VERSION}/scripts/addons"
    unzip zpy_addon-v${ZPY_VERSION}.zip -d ${BLENDERADDONS}/
    rm zpy_addon-v${ZPY_VERSION}.zip
    echo "zpy addon installed succesfully"
  elif $ON_MAC ; then
    curl -H "X-JFrog-Art-Api:${ARTIFACTORY_KEY}" -O "https://zumolabs.jfrog.io/artifactory/addons/zpy_addon-v${ZPY_VERSION}.zip"
    export BLENDERADDONS="/Applications/Blender.app/Contents/Resources/${BLENDER_VERSION}/scripts/addons"
    unzip zpy_addon-v${ZPY_VERSION}.zip -d ${BLENDERADDONS}/
    rm zpy_addon-v${ZPY_VERSION}.zip
    echo "zpy addon installed succesfully"
  else 
    echo "Windows currently not supported"
  fi
else
  echo "Skipping zpy addon install"
fi
