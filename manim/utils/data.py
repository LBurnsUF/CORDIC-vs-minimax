DATA = {
    "cycles": [
        {"L": 1, "cordic": 410, "taylor": 282, "minimax": 202},
        {"L": 2, "cordic": 1488, "taylor": 1537, "minimax": 1215},
        {"L": 4, "cordic": 9419, "taylor": 5345, "minimax": 4218},
    ],
    "accuracy": [
        {"fb": 6, "cordic": 4, "taylor": 1, "minimax": 1},
        {"fb": 14, "cordic": 4, "taylor": 1, "minimax": 1},
        {"fb": 30, "cordic": 5, "taylor": 1, "minimax": 1},
    ],
    "opcount": [
        {"fb": 6, "cordic_iter": 6, "taylor_terms": 3, "minimax_terms": 2},
        {"fb": 14, "cordic_iter": 14, "taylor_terms": 4, "minimax_terms": 3},
        {"fb": 30, "cordic_iter": 30, "taylor_terms": 6, "minimax_terms": 5},
    ],
}
