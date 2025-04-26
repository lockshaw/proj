#include "not-kernels/not-kernels.h"
#include <iostream>

namespace GPUTestProject {

void call_not_kernels_cpu() {
  std::cout << "not-kernels-cpu" << std::endl; 
}

void call_not_kernels_gpu() {
  std::cout << "not-kernels-gpu" << std::endl; 
}

}
