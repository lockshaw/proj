{ buildPythonApplication
, pytestCheckHook
, typing-extensions
, enlighten
, setuptools
, pytest-skip-slow
, pytest
, nclib
, valgrind
, kdePackages
, ff-clang-format
, hotspot
, perf
, ccache
, compdb
, cmake
, ninja
, mypy
, doctest
, gbenchmark
, libassert
, rapidcheckFull
, nlohmann_json
, fmt_10
, tree
, doxygen
, lcov
, gdb
, pytest-xdist
, universal-ctags
# TODO use these if we ever update nixpkgs
# , writableTmpDirAsHomeHook
# , addBinAsPathHook
, ...
}:

let
  bins = [
    valgrind
    kdePackages.kcachegrind
    ff-clang-format
    hotspot
    perf
    ccache
    compdb
    cmake
    ninja
    lcov
    doxygen
    universal-ctags
  ];
in
buildPythonApplication {
  pname = "proj";
  version = "0.0.1";
  src = ../../.;

  dontUseCmakeConfigure = true;

  propagatedBuildInputs = [
    typing-extensions
    enlighten
  ] ++ bins;

  pyproject = true;
  build-system = [
    setuptools
  ];

  checkPhase = ''
    runHook preCheck

    export HOME="$(mktemp -d)"
    export PATH="$out/bin:$PATH"
    mypy proj/ tests/
    TMP=/dev/shm pytest -n $NIX_BUILD_CORES --dist loadgroup -x -s -vvvv tests/ -m 'not no_sandbox' --log-level=DEBUG --slow

    runHook postCheck
  '';

  checkInputs = [
    doctest
    gbenchmark
    rapidcheckFull
    libassert
    nlohmann_json
    fmt_10
  ];

  nativeCheckInputs = [
    pytest
    pytest-skip-slow
    pytest-xdist
    mypy
    nclib
    gdb
  ] ++ bins;

  dontWrapQtApps = true;
}
