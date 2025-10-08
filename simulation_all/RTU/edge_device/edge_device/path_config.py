import os

class pathConfig():
    base_path = ""

    def __init__(self) -> None:
        a=os.path.abspath(__file__)
        name = os.path.basename(__file__)
        self.base_path = a[0:len(a)-len(name)]

path_cfg : pathConfig 

