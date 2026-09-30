{ pkgs
, proj
}:

pkgs.vimUtils.buildVimPlugin {
  name = "proj-nvim";
  src = ../vim;
  buildInputs = [ proj ];

  dontWrapQtApps = true;

  postPatch = ''
    substituteInPlace UltiSnips/cpp.snippets --replace "%PROJPATH%" "${proj}/${pkgs.python3.sitePackages}"
  '';
}
