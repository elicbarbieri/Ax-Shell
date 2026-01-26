{ lib, stdenv, fetchFromGitHub }:

stdenv.mkDerivation rec {
  pname = "tabler-icons-font";
  version = "v0.0.62";

  src = fetchFromGitHub {
    owner = "Axenide";
    repo = "Ax-Shell";
    rev = "e8604047408a818785b32c4a5d1c1e1c8b09b7e3";
    sha256 = "sha256-iVUpIUSli234kwZsw9pOXu9hiR+7ws4x6AdlZyjTRbI=";
  };


  installPhase = ''
    runHook preInstall
    mkdir -p $out/share/fonts/truetype/tabler-icons
    cp assets/fonts/tabler-icons/tabler-icons.ttf $out/share/fonts/truetype/tabler-icons/
    runHook postInstall
  '';

  meta = with lib; {
    description = "Tabler Icons font for ax-shell icon display";
    homepage = "https://github.com/Axenide/Ax-Shell";
    license = licenses.mit;
    platforms = platforms.all;
  };
}
