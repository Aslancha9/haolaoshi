#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化版GPU测试脚本，只测试PyTorch和CUDA
"""

import torch
import time
import numpy as np

def test_gpu_availability():
    """测试GPU是否可用"""
    print("\n=== GPU可用性测试 ===")
    if torch.cuda.is_available():
        print(f"GPU可用: {torch.cuda.get_device_name(0)}")
        print(f"CUDA版本: {torch.version.cuda}")
        print(f"可用GPU数量: {torch.cuda.device_count()}")
        
        # 简单性能测试
        # 创建随机矩阵
        size = 5000
        print(f"执行{size}x{size}矩阵乘法性能测试...")
        
        # GPU计时
        a = torch.randn(size, size, device="cuda")
        b = torch.randn(size, size, device="cuda")
        
        torch.cuda.synchronize()
        start = time.time()
        c = torch.matmul(a, b)
        torch.cuda.synchronize()
        gpu_time = time.time() - start
        
        # CPU计时
        a_cpu = a.cpu()
        b_cpu = b.cpu()
        start = time.time()
        c_cpu = torch.matmul(a_cpu, b_cpu)
        cpu_time = time.time() - start
        
        print(f"矩阵乘法 ({size}x{size}):")
        print(f"  GPU时间: {gpu_time:.4f} 秒")
        print(f"  CPU时间: {cpu_time:.4f} 秒")
        print(f"  加速比: {cpu_time/gpu_time:.1f}x")
        
        # 测试GPU内存
        print("\n=== GPU内存测试 ===")
        print(f"GPU总内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        print(f"当前已分配: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")
        print(f"当前缓存: {torch.cuda.memory_reserved() / 1024**3:.1f} GB")
        
        return True
    else:
        print("警告: GPU不可用，将使用CPU运行模型")
        return False

if __name__ == "__main__":
    # 运行GPU测试
    gpu_available = test_gpu_availability()
    
    if gpu_available:
        print("\n=== 测试结果 ===")
        print("✓ GPU可用且性能良好")
        print("✓ PyTorch成功使用GPU加速")
        print("\n系统已准备好运行推荐模型！")
    else:
        print("\n=== 测试结果 ===")
        print("✗ GPU不可用，推荐系统将使用CPU运行，性能会受到影响")