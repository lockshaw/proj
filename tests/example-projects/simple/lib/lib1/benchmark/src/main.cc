#include <vector>
#include <string>
#include <iostream>
#include "benchmark/lib1/lib1.h"
#include <cstdlib>

using namespace ::TestProject;

void require_cond(bool c) {
  if (!c) {
    std::exit(1);
  }
}

int main(int argc, char **argv) {
  std::vector<std::string> args(argv, argv + argc);
  std::string arg = args.at(1);

  if (arg == "--list") {
    require_cond(args.size() == 2);
    std::cout << "example_benchmark" << std::endl;
    return 0;
  }

  require_cond(arg == "--benchmark");
  require_cond(args.size() == 3);
  require_cond(args.at(2) == "example_benchmark");
  example_benchmark();
}
