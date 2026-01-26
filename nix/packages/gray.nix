{ lib, pkgs }:

pkgs.stdenv.mkDerivation rec {
  pname = "gray";
  version = "0.0.1-unstable-2025-08-31";

  src = pkgs.fetchFromGitHub {
    owner = "Fabric-Development";
    repo = "gray";
    rev = "d5a8452c39b074ef6da25be95305a22203cf230e";
    sha256 = "sha256-s9v9fkp+XrKqY81Z7ezxMikwcL4HHS3KvEwrrudJutw=";
  };

  nativeBuildInputs = with pkgs; [
    meson
    ninja
    pkg-config
    vala
    gobject-introspection
  ];

  # Fix source directory for Meson
  sourceRoot = "source";
  
  buildInputs = with pkgs; [
    glib
    gobject-introspection
    gtk3
    libdbusmenu-gtk3
  ];

  meta = with pkgs.lib; {
    description = "libgray; a status notifier GObject library which can be used to create system trays";
    homepage = "https://github.com/Fabric-Development/gray";
    license = licenses.agpl3Plus;
    platforms = platforms.linux;
  };
}