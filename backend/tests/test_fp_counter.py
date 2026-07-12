import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.core.fp_counter import FpCounter, DevAdjustmentEngine

def test_fp_counter_estimated():
    c = FpCounter("estimated")
    assert c.weights["ILF"] == 35
    assert c.weights["EIF"] == 15
    assert c.weights["EI"] == 4
    assert c.weights["EO"] == 5
    assert c.weights["EQ"] == 4

def test_fp_counter_detailed():
    c = FpCounter("detailed")
    assert c.weights["ILF"] == 10
    assert c.weights["EIF"] == 7

def test_compute_us():
    c = FpCounter()
    # UFP=10, reuse=low(1.0), modify=new(1.0) => 10*1*1=10
    assert c.compute_us(10, "low", "new") == 10.0
    # UFP=10, reuse=high(0.3333), modify=modify(0.8) => 10*0.3333*0.8≈2.6667
    assert c.compute_us(10, "high", "modify") == 2.6667

def test_compute_raw_fp():
    c = FpCounter()
    items = [{"ufp": 10}, {"ufp": 7}, {"ufp": 4}]
    assert c.compute_raw_fp(items) == 21

def test_compute_total_us():
    c = FpCounter()
    items = [
        {"ufp": 10, "reuse_level": "low", "modify_type": "new"},
        {"ufp": 7, "reuse_level": "high", "modify_type": "modify"},
    ]
    total = c.compute_total_us(items)
    expected = 10 * 1.0 * 1.0 + 7 * 0.3333 * 0.8
    assert abs(total - expected) < 0.01

def test_scale_change():
    c = FpCounter()
    assert c.apply_scale_change(100, "early_stage") == 139
    assert c.apply_scale_change(100, "post_delivery") == 100

def test_dev_adj_engine():
    e = DevAdjustmentEngine()
    assert e.get_application_type_factor("业务处理") == 1.0
    assert e.get_application_type_factor("智能信息") == 1.5
    assert e.get_non_functional_factor([0, 0, 0, 0]) == 1.0
    assert e.get_non_functional_factor([1, 1, 1, 1]) == 1.1
    assert e.get_integrity_factor("C/D级别或无明确完整性级别") == 1.0
    assert e.get_language_factor("JAVA、C++、C#及其他同级别语言/平台") == 1.0
    assert e.get_team_factor("为本行业开发过类似的项目") == 0.8

def test_total_factor():
    e = DevAdjustmentEngine()
    f = e.compute_total_factor("业务处理", [0, 0, 0, 0], "C/D级别或无明确完整性级别",
                                "JAVA、C++、C#及其他同级别语言/平台", "为本行业开发过类似的项目")
    assert abs(f - 0.8) < 0.01  # 1.0 * 1.0 * 1.0 * 1.0 * 0.8

if __name__ == "__main__":
    test_fp_counter_estimated()
    test_fp_counter_detailed()
    test_compute_us()
    test_compute_raw_fp()
    test_compute_total_us()
    test_scale_change()
    test_dev_adj_engine()
    test_total_factor()
    print("All FP counter tests passed!")
