Tests of using ARL for LOW imaging

simulation1: ngroup = 8, use_serial_invert True
    Only uses 20 workers but creates 33
    Works but CPU usage and memory low

simulation2: ngroup = 8, use_serial_invert False
    Only uses 20 workers but creates 33
    Not balanced but works

simulation3: ngroup=4, use_serial_invert True
    Only uses 40 workers but creates 65
    Not balanced but works

simulation4: Same as sim3 but start client earlier
    Killed

simulation5: ngroup=1, 161 workers, use_serial_invert=True
    Memory error

simulation6: same as 5 but use_serial_invert=False
    Memory error
    
simulation7: ngroup=8, 65 tasks, 4 tasks/node use_serial_invert True
    Works but some nodes seem to have only one task
    
122295 tim       20   0   40.2g  30.9g  11872 S 102.7 24.6  31:32.73 python3.6
122297 tim       20   0   36.2g  30.8g  11872 S 102.3 24.5  31:40.53 python3.6

simulation8: ngroup=5, 161 tasks, 10 tasks/node use_serial_invert True
    Memory error
    
simulation9: ngroup=5, 161 tasks, 10 tasks/node use_serial_invert False
    Memory error
    
simulation10: ngroup=1, 161 tasks, 10 tasks/node use_serial_invert False
    Memory error

simulation11: ngroup=1, 161 tasks, 10 tasks/node use_serial_invert False
    processing time = 13762.14

simulation12: ngroup=1, 161 tasks, 10 tasks/node use_serial_invert True
    Size of one vis = 0.327 GB
    Full MS = 7.8 GB
    Memory errors!
    
simulation13: ngroup=5, 129 tasks, 8 tasks/node use_serial_invert True
    Memory error
    
Best so far is simulation 7

simulation 14: ngroup=5, 65 tasks, 4 tasks/node use_serial_invert False
    Memory error