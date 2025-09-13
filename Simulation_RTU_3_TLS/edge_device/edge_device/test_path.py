import os
a=os.path.abspath(__file__)
name = os.path.basename(__file__)
base_path = a[0:len(a)-len(name)]
print(base_path)