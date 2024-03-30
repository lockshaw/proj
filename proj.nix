{ buildPythonApplication, ... }:

buildPythonApplication {
  pname = "proj";
  version = "0.0.1";
  src = ./.;
}
