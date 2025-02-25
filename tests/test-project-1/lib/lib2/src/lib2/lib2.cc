#include "lib2/lib2.h"
#include "lib1/lib1.h"
#include <iostream>

namespace TestProject {

void call_lib2() {
  call_lib1();

  std::cout << "lib2" << std::endl; 
}

}
