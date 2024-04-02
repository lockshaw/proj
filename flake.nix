{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-23.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }: flake-utils.lib.eachDefaultSystem (system: 
    let 
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };

    in 
    {
      packages = rec {
        proj = pkgs.python3Packages.callPackage ./proj.nix { };
        proj-nvim = pkgs.vimUtils.buildVimPlugin {
          name = "proj-nvim";
          src = ./vim;
          buildInputs = [ self.packages.${system}.proj ];

          postPatch = ''
            substituteInPlace UltiSnips/cpp.snippets --replace "%PROJPATH%" "${proj}/${pkgs.python3.sitePackages}"
          '';
        };

        default = proj;
      };

      apps.default = {
        type = "app";
        program = "${self.packages.${system}.proj}/bin/proj";
      };
    }
  );
}
# vim: set tabstop=2 shiftwidth=2 expandtab:
