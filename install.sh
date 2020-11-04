#!/bin/bash
set -ue

BLENDER_VERSION="2.90"
BLENDER_VERSION_FULL="2.90.1"
ZPY_VERSION="1.1.14"

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
    echo "Blender installed succesfully."
  elif $ON_MAC ; then
    curl -O https://download.blender.org/release/Blender${BLENDER_VERSION}/blender-${BLENDER_VERSION_FULL}-macOS.dmg
    mac_dmg_install blender-${BLENDER_VERSION_FULL}-macOS.dmg
    echo "Blender installed succesfully."
  else 
    echo "Windows currently not supported"
  fi
else
  echo "Skipping Blender install."
fi

# Install zpy pip
bprint "Downloading and installing zpy python package..."
read -p "Should I download and install zpy python package? (y/n) " RESP
if [ "$RESP" = "y" ]; then
  echo "YES zpy package"
else
  echo "NOPE zpy package"
fi

# Install zpy addon
bprint "Downloading and installing zpy addon..."
read -p "Should I download and install zpy addon? (y/n) " RESP
if [ "$RESP" = "y" ]; then
  echo "YES zpy addon"
else
  echo "NOPE zpy addon"
fi
