import unittest
from src import utils as controller


# --- Unit Tests ---
class TestStochasticK(unittest.TestCase):
    def test_length_and_validity(self):
        data = [{"High": 10+i, "Low": 5+i, "Close": 7+i} for i in range(12)]
        period = 8
        result = controller.stochastic_k(data, period)
        self.assertEqual(len(result), len(data))
        self.assertEqual(result[:period-1], [None]*(period-1))
        self.assertIsInstance(result[period-1], float)

class TestSimpleMovingAverage(unittest.TestCase):
    def test_sma_computation(self):
        values = [1, 2, 3, 4, 5, 6]
        period = 3
        expected = [None, None, 2.0, 3.0, 4.0, 5.0]
        result = controller.simple_moving_average(values, period)
        self.assertEqual(result, expected)

class TestCrossSignals(unittest.TestCase):
    def test_crossover(self):
        self.assertTrue(controller.crossover(10, 15, 12, 13))
        self.assertFalse(controller.crossover(14, 13, 13, 13))

    def test_crossunder(self):
        self.assertTrue(controller.crossunder(15, 10, 12, 11))
        self.assertFalse(controller.crossunder(10, 12, 11, 11))

class TestPattern123(unittest.TestCase):
    def test_detect_123_buy(self):
        data = [
            {"High": 10, "Low": 9.0, "Close": 9.5},  # dummy - ignored
            {"High": 11, "Low": 9.1, "Close": 10},  # p1
            {"High": 12, "Low": 10.2, "Close": 11},  # p2
            {"High": 11.5, "Low": 9.5, "Close": 10},  # p3
            {"High": 13, "Low": 10.5, "Close": 12.01},  # p4
        ]
        for d in data:
            d["pattern123"] = None
        controller.signal_setup123(data)
        self.assertEqual(data[-1]["pattern123"], "123buy")

    def test_detect_123_sell(self):
        data = [
            {"High": 12, "Low": 11, "Close": 11.5},  # ignored
            {"High": 15, "Low": 14.0, "Close": 14.5},  # P1 (top)
            {"High": 14, "Low": 12.0, "Close": 13.0},  # P2 (lower low)
            {"High": 13.5, "Low": 12.8, "Close": 13.2},  # P3 (lower high)
            {"High": 12.5, "Low": 11.5, "Close": 11.9},  # P4 (breaks below P2's low)
        ]

        for d in data:
            d["pattern123"] = None
        controller.signal_setup123(data)
        self.assertEqual(data[-1]["pattern123"], "123sell")

if __name__ == "__main__":
    unittest.main()
