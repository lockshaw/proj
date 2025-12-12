{ pkgs
, fetchpatch
}:

pkgs.doctest.overrideAttrs ( old: rec {
  version = "2.4.9";
  src = pkgs.fetchFromGitHub {
    owner = "doctest";
    repo = "doctest";
    rev = "v${version}";
    sha256 = "sha256-ugmkeX2PN4xzxAZpWgswl4zd2u125Q/ADSKzqTfnd94=";
  };
  patches = [
    ./doctest-template-test.patch

    # Fix the build with Clang.
    (fetchpatch {
      name = "doctest-disable-warnings.patch";
      url = "https://github.com/doctest/doctest/commit/c8d9ed2398d45aa5425d913bd930f580560df30d.patch";
      excludes = [ ".github/workflows/main.yml" ];
      hash = "sha256-kOBy0om6MPM2vLXZjNLXiezZqVgNr/viBI7mXrOZts8=";
    })
  ];
})
