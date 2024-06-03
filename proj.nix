{ buildPythonApplication, python3Packages, ... }:

buildPythonApplication {
  pname = "proj";
  version = "0.0.1";
  src = ./.;

  buildInputs = [
    python3Packages.typing-extensions
  ];
}
