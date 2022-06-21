from lora_ctp.ctp_node import LoRA_CTP_Node
from adapters.Wifi_adapter import WiFi_adapter

class Gateway_Node(LoRA_CTP_Node):

    def __init__(self, mesh_mode = False, debug_hops = False, adapter = None):
        LoRA_CTP_Node.__init__(self, mesh_mode = False, debug_hops = False, adapter = adapter)
    
    def set_nodes_to_hear(self, list_of_nodes):
        pass


adapter = WiFi_adapter(1,2,3,4,5,6)
node = Gateway_Node(adapter = adapter)
print(node.get_mesh_mode())