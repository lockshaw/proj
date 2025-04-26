#include "kernels/kernels.h"
#include <iostream>

namespace GPUTestProject {

void call_kernels_cpu() {
  std::cout << "kernels-cpu" << std::endl; 
}

void call_kernels_gpu() {
  std::cout << "kernels-gpu" << std::endl; 
}

}
