#include "lib1/lib1.h"
#include "lib1/example_enum.h"
#include <iostream>

namespace TestProject {

void call_lib1() {
#ifdef LIB1_FAIL_BUILD
  some_function_that_does_not_exist();
#endif
  std::cout << "lib1" << std::endl; 
}

}
