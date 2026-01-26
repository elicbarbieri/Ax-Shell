{ lib, pkgs }:

pkgs.buildGoModule rec {
  pname = "fabric-cli";
  version = "0.0.2";

  src = pkgs.fetchFromGitHub {
    owner = "Fabric-Development";
    repo = "fabric-cli";
    rev = "9f5ce4d"; # Latest commit from fabric-cli repo
    sha256 = "sha256-C4JO82RMuEh+S+MUUHuBaPuDhv48QKBlxRqYgrjyqPk=";
  };

  # Vendor hash for Go dependencies
  vendorHash = "sha256-5luc8FqDuoKckrmO2Kc4jTmDmgDjcr3D4v5Z+OpAOs4=";

  # The go.mod is in root, but source files are in src/
  # So we need to build the ./src subdirectory
  subPackages = [ "./src" ];

  ldflags = [ "-s" "-w" ];

  # Fix the binary name and install shell completions
  postInstall = ''
    mv $out/bin/src $out/bin/fabric-cli
    
    # Install shell completions
    mkdir -p $out/share/{bash-completion/completions,zsh/site-functions,fish/completions}
    cp $src/autocompletions/bash_autocomplete $out/share/bash-completion/completions/fabric-cli
    cp $src/autocompletions/zsh_autocomplete $out/share/zsh/site-functions/_fabric-cli  
    cp $src/autocompletions/fish_autocomplete $out/share/fish/completions/fabric-cli.fish
  '';

  meta = with pkgs.lib; {
    description = "An alternative super-charged CLI for Fabric";
    homepage = "https://github.com/Fabric-Development/fabric-cli";
    license = licenses.agpl3Plus;
    platforms = platforms.linux;
  };
}