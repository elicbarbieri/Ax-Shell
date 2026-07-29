{ pkgs }:

pkgs.python3Packages.buildPythonPackage rec {
  pname = "fabric";
  # Upstream declares version "0.0.2" in pyproject.toml; the date suffix follows
  # the nixpkgs unstable-snapshot convention to track the pinned git rev below.
  version = "0.0.2-unstable-2026-07-24";
  pyproject = true;  # Required for Python 3.13+

  # The pinned snapshot's metadata version ("0.0.2") intentionally differs from
  # the nix `version` above, so skip the metadata/version equality check.
  dontCheckPythonMetadata = true;

  src = pkgs.fetchFromGitHub {
    owner = "Fabric-Development";
    repo = "fabric";
    rev = "85cacf660b1a324525a4dd9b512521e55ef7f89b";
    sha256 = "sha256-QV0t7y3ant10weKwlNoy3RMmOQ2rOr3/C0bgNkutoi8=";
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
