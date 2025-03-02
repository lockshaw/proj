{ buildPythonPackage
, flit-core
, flit
, fetchPypi
}:

buildPythonPackage rec {
  pname = "pytest-skip-slow";
  version = "0.0.5";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    sha256 = "sha256-ZV6lx0jHKUfg0wIzTn+o75mSkleiorySj2MN21oWHYg=";
  };

  nativeBuildInputs = [
    flit-core
  ];

  build-system = [
    flit 
  ];
}
