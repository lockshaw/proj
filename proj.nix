{ buildPythonApplication
, python3Packages
, bencher-cli
}:

buildPythonApplication {
  pname = "proj";
  version = "0.0.1";
  src = ./.;

  propagatedBuildInputs = [
    python3Packages.typing-extensions
    python3Packages.enlighten
    bencher-cli
  ];
}
