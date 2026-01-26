{ pkgs }:

pkgs.python3Packages.buildPythonPackage rec {
  pname = "fabric";
  version = "2025-12-05";
  pyproject = true;  # Required for Python 3.13+

  src = pkgs.fetchFromGitHub {
    owner = "Fabric-Development";
    repo = "fabric";
    rev = "8633df172a3ceee9222e7e583e93717f733d5618";
    sha256 = "sha256-c56/WC4B4UDiKJ1R6Rz+io9Jt1Mq/WmIqjP1KYJvDf0=";
  };

  # Patch pyproject.toml to accept PyGObject 3.52.3 instead of strict 3.50.0 pin
  postPatch = ''
    substituteInPlace pyproject.toml \
      --replace-fail 'PyGObject==3.50.0' 'PyGObject>=3.50.0'
    substituteInPlace requirements.txt \
      --replace-fail 'PyGObject==3.50.0' 'PyGObject>=3.50.0'
  '';

  build-system = with pkgs.python3Packages; [
    setuptools
    wheel
  ];

  dependencies = with pkgs.python3Packages; [
    click
    loguru
    pycairo
    pygobject3
    psutil
  ];

  nativeBuildInputs = with pkgs; [
    pkg-config
    gobject-introspection
    wrapGAppsHook3
  ];

  buildInputs = with pkgs; [
    glib
    gtk3
    cairo
    gdk-pixbuf
    gtk-layer-shell
    libdbusmenu-gtk3
    gnome-bluetooth
    cinnamon-desktop
    networkmanager  # For NM GI typelibs
    gobject-introspection
  ];

  pythonImportsCheck = [ "fabric" ];

  meta = with pkgs.lib; {
    description = "Next-Gen python framework for creating system widgets on *Nix systems!";
    homepage = "https://github.com/Fabric-Development/fabric";
    license = licenses.agpl3Plus;
    platforms = platforms.linux;
  };
}
