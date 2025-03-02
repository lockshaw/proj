{ buildPythonApplication
, pytestCheckHook
, typing-extensions
, enlighten
, immutables
, setuptools
, pytest-skip-slow
, pytest
, callPackage
}:

buildPythonApplication {
  pname = "proj";
  version = "0.0.1";
  src = ../../.;

  dontUseCmakeConfigure = true;

  propagatedBuildInputs = [
    typing-extensions
    enlighten
    immutables
  ];

  build-system = [
    setuptools
  ];

  checkPhase = ''
    runHook preCheck

    CCACHE_DIR="$(mktemp -d)" pytest -s -vvvv tests/ -m 'not no_sandbox' --log-level=DEBUG

    runHook postCheck
  '';

  nativeCheckInputs = [
    pytestCheckHook
    pytest
    pytest-skip-slow
  ];

  passthru.tests = {
    e2e = callPackage ./tests-e2e.nix { };
  };
}
