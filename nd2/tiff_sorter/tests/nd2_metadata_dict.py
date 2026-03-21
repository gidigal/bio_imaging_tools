from nd2reader import ND2Reader
import json
nd2_reader = ND2Reader('D:\\Gidi\\weizmann\\alex\\samples\\10_23_25_clp_PBS_test.nd2')
print(str(nd2_reader.metadata))