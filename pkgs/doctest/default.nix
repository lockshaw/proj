{ pkgs
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
  ];
})
