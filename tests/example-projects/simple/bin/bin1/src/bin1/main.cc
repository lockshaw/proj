#include "lib1/lib1.h"
#include "bin1/in_my_binary.dtg.h"

using namespace ::TestProject;

int main() {
#ifdef BIN1_FAIL_BUILD
  some_function_that_does_not_exist();
#endif
  call_lib1();
}
