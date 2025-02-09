{ buildPythonApplication
, python3Packages
, bencher-cli
, pkgs
, hotspot
}:

buildPythonApplication {
  pname = "proj";
  version = "0.0.1";
  src = ./.;

  propagatedBuildInputs = [
    python3Packages.typing-extensions
    python3Packages.enlighten
    bencher-cli
    pkgs.linuxPackages_latest.perf
  ];
}
