{ lib, pkgs }:

pkgs.stdenv.mkDerivation rec {
  pname = "zed-fonts";
  version = "1.2.0";

  src = pkgs.fetchurl {
    url = "https://github.com/zed-industries/zed-fonts/releases/download/${version}/zed-sans-${version}.zip";
    sha256 = "sha256-64YcNcbxY5pnR5P3ETWxNw/+/JvW5ppf9f/6JlnxUME="; 
  };

  nativeBuildInputs = with pkgs; [ unzip ];

  unpackPhase = ''
    runHook preUnpack
    unzip $src
    runHook postUnpack
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p $out/share/fonts/truetype/zed-sans
    cp -r *.ttf $out/share/fonts/truetype/zed-sans/
    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "Zed Sans fonts";
    homepage = "https://github.com/zed-industries/zed-fonts";
    license = licenses.ofl;
    platforms = platforms.all;
  };
}