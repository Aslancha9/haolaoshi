#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试GPU可用性和性能
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
        
        return True
    else:
        print("警告: GPU不可用，将使用CPU运行模型")
        return False

def test_bert_import():
    """测试BERT模型导入"""
    print("\n=== BERT模型导入测试 ===")
    try:
        from transformers import BertModel, BertTokenizer
        print("成功导入transformers库")
        
        # 尝试加载模型
        print("尝试加载BERT模型...")
        tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
        model = BertModel.from_pretrained('bert-base-chinese')
        
        # 测试GPU加速
        if torch.cuda.is_available():
            print("将模型移至GPU...")
            model = model.to('cuda')
            
            # 简单推理测试
            print("执行简单推理测试...")
            text = "这是一个测试句子"
            inputs = tokenizer(text, return_tensors="pt").to('cuda')
            
            start = time.time()
            with torch.no_grad():
                outputs = model(**inputs)
            torch.cuda.synchronize()
            inference_time = time.time() - start
            
            print(f"推理完成，用时: {inference_time:.4f} 秒")
            print(f"输出张量形状: {outputs.last_hidden_state.shape}")
            
        return True
    except Exception as e:
        print(f"BERT模型导入失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 运行GPU测试
    gpu_available = test_gpu_availability()
    
    if gpu_available:
        # 测试BERT导入
        bert_success = test_bert_import()
        
        if bert_success:
            print("\n=== 测试结果 ===")
            print("✓ GPU可用且性能良好")
            print("✓ BERT模型可以成功加载并使用GPU加速")
            print("\n系统已准备好运行推荐模型！")
        else:
            print("\n=== 测试结果 ===")
            print("✓ GPU可用且性能良好")
            print("✗ BERT模型加载失败，请检查transformers库安装")
    else:
        print("\n=== 测试结果 ===")
        print("✗ GPU不可用，推荐系统将使用CPU运行，性能会受到影响")